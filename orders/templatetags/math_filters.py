from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Множення чисел"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    """Ділення чисел"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def subtract(value, arg):
    """Віднімання чисел"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
