# Generated by Django 3.2 on 2021-09-19 17:27

import django.core.validators
from django.db import migrations
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0048_auto_20210822_0945'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='phonenumber',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=20, region=None, validators=[django.core.validators.MaxLengthValidator(12)], verbose_name='номер телефона'),
        ),
        migrations.AlterField(
            model_name='restaurant',
            name='contact_phone',
            field=phonenumber_field.modelfields.PhoneNumberField(max_length=20, region=None, validators=[django.core.validators.MaxLengthValidator(12)], verbose_name='контактный телефон'),
        ),
    ]
