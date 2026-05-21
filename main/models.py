import os
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from ckeditor_uploader.fields import RichTextUploadingField
from django.utils import timezone
from decimal import Decimal

def slugify_uk(text):
    translit_map = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'h', 'ґ': 'g', 'д': 'd', 'е': 'e', 'є': 'ye', 'ж': 'zh', 'з': 'z',
        'и': 'y', 'і': 'i', 'ї': 'yi', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p',
        'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'kh', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'shch',
        'ь': '', 'ю': 'yu', 'я': 'ya',
        'А': 'a', 'Б': 'b', 'В': 'v', 'Г': 'h', 'Ґ': 'g', 'Д': 'd', 'Е': 'e', 'Є': 'ye', 'Ж': 'zh', 'З': 'z',
        'И': 'y', 'І': 'i', 'Ї': 'yi', 'Й': 'y', 'К': 'k', 'Л': 'l', 'М': 'm', 'Н': 'n', 'О': 'o', 'П': 'p',
        'Р': 'r', 'С': 's', 'Т': 't', 'У': 'u', 'Ф': 'f', 'Х': 'kh', 'Ц': 'ts', 'Ч': 'ch', 'Ш': 'sh', 'Щ': 'shch',
        'Ь': '', 'Ю': 'yu', 'Я': 'ya'
    }
    res = []
    for c in text:
        res.append(translit_map.get(c, c))
    translit_text = "".join(res)
    from django.utils.text import slugify
    return slugify(translit_text)

def category_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    name = instance.slug or slugify_uk(instance.name) or "category"
    return os.path.join("categories", f"{name}.{ext}")

def product_main_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    category_slug = instance.category.slug if (instance.category and instance.category.slug) else "no-category"
    product_slug = instance.slug or slugify_uk(instance.name) or "product"
    base_name = filename.rsplit('.', 1)[0]
    clean_base = slugify_uk(base_name) or "main"
    return os.path.join("products", category_slug, product_slug, "main", f"{clean_base}.{ext}")

def product_gallery_image_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    product = instance.product
    category_slug = product.category.slug if (product.category and product.category.slug) else "no-category"
    product_slug = product.slug or slugify_uk(product.name) or "product"
    base_name = filename.rsplit('.', 1)[0]
    clean_base = slugify_uk(base_name) or "gallery"
    
    if instance.color:
        color_slug = slugify_uk(instance.color.name)
        return os.path.join("products", category_slug, product_slug, color_slug, f"{clean_base}.{ext}")
    else:
        return os.path.join("products", category_slug, product_slug, "general", f"{clean_base}.{ext}")



try:
    from discounts.models import Discount 
except ImportError:
    Discount = None


class Supplier(models.Model):
    name = models.CharField(max_length=200, unique=True, verbose_name='Назва')
    website = models.URLField(blank=True, verbose_name='Сайт')
    notes = models.TextField(blank=True, verbose_name='Нотатки')

    class Meta:
        ordering = ('name',)
        verbose_name = 'Постачальник/Виробник'
        verbose_name_plural = 'Постачальники/Виробники'

    def __str__(self):
        return self.name

