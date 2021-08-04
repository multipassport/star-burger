# Generated by Django 3.2 on 2021-08-04 20:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20210804_1957'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment_method',
            field=models.CharField(choices=[('CASH', 'Наличными'), ('CARD', 'Электронно')], default='CASH', max_length=5, verbose_name='Способ оплаты'),
        ),
    ]
