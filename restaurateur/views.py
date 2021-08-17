from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from geopy import distance
from operator import itemgetter

from foodcartapp.models import Product, Restaurant, Order, RestaurantMenuItem
from geocoder.models import Location

from django.db.models import F


class Login(forms.Form):
    username = forms.CharField(
        label='Логин', max_length=75, required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Укажите имя пользователя'
        })
    )
    password = forms.CharField(
        label='Пароль', max_length=75, required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Введите пароль'
        })
    )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, 'login.html', context={
            'form': form
        })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect('restaurateur:RestaurantView')
                return redirect('start_page')

        return render(request, 'login.html', context={
            'form': form,
            'ivalid': True,
        })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    default_availability = {restaurant.id: False for restaurant in restaurants}
    products_with_restaurants = []
    for product in products:

        availability = {
            **default_availability,
            **{item.restaurant_id: item.availability for item in product.menu_items.all()},
        }
        orderer_availability = [availability[restaurant.id] for restaurant in restaurants]

        products_with_restaurants.append(
            (product, orderer_availability)
        )

    return render(request, template_name='products_list.html', context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name='restaurants_list.html', context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = (
        Order.objects
        .get_total_cost()
        .annotate(products=F('positions__product'))
    )

    locations = get_locations(orders)

    orders_with_products = {}
    order_query = [(order, order.products) for order in orders]
    for order, products in order_query:
        orders_with_products.setdefault(order, []).append(products)

    return render(request, template_name='order_items.html', context={
        'order_items': [
            serialize_order(order_with_products, locations)
            for order_with_products in orders_with_products.items()
        ],
    })


def serialize_order(order_with_products, locations):
    order, products = order_with_products

    serialized_order = {
        'id': order.id,
        'status': order.get_status_display(),
        'payment_method': order.get_payment_method_display(),
        'cost': order.cost,
        'firstname': order.firstname,
        'lastname': order.lastname,
        'phonenumber': order.phonenumber,
        'address': order.address,
        'note': order.note,
    }

    order_location = locations.get(order.address)

    restaurants = serialize_restaurants(products, locations, order_location)
    serialized_order['restaurants'] = sorted(
        restaurants, key=itemgetter('distance'),
    )

    return serialized_order


def serialize_restaurant(order_address, restaurant, restaurant_location):
    return {
        'name': restaurant,
        'distance': f'{distance.distance(order_address, restaurant_location).km:.3f}',
    }


def serialize_restaurants(products, locations, order_location):
    restaurant, *others = [
        RestaurantMenuItem.objects
        .filter(product=product)
        .values_list('restaurant') for product in products
    ]
    appropriate_restaurants = restaurant.intersection(*others)

    serialized_restaurants = []
    for restaurant in Restaurant.objects.filter(id__in=appropriate_restaurants):
        order_distance = distance.distance(
            order_location, locations.get(restaurant.address)
        ).km

        serialized_restaurant = {
            'name': restaurant.name,
            'distance': f'{order_distance:.3f}'
        } 
        serialized_restaurants.append(serialized_restaurant)

    return serialized_restaurants


def get_locations(orders):
    order_addresses = {order.address for order in orders}
    restaurants_addresses = {
        restaurant.address for restaurant in Restaurant.objects.all()
    }
    all_addresses = order_addresses | restaurants_addresses

    locations = {
        address: (
            Location.objects.get(address=address).latitude,
            Location.objects.get(address=address).longitude,
        ) for address in all_addresses
    }
    return locations