class Size(models.Model):
    name = models.CharField(max_length=20)

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=30)
    hex_code = models.CharField(max_length=7)
    in_stock = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, db_index=True, verbose_name="Назва")
    slug = models.SlugField(max_length=100, unique=True, verbose_name="URL-адреса")
    description = models.TextField(blank=True, verbose_name="Опис")
    image = models.ImageField(upload_to=category_image_upload_path, blank=True, verbose_name="Зображення")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    # SEO поля
    seo_title = models.CharField(
        max_length=150, 
        blank=True, 
        verbose_name="SEO Заголовок (Title)",
        help_text="Відображається у вкладці браузера та заголовку пошукової видачі Google (до 60-70 символів). Якщо порожнє — береться назва категорії."
    )
    seo_description = models.TextField(
        blank=True, 
        verbose_name="SEO Опис (Description)",
        help_text="Короткий опис сторінки в пошуковій видачі (сніпет, 140-160 символів). Якщо порожнє — автогенерація з опису категорії."
    )
    seo_keywords = models.CharField(
        max_length=250, 
        blank=True, 
        verbose_name="SEO Ключові слова",
        help_text="Ключові запити через кому (напр. 'піжами, жіноча білизна'). Якщо порожнє — генерується автоматично."
    )

    class Meta:
        ordering = ('name',)
        verbose_name = "Категорія"
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        """Повертає URL для фільтрації товарів за цією категорією."""
        return reverse('main:product_list_by_category', args=[self.slug])

    def get_seo_title(self):
        return self.seo_title or self.name

    def get_seo_description(self):
        return self.seo_description or self.description or f"Категорія {self.name} в інтернет-магазині LadiesDream."

    def get_seo_keywords(self):
        return self.seo_keywords or f"{self.name}, жіночий одяг, купити {self.name}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Категорія"
    )
    supplier = models.ForeignKey(
        'Supplier',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Постачальник/Виробник'
    )
    name = models.CharField(max_length=200, db_index=True, verbose_name="Назва")
    slug = models.SlugField(max_length=200, unique=True, verbose_name="URL-адреса")
    description = models.TextField(blank=True, verbose_name="Опис")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    is_available = models.BooleanField(default=True, db_index=True, verbose_name="В наявності")
    sizes = models.ManyToManyField(
        Size, 
        blank=True, 
        verbose_name="Доступні розміри",
        help_text="Оберіть розміри, які є або будуть в наявності для цього товару. Вони відображатимуться у фільтрах каталогу та як кнопки вибору на картці товару."
    )
    colors = models.ManyToManyField(
        Color, 
        blank=True, 
        verbose_name="Доступні кольори",
        help_text="Оберіть кольори, в яких виготовляється цей товар. Вони використовуються для фільтрації в каталозі та вибору варіантів купівлі."
    )
    image = models.ImageField(upload_to=product_main_image_upload_path, blank=True, null=True, verbose_name="Головне фото")

    # SEO поля
    seo_title = models.CharField(
        max_length=150, 
        blank=True, 
        verbose_name="SEO Заголовок (Title)",
        help_text="Відображається у вкладці браузера та заголовку пошукової видачі Google (до 60-70 символів). Якщо порожнє — береться назва товару."
    )
    seo_description = models.TextField(
        blank=True, 
        verbose_name="SEO Опис (Description)",
        help_text="Короткий опис сторінки в пошуковій видачі (сніпет, 140-160 символів). Якщо порожнє — автогенерація з опису товару."
    )
    seo_keywords = models.CharField(
        max_length=250, 
        blank=True, 
        verbose_name="SEO Ключові слова",
        help_text="Ключові запити через кому (напр. 'купити піжаму, шовкова піжама'). Якщо порожнє — генерується автоматично."
    )

    def images(self):
        return self.gallery.all()[:10]

    def get_thumbnail_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            thumb_path = os.path.join(dir_name, f"{base_name}_thumbnail.webp")
            if os.path.exists(thumb_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_thumbnail.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    def get_catalog_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            catalog_path = os.path.join(dir_name, f"{base_name}_catalog.webp")
            if os.path.exists(catalog_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_catalog.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    def get_card_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            card_path = os.path.join(dir_name, f"{base_name}_card.webp")
            if os.path.exists(card_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_card.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    views = models.IntegerField(default=0, verbose_name="Перегляди")
    featured = models.BooleanField(default=False, verbose_name="Рекомендований")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    detailed_description = RichTextUploadingField(
        blank=True, 
        null=True, 
        verbose_name="Детальний опис")
    
    discount_percent = models.IntegerField(
        default=0, 
        verbose_name="Постійна знижка (%)"
    ) 

    discount_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_label = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = "Товар"
        verbose_name_plural = "Товари"
        indexes = [
            models.Index(fields=['id', 'slug']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('main:product-detail', kwargs={
            'id': self.id, 
            'slug': self.slug
        })

    def get_seo_title(self):
        return self.seo_title or self.name

    def get_seo_description(self):
        if self.seo_description:
            return self.seo_description
        from django.utils.html import strip_tags
        desc = strip_tags(self.description or "")
        return desc[:157] + "..." if len(desc) > 160 else desc

    def get_seo_keywords(self):
        return self.seo_keywords or f"{self.name}, купити {self.name}, жіночий одяг"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
        
    def get_current_price(self):
        base_price = self.price

        if not isinstance(base_price, Decimal):
            base_price = Decimal(str(base_price))

        active_discount = None
        if Discount:
            active_discount = Discount.objects.filter(
                product=self, 
                is_active=True,
                start_date__lte=timezone.now(),
                end_date__gte=timezone.now(),
            ).first()
            
        if active_discount:
            discount_value = Decimal(str(active_discount.value))
            
            if active_discount.discount_type == 'percentage':
                discount_amount = base_price * (discount_value / Decimal('100'))
                return base_price - discount_amount
            
            elif active_discount.discount_type == 'fixed':
                return max(Decimal('0'), base_price - discount_value)

        elif self.discount_percent and self.discount_percent > 0:
            discount_percentage = Decimal(str(self.discount_percent))
            discount_amount = base_price * (discount_percentage / Decimal('100'))
            return base_price - discount_amount

        return base_price
    

    def get_discounted_price(self):
        return self.get_current_price()


    def get_average_rating(self):
        """Розраховує середній рейтинг активних відгуків."""
        average = self.reviews.filter(is_active=True).aggregate(Avg('rating'))
        return round(average['rating__avg'], 1) if average['rating__avg'] else 0.0

    def get_reviews_count(self):
        """Повертає кількість активних відгуків."""
        return self.reviews.filter(is_active=True).count()
        
    def get_rating_distribution(self):
        """Повертає розподіл оцінок (1-5 зірок)."""
        distribution = {}
        total_reviews = self.get_reviews_count()
        
        counts = self.reviews.filter(is_active=True).values('rating').annotate(count=Count('rating'))
        
        for i in range(1, 6):
            count_obj = next((item for item in counts if item['rating'] == i), None)
            count = count_obj['count'] if count_obj else 0
            percent = (count / total_reviews * 100) if total_reviews else 0
            
            distribution[i] = {
                'count': count,
                'percent': round(percent),
                'stars': '★' * i + '☆' * (5 - i)
            }
            

        return dict(sorted(distribution.items(), reverse=True))
    


class ProductImage(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="gallery"
    )
    image = models.ImageField(upload_to=product_gallery_image_upload_path)
    order = models.PositiveIntegerField(default=0)
    color = models.ForeignKey(
        Color,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Колір товару",
        help_text="Залиште порожнім — фото відображатиметься для всіх кольорів",
    )

    def get_thumbnail_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            thumb_path = os.path.join(dir_name, f"{base_name}_thumbnail.webp")
            if os.path.exists(thumb_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_thumbnail.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    def get_catalog_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            catalog_path = os.path.join(dir_name, f"{base_name}_catalog.webp")
            if os.path.exists(catalog_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_catalog.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    def get_card_url(self):
        if not self.image:
            return ""
        import os
        try:
            orig_path = self.image.path
            dir_name = os.path.dirname(orig_path)
            base_name = os.path.splitext(os.path.basename(orig_path))[0]
            card_path = os.path.join(dir_name, f"{base_name}_card.webp")
            if os.path.exists(card_path):
                rel_path = os.path.join(os.path.dirname(self.image.name), f"{base_name}_card.webp")
                from django.conf import settings
                return f"{settings.MEDIA_URL}{rel_path}"
        except Exception:
            pass
        return self.image.url

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"Image for {self.product.name}"

class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="variants"
    )

    size = models.ForeignKey(Size, on_delete=models.CASCADE)

    color = models.ForeignKey(
        Color,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    stock = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = [('product', 'size', 'color')]
        verbose_name = "Варіант товару"
        verbose_name_plural = "Варіанти товару"

    def __str__(self):
        return f"{self.product.name} {self.size} {self.color}"
