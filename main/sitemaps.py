from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Category, Product

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['main:product-list', 'main:about', 'main:contact']

    def location(self, item):
        return reverse(item)

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7

    def items(self):
        return Category.objects.filter(is_active=True)

class ProductSitemap(Sitemap):
    changefreq = 'daily'
    priority = 0.9

    def items(self):
        return Product.objects.filter(is_available=True).order_by('-updated_at')

    def lastmod(self, obj):
        return obj.updated_at
