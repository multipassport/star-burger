# Generated by Django 3.2 on 2021-08-04 17:22

from django.db import migrations


def fill_price_field(apps, schema_editor):
    OrderPosition = apps.get_model('foodcartapp', 'OrderPosition')
    positions = OrderPosition.objects.select_related('product')

    for position in positions:
        if not position.price:
            position.price = position.quantity * position.product.price

    positions.bulk_update(positions, ['price'])


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0039_orderposition_price'),
    ]

    operations = [
        migrations.RunPython(fill_price_field),
    ]
