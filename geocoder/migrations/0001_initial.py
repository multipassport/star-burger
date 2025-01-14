# Generated by Django 3.2 on 2021-08-06 14:09

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=100, unique=True, verbose_name='адрес')),
                ('latitude', models.FloatField(verbose_name='широта')),
                ('longitude', models.FloatField(verbose_name='долгота')),
                ('request_date', models.DateTimeField(default=django.utils.timezone.now, verbose_name='дата запроса к геокодеру')),
            ],
            options={
                'verbose_name': 'место',
                'verbose_name_plural': 'места',
            },
        ),
    ]
