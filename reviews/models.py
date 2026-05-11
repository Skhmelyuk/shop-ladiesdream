from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from main.models import Product


RATING_CHOICES = (
    (1, '★☆☆☆☆ (1)'),
    (2, '★★☆☆☆ (2)'),
    (3, '★★★☆☆ (3)'),
    (4, '★★★★☆ (4)'),
    (5, '★★★★★ (5)'),
)

class Review(models.Model):
    product = models.ForeignKey(
        Product, 
        on_delete=models.CASCADE, 
        related_name='reviews', 
        verbose_name="Товар"
    )
    author = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        verbose_name="Автор"
    )
    parent_review = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies',
        verbose_name="Батьківський відгук"
    )
    rating = models.IntegerField(
        choices=RATING_CHOICES, 
        default=5, 
        verbose_name="Оцінка"
    )
    title = models.CharField(
        max_length=100, 
        verbose_name="Заголовок"
    )
    content = models.TextField(
        max_length=1000, 
        verbose_name="Текст відгуку"
    )
    advantages = models.TextField(
        blank=True, 
        verbose_name="Переваги"
    )
    disadvantages = models.TextField(
        blank=True, 
        verbose_name="Недоліки"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Створено"
    )
    updated_at = models.DateTimeField(
        auto_now=True, 
        verbose_name="Оновлено"
    )
    is_active = models.BooleanField(
        default=True, 
        verbose_name="Активний (Модерація)"
    )
    helpful_count = models.IntegerField(
        default=0, 
        verbose_name="Корисно (Лічильник)"
    )
    
    @property
    def is_reply(self):
        """Перевіряє чи є відгук відповіддю"""
        return self.parent_review is not None

    class Meta:
        verbose_name = "Відгук"
        verbose_name_plural = "Відгуки"
        ordering = ['-created_at']

    def __str__(self):
        return f"Відгук {self.rating}★ на {self.product.name} від {self.author.username}"

    def get_rating_display_stars(self):
        """Повертає рядок зірок для відображення оцінки."""
        full_stars = '★' * self.rating
        empty_stars = '☆' * (5 - self.rating)
        return full_stars + empty_stars


class ReviewReply(models.Model):
    """Відповідь адміністратора на відгук"""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='admin_replies',
        verbose_name="Відгук"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Автор (адмін)"
    )
    content = models.TextField(
        max_length=1000,
        verbose_name="Текст відповіді"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Створено"
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Оновлено"
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна"
    )

    class Meta:
        verbose_name = "Відповідь адміністратора"
        verbose_name_plural = "Відповіді адміністратора"
        ordering = ['created_at']

    def __str__(self):
        return f"Відповідь від {self.author.username} на відгук #{self.review.id}"


class ReviewImage(models.Model):
    """Зображення до відгуку"""
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='images',
        verbose_name="Відгук"
    )
    image = models.ImageField(
        upload_to='reviews/images/', 
        verbose_name="Зображення"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Створено"
    )
    
    class Meta:
        verbose_name = "Зображення відгуку"
        verbose_name_plural = "Зображення відгуків"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Зображення для відгуку {self.review.id}"


class ReviewVideo(models.Model):
    """Відео до відгуку"""
    review = models.ForeignKey(
        Review, 
        on_delete=models.CASCADE, 
        related_name='videos',
        verbose_name="Відгук"
    )
    video = models.FileField(
        upload_to='reviews/videos/', 
        verbose_name="Відео"
    )
    thumbnail = models.ImageField(
        upload_to='reviews/thumbnails/', 
        blank=True, 
        null=True,
        verbose_name="Прев'ю"
    )
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Створено"
    )
    
    class Meta:
        verbose_name = "Відео відгуку"
        verbose_name_plural = "Відео відгуків"
        ordering = ['created_at']
    
    def __str__(self):
        return f"Відео для відгуку {self.review.id}"