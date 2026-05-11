from .models import Order
from django.db.models import Sum

def get_user_discount_stats(user):
    orders_with_discount = Order.objects.filter(user=user, discount__isnull=False)
    total_usage = orders_with_discount.count()
    total_savings = orders_with_discount.aggregate(total=Sum('discounted_amount'))['total'] or 0
    return total_usage, total_savings, orders_with_discount
