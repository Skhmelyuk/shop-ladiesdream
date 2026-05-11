from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from main.models import Product


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Відсоток (%)'),
        ('fixed', 'Фіксована сума (грн)'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='discounts', verbose_name='Товар')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, verbose_name='Тип знижки')
    value = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Значення')
    start_date = models.DateTimeField(verbose_name='Початок дії')
    end_date = models.DateTimeField(verbose_name='Кінець дії')
    is_active = models.BooleanField(default=True, verbose_name='Активна')
    min_quantity = models.IntegerField(default=1, verbose_name='Мінімальна кількість')
    description = models.TextField(blank=True, verbose_name='Опис акції')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Знижка'
        verbose_name_plural = 'Знижки'

    def __str__(self):
        return f"{self.product.name} - {self.value} ({self.get_discount_type_display()})"

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date

    def calculate_discount(self, price, quantity=1):
        if not self.is_valid() or quantity < self.min_quantity:
            return 0
        if self.discount_type == 'percentage':
            return price * (self.value / 100)
        return self.value

    def get_discounted_price(self, price, quantity=1):
        discount = self.calculate_discount(price, quantity)
        return max(price - discount, 0)

    def clean(self):
        if self.discount_type == 'percentage' and not (0 < self.value <= 100):
            raise ValidationError("Відсоткова знижка має бути в межах 0-100%.")
        if self.discount_type == 'fixed' and self.value <= 0:
            raise ValidationError("Фіксована знижка має бути більшою за 0.")
        if self.end_date <= self.start_date:
            raise ValidationError("Дата закінчення повинна бути після початку.")
        if self.min_quantity < 1:
            raise ValidationError("Мінімальна кількість має бути не менше 1.")
class PromoCode(models.Model):
    DISCOUNT_CHOICES = [
        ('percentage', 'Відсоток'),
        ('fixed', 'Фіксована сума'),
        ('free_shipping', 'Безкоштовна доставка'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='Код')
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_CHOICES)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    usage_limit = models.IntegerField(null=True, blank=True)
    used_count = models.IntegerField(default=0)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоди'

    def __str__(self):
        return self.code

    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date and (not self.usage_limit or self.used_count < self.usage_limit)

    def can_be_used(self):
        return self.is_valid()

    def apply_discount(self, order_amount):
        if not self.is_valid() or order_amount < self.min_order_amount:
            return 0
        if self.discount_type == 'percentage':
            return order_amount * (self.value / 100)
        elif self.discount_type == 'fixed':
            return min(order_amount, self.value)
        elif self.discount_type == 'free_shipping':
            return 0  # тут додати логіку безкоштовної доставки
        return 0

    def increment_usage(self):
        self.used_count += 1
        self.save()

    def clean(self):
        self.code = self.code.upper().replace(" ", "")
        if len(self.code) < 4:
            raise ValidationError("Код має бути не менше 4 символів.")
        if self.discount_type == 'percentage' and not (0 < self.value <= 100):
            raise ValidationError("Відсоткова знижка має бути в межах 0-100%.")
        if self.discount_type == 'fixed' and self.value <= 0:
            raise ValidationError("Фіксована знижка має бути більшою за 0.")
        if self.end_date <= self.start_date:
            raise ValidationError("Дата закінчення повинна бути після початку.")


class PromoCodeUsage(models.Model):
    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='promo_usages')
    order_amount = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']
        verbose_name = 'Використання промокоду'
        verbose_name_plural = 'Використання промокодів'

    def __str__(self):
        return f"{self.user.username} - {self.promo_code.code}"