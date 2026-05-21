from django.db import models
from django.contrib.auth.models import User

class AbandonedCart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='abandoned_cart')
    cart_data = models.JSONField(default=dict)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Покинутий кошик"
        verbose_name_plural = "Покинуті кошики"

    def __str__(self):
        return f"Кошик {self.user.username}"
