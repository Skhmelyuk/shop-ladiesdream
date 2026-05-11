from django.db import models
from main.models import Product
from django.contrib.auth.models import User
from discounts.models import Discount
from decimal import Decimal

DELIVERY_CHOICES = [
   ('NP', 'Нова Пошта'),
   ('UP', 'УкрПошта'),
   ('COURIER', 'Кур’єрська доставка'),
   ('PICKUP', 'Самовивіз'),
]

STATUS_CHOICES = [
    ('new', 'Нове'),
    ('processing', 'В обробці'),
    ('shipped', 'Відправлено'),
    ('delivered', 'Доставлено'),
    ('cancelled', 'Скасовано'),
]

payment_choices = [
    ("cod", "Післяплата"),
    ("online", "Онлайн оплата"),
]

class PromoCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_percent = models.PositiveIntegerField()

    def apply_discount(self, total_amount):
        """Повертає суму знижки в гривнях"""
        return (total_amount * Decimal(self.discount_percent) / Decimal(100)).quantize(Decimal('0.01'))
    
    def __str__(self):
        return self.code

class Order(models.Model):

    user = models.ForeignKey(
        User, 
        related_name='orders', 
        on_delete=models.SET_NULL,
        null=True, 
        blank=True, 
        verbose_name="Користувач"
    )

    first_name = models.CharField(max_length=50, verbose_name="Ім'я")
    last_name = models.CharField(max_length=50, verbose_name="Прізвище")
    email = models.EmailField(verbose_name="Електронна пошта")
    phone = models.CharField(max_length=20, verbose_name="Телефон", blank=True)
    # address = models.CharField(max_length=250, verbose_name="Адреса доставки")
    delivery_type = models.CharField(
    max_length=10,
    choices=DELIVERY_CHOICES,
    default='NP',
    verbose_name="Спосіб доставки")
    city = models.CharField(max_length=250, verbose_name="Місто доставки")
    delivery_address = models.CharField(max_length=250, verbose_name="Адреса / Відділення")

    is_billing_address_same = models.BooleanField(
       default=True,
       verbose_name="Адреса доставки збігається з адресою платника"
   )
    
    promo_code = models.CharField(
        max_length=50, 
        blank=True, 
        null=True, 
        verbose_name="Промокод (код)"
    )
    # discount_percent = models.PositiveIntegerField(
    #     default=0, 
    #     verbose_name="Знижка, %"
    # )
    discounted_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        verbose_name="Сума знижки"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=payment_choices,
        default="cod"
    )
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    paid = models.BooleanField(default=False, verbose_name="Оплачено")
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name="Статус"
    )
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created']),
        ]
        verbose_name = "Замовлення"
        verbose_name_plural = "Замовлення"

    def __str__(self):
        return f'Замовлення {self.id}'
    
    def get_total_cost(self):
        total_items_cost = sum(item.get_cost() for item in self.items.all())
        final_cost = total_items_cost - self.discounted_amount
        return max(Decimal('0.00'), final_cost)



class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE,
        verbose_name="Замовлення"
    )
    product = models.ForeignKey(
        Product,
        related_name='order_items',
        on_delete=models.CASCADE,
        verbose_name="Товар"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна за одиницю")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")

    class Meta:
        verbose_name = "Позиція замовлення"
        verbose_name_plural = "Позиції замовлення"
        
    def __str__(self):
        return str(self.id)

    def get_cost(self):
        """Розраховує вартість позиції (ціна * кількість)."""
        if self.price is None:
            return Decimal('0.00')
        return self.price * self.quantity