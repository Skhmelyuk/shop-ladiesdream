from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Користувач")
    bio = models.TextField(blank=True, verbose_name="Біографія")
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/',
        blank=True,
        verbose_name="Аватар"
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name="Дата народження")
    location = models.CharField(max_length=100, blank=True, verbose_name="Місто")
    website = models.URLField(blank=True, verbose_name="Веб-сайт")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return f"Профіль {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Автоматично створює профіль при створенні користувача."""
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Автоматично зберігає профіль при збереженні користувача."""
    if hasattr(instance, 'profile'):
        instance.profile.save()
