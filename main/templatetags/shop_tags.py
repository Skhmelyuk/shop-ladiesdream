from django import template
from django.utils import timezone
from datetime import datetime
from main.models import Product

register = template.Library()

@register.simple_tag
def get_products_count():
    """Повертає загальну кількість товарів у базі даних."""
    try:
        return Product.objects.count()
    except Exception:
        return 0

@register.simple_tag
def calculate_total(items):
    """Обчислює загальну суму, множачи ціну на кількість для кожного елемента."""
    total = 0
    if items:
        for item in items:
            price = getattr(item, 'price', None)
            if price is not None:
                 total += float(price)
    
    return f"{total:,.2f}".replace(",", " ")

@register.simple_tag
def user_greeting(user):
    """Повертає привітання залежно від часу доби (Доброго ранку/дня/вечора)."""
    
    if not user or not user.is_authenticated:
        return "Ласкаво просимо!"
        
    current_hour = datetime.now().hour
    username = user.first_name or user.username
    
    if 6 <= current_hour < 12:
        greeting = "Доброго ранку"
    elif 12 <= current_hour < 18:
        greeting = "Доброго дня"
    else:
        greeting = "Доброго вечора"
        
    return f"{greeting}, {username}!"

@register.inclusion_tag('main/components/product_card_tag.html')
def show_product_card(product, delay=0):
    """
    Відображає картку товару. 
    Використовує окремий шаблон product_card_tag.html.
    """
    return {'product': product, 'delay': delay}


@register.inclusion_tag('main/components/popular_products_widget.html')
def show_popular_products(limit=3):
    """
    Відображає віджет з найбільш популярними товарами (за переглядами).
    Використовує окремий шаблон popular_products_widget.html.
    """
    try:
        popular_products = Product.objects.all().order_by('-views')[:limit]
    except Exception:
        popular_products = []
        
    return {'popular_products': popular_products}