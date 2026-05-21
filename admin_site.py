from django.contrib.admin import AdminSite
from django.db.models import Sum, Count, Avg
from django.utils import timezone
from datetime import timedelta


class LadiesDreamAdminSite(AdminSite):
    site_header = "LadiesDream — Адмін панель"
    site_title = "LadiesDream Admin"
    index_title = "Дашборд"

    def index(self, request, extra_context=None):
        from main.models import Product, Category
        from orders.models import Order
        from django.contrib.auth.models import User
        from reviews.models import Review
        from discounts.models import PromoCode

        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        total_revenue = (
            Order.objects.filter(paid=True)
            .aggregate(total=Sum('final_price'))['total'] or 0
        )
        month_revenue = (
            Order.objects.filter(paid=True, created__date__gte=month_ago)
            .aggregate(total=Sum('final_price'))['total'] or 0
        )
        paid_orders_count = Order.objects.filter(paid=True).count()
        avg_check = round(total_revenue / paid_orders_count, 2) if paid_orders_count else 0

        sales_by_day = []
        max_day_revenue = 0
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            revenue = (
                Order.objects.filter(paid=True, created__date=day)
                .aggregate(total=Sum('final_price'))['total'] or 0
            )
            sales_by_day.append({'date': day.strftime('%d.%m'), 'revenue': float(revenue)})
            if float(revenue) > max_day_revenue:
                max_day_revenue = float(revenue)

        from orders.models import OrderItem
        top_products = (
            OrderItem.objects
            .values('product__name', 'product__id')
            .annotate(total_qty=Sum('quantity'))
            .order_by('-total_qty')[:5]
        )

        stats = {
            'total_products': Product.objects.count(),
            'total_categories': Category.objects.count(),
            'total_orders': Order.objects.count(),
            'paid_orders': paid_orders_count,
            'unpaid_orders': Order.objects.filter(paid=False).count(),
            'orders_today': Order.objects.filter(created__date=today).count(),
            'orders_week': Order.objects.filter(created__date__gte=week_ago).count(),
            'total_users': User.objects.count(),
            'new_users_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
            'total_revenue': total_revenue,
            'month_revenue': month_revenue,
            'avg_check': avg_check,
            'total_reviews': Review.objects.count(),
            'active_reviews': Review.objects.filter(is_active=True).count(),
            'active_promos': PromoCode.objects.filter(is_active=True).count(),
            'recent_orders': Order.objects.select_related('user').order_by('-created')[:8],
            'sales_by_day': sales_by_day,
            'max_day_revenue': max_day_revenue or 1,
            'top_products': top_products,
            'new_orders_count': Order.objects.filter(status='new').count(),
        }

        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().index(request, extra_context)


admin_site = LadiesDreamAdminSite(name='admin')

try:
    from django_celery_beat.models import (
        PeriodicTask, IntervalSchedule, CrontabSchedule, ClockedSchedule, SolarSchedule
    )
    from django_celery_beat.admin import (
        PeriodicTaskAdmin, IntervalScheduleAdmin, CrontabScheduleAdmin, ClockedScheduleAdmin, SolarScheduleAdmin
    )
    
    admin_site.register(PeriodicTask, PeriodicTaskAdmin)
    admin_site.register(IntervalSchedule, IntervalScheduleAdmin)
    admin_site.register(CrontabSchedule, CrontabScheduleAdmin)
    admin_site.register(ClockedSchedule, ClockedScheduleAdmin)
    admin_site.register(SolarSchedule, SolarScheduleAdmin)
except ImportError:
    pass

