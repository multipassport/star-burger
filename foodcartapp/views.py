import json

from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order, OrderPosition


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
def register_order(request):
    cart = request.data
    try:
        products = cart['products']
    except KeyError:
        return Response({'products': 'Order should contain a \'products\' key'})
    if not products:
        return Response({'products': 'This field cannot be empty.'})
    if not isinstance(products, list):
        return Response({'products': 'This field should receive a list.'})
    order = Order.objects.create(
        first_name=cart['firstname'],
        last_name=cart['lastname'],
        phone_number=cart['phonenumber'],
        address=cart['address'],
    )
    for position in cart['products']:
        OrderPosition.objects.create(
            order_id=order.id,
            product_id=position['product'],
            count=position['quantity'],
        )
    return Response(cart)
