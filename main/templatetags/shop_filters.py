from django import template
from django.utils import timezone
import datetime

register = template.Library()

@register.filter
def currency(value):
    """Форматує число як ціну у гривнях (грн)."""
    try:
        return f"{float(value):,.2f} грн".replace(",", " ")
    except (ValueError, TypeError):
        return value

@register.filter
def discount_percentage(original_price, discounted_price):
    """Обчислює відсоток знижки між двома цінами."""
    try:
        original = float(original_price)
        discounted = float(discounted_price)
        if original > 0 and original > discounted:
            percent = ((original - discounted) / original) * 100
            return int(percent)
        return 0
    except (ValueError, TypeError):
        return 0

@register.filter
def compact_number(num):
    """Скорочує великі числа до K (тисяч), M (мільйонів)."""
    try:
        num = float(num)
        if num >= 1_000_000:
            return f'{num/1_000_000:.1f}M'
        if num >= 1_000:
            return f'{num/1_000:.1f}K'
        return int(num)
    except (ValueError, TypeError):
        return num

@register.filter
def time_ago(value):
    """Форматує datetime об'єкт у формат "X годин тому"."""
    if not value:
        return ""
        
    now = timezone.now() if timezone.is_aware(value) else datetime.datetime.now()
    diff = now - value

    if diff.days > 365:
        return f'{diff.days // 365} років тому'
    if diff.days > 30:
        return f'{diff.days // 30} місяців тому'
    if diff.days > 0:
        return f'{diff.days} днів тому'
    if diff.seconds > 3600:
        return f'{diff.seconds // 3600} годин тому'
    if diff.seconds > 60:
        return f'{diff.seconds // 60} хвилин тому'
    
    return "щойно"

@register.filter
def mul(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def add(value, arg):
    try:
        return float(value) + float(arg)
    except (ValueError, TypeError):
        return ''