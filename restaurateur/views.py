from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views
from geopy import distance
from operator import itemgetter

from foodcartapp.models import Product, Restaurant, Order
from geocoder.models import Location


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
        return render(request, "login.html", context={
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
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
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

    return render(request, template_name="products_list.html", context={
        'products_with_restaurants': products_with_restaurants,
        'restaurants': restaurants,
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
    })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    orders = Order.objects.get_total_cost()
    return render(request, template_name='order_items.html', context={
        'order_items': [serialize_order(order) for order in orders],
    })


def serialize_order(order):
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
    restaurants = [
        serialize_restaurant(order.address, restaurant)
        for restaurant in order.restaurants.all()
    ]
    serialized_order['restaurants'] = sorted(
        restaurants, key=itemgetter('distance')
    )

    return serialized_order


def serialize_restaurant(order_address, restaurant):
    return {
        'name': restaurant.name,
        'distance': (calculate_distance(order_address, restaurant.address))
    }


def calculate_distance(first_address, second_address):
    order_location, _ = Location.objects.get_or_create(address=first_address)
    restaurant_location, _ = Location.objects.get_or_create(address=second_address)
    order_coordinates = order_location.latitude, order_location.longitude
    restaurant_coordinates = restaurant_location.latitude, restaurant_location.longitude
    order_distance = distance.distance(order_coordinates, restaurant_coordinates).km
    return f'{order_distance:.3f} км'
