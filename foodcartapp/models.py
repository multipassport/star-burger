from django.db import models
from django.core.validators import MinValueValidator, MaxLengthValidator
from django.utils import timezone
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderPositionQuerySet(models.QuerySet):
    def get_total_cost(self):
        return (
            self.annotate(cost=models.Sum(models.F('positions__price')))
            .prefetch_related('restaurants')
        )


class Order(models.Model):
    STATUS = (
        ('UNANSWERED', 'Не обработан'),
        ('EN_ROUTE', 'В пути'),
        ('COMPLETED', 'Выполнен'),
    )
    PAYMENT_METHODS = (
        ('CASH', 'Наличными'),
        ('CARD', 'Электронно'),
    )
    firstname = models.CharField(
        'имя',
        max_length=50,
    )
    lastname = models.CharField(
        'фамилия',
        max_length=50,
    )
    phonenumber = PhoneNumberField(
        'номер телефона',
        max_length=12,
        validators=[MaxLengthValidator(12)]
    )
    address = models.CharField(
        'адрес',
        max_length=100,
    )

    status = models.CharField(
        'статус',
        max_length=12,
        choices=STATUS,
        default='UNANSWERED',
    )
    note = models.TextField(
        'комментарий к заказу',
        max_length=200,
        blank=True,
    )
    payment_method = models.CharField(
        'Способ оплаты',
        max_length=5,
        choices=PAYMENT_METHODS,
        default='CASH',
    )

    created_at = models.DateTimeField(
        'создан в',
        default=timezone.now,
    )
    called_at = models.DateTimeField(
        'принят в',
        blank=True,
        null=True,
    )
    delivered_at = models.DateTimeField(
        'доставлен в',
        blank=True,
        null=True,
    )

    restaurants = models.ManyToManyField(
        Restaurant,
        related_name='orders',
        verbose_name='ресторан',
    )

    objects = OrderPositionQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname}'


class OrderPosition(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='positions',
        verbose_name='заказ',
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='positions',
        verbose_name='продукт',
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveSmallIntegerField(
        'число продуктов',
        validators=[MinValueValidator(1)],
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
    )

    def get_price(self):
        self.price = self.quantity * self.product.price

    class Meta:
        verbose_name = 'позиция'
        verbose_name_plural = 'позиции'

    def __str__(self):
        return self.product.name
