from django.contrib.admin import AdminSite
from django.db.models import Sum, Count
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

        stats = {
            'total_products': Product.objects.count(),
            'total_categories': Category.objects.count(),
            'total_orders': Order.objects.count(),
            'paid_orders': Order.objects.filter(paid=True).count(),
            'unpaid_orders': Order.objects.filter(paid=False).count(),
            'orders_today': Order.objects.filter(created__date=today).count(),
            'orders_week': Order.objects.filter(created__date__gte=week_ago).count(),
            'total_users': User.objects.count(),
            'new_users_week': User.objects.filter(date_joined__date__gte=week_ago).count(),
            'total_revenue': total_revenue,
            'month_revenue': month_revenue,
            'total_reviews': Review.objects.count(),
            'active_reviews': Review.objects.filter(is_active=True).count(),
            'active_promos': PromoCode.objects.filter(is_active=True).count(),
            'recent_orders': Order.objects.select_related('user').order_by('-created')[:8],
        }

        extra_context = extra_context or {}
        extra_context['stats'] = stats
        return super().index(request, extra_context)


admin_site = LadiesDreamAdminSite(name='admin')
