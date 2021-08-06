from django.db import models
from django.utils import timezone


class Location(models.Model):
    address = models.CharField(
        'адрес',
        max_length=100,
        unique=True,
    )
    latitude = models.FloatField(
        'широта',
        null=True,
    )
    longitude = models.FloatField(
        'долгота',
        null=True,
    )
    request_date = models.DateTimeField(
        'дата запроса к геокодеру',
        default=timezone.now,
    )

    class Meta():
        verbose_name = 'место'
        verbose_name_plural = 'места'

    def __str__(self):
        return self.address
