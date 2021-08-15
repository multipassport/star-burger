import requests

from django.db import transaction
from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer

from .models import Product, Order, OrderPosition, RestaurantMenuItem
from geocoder.models import Location
from star_burger.settings import YANDEX_GEOCODE_APIKEY


class OrderPositionSerializer(ModelSerializer):
    class Meta:
        model = OrderPosition
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    products = OrderPositionSerializer(
        many=True, allow_empty=False, write_only=True,
    )

    class Meta:
        model = Order
        fields = [
            'id',
            'firstname',
            'lastname',
            'phonenumber',
            'address',
            'products',
        ]


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            },
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


@api_view(['POST'])
@transaction.atomic
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    valid_data = serializer.validated_data

    order = Order.objects.create(
        firstname=valid_data['firstname'],
        lastname=valid_data['lastname'],
        phonenumber=valid_data['phonenumber'],
        address=valid_data['address'],
    )
    positions = [
        OrderPosition(order=order, **fields)
        for fields in valid_data['products']
    ]

    products = [item['product'] for item in valid_data['products']]

    for position in positions:
        position.price = position.calculate_actual_price()

    try:
        create_location(valid_data['address'])
    except IndexError:
        transaction.rollback()
        return Response('Invalid address', status=status.HTTP_400_BAD_REQUEST)

    OrderPosition.objects.bulk_create(positions)

    return Response(OrderSerializer(order).data)


def choose_restaurant(products, order):
    products_restaurants = []
    for product in products:
        restaurants = [
            item.restaurant for item in
            RestaurantMenuItem.objects.filter(product__exact=product)
        ]
        products_restaurants.append(set(restaurants))
    first_restaurant, *others_restaurants = products_restaurants
    suitable_restaurants = first_restaurant.intersection(*others_restaurants)

    order.restaurant.set(suitable_restaurants)
    order.save()


def create_location(address):
    location, created = Location.objects.get_or_create(address=address)
    if not created:
        return None
    latitude, longitude = fetch_coordinates(address)
    location.latitude = latitude
    location.longitude = longitude
    location.save()


def fetch_coordinates(place):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    payload = {
        'geocode': place, 'apikey': YANDEX_GEOCODE_APIKEY, 'format': 'json'
    }

    response = requests.get(base_url, params=payload)
    response.raise_for_status()

    found_places = response.json()['response']['GeoObjectCollection']['featureMember']
    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lat, lon
