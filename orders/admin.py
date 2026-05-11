from django.contrib import admin
from django.http import HttpResponse
from django.utils.html import format_html
from .models import Order, OrderItem
from admin_site import admin_site
import csv
import datetime


def export_to_csv(modeladmin, request, queryset):
    """Експортує вибрані замовлення у формат CSV."""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename=orders_{datetime.date.today()}.csv'
    writer = csv.writer(response)
    writer.writerow(['ID', "Ім'я", 'Прізвище', 'Email', 'Телефон', 'Місто', 'Статус', 'Оплачено', 'Сума', 'Дата'])
    for obj in queryset:
        writer.writerow([
            obj.id, obj.first_name, obj.last_name, obj.email,
            obj.phone, obj.city, obj.get_status_display(),
            'Так' if obj.paid else 'Ні',
            obj.get_total_cost(), obj.created.strftime('%d.%m.%Y %H:%M'),
        ])
    return response

export_to_csv.short_description = 'Експортувати у CSV'


def mark_status_processing(modeladmin, request, queryset):
    queryset.update(status='processing')
mark_status_processing.short_description = '⚙️ Статус: В обробці'

def mark_status_shipped(modeladmin, request, queryset):
    queryset.update(status='shipped')
mark_status_shipped.short_description = '📦 Статус: Відправлено'

def mark_status_delivered(modeladmin, request, queryset):
    queryset.update(status='delivered')
mark_status_delivered.short_description = '✅ Статус: Доставлено'

def mark_status_cancelled(modeladmin, request, queryset):
    queryset.update(status='cancelled')
mark_status_cancelled.short_description = '❌ Статус: Скасовано'

def mark_paid(modeladmin, request, queryset):
    queryset.update(paid=True)
mark_paid.short_description = '💳 Позначити як оплачено'

def mark_unpaid(modeladmin, request, queryset):
    queryset.update(paid=False)
mark_unpaid.short_description = '🔴 Скасувати оплату'


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    fields = ['product', 'price', 'quantity', 'get_cost']
    readonly_fields = ['price', 'get_cost']
    extra = 0

    def get_cost(self, obj):
        return f'{obj.get_cost():.2f} грн'
    get_cost.short_description = 'Вартість'


class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'first_name',
        'last_name',
        'phone',
        'city',
        'delivery_badge',
        'status_badge',
        'paid_badge',
        'get_total_cost_display',
        'created',
    ]
    list_filter = ['status', 'paid', 'delivery_type', 'payment_method', 'created']
    search_fields = ['first_name', 'last_name', 'email', 'phone', 'promo_code', 'city']
    inlines = [OrderItemInline]
    actions = [
        export_to_csv,
        mark_paid, mark_unpaid,
        mark_status_processing, mark_status_shipped,
        mark_status_delivered, mark_status_cancelled,
    ]
    fieldsets = (
        ("Інформація про клієнта", {
            'fields': ('user', 'first_name', 'last_name', 'email', 'phone')
        }),
        ("Доставка", {
            'fields': ('delivery_type', 'city', 'delivery_address')
        }),
        ("Оплата і знижка", {
            'fields': ('payment_method', 'paid', 'promo_code', 'discounted_amount', 'final_price', 'get_total_cost_display')
        }),
        ("Статус і дати", {
            'fields': ('status', 'created', 'updated', 'get_base_cost_display'),
        }),
    )
    readonly_fields = ['user', 'created', 'updated', 'get_total_cost_display', 'get_base_cost_display']

    def paid_badge(self, obj):
        if obj.paid:
            return format_html('<span style="background:#e8f5e9;color:#2e7d32;padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:700;">✓ Оплачено</span>')
        return format_html('<span style="background:#fce4ec;color:#c2185b;padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:700;">✗ Не оплачено</span>')
    paid_badge.short_description = 'Оплата'
    paid_badge.admin_order_field = 'paid'

    STATUS_COLORS = {
        'new':        ('#e3f2fd', '#1565c0'),
        'processing': ('#fff8e1', '#f57f17'),
        'shipped':    ('#e8eaf6', '#283593'),
        'delivered':  ('#e8f5e9', '#2e7d32'),
        'cancelled':  ('#ffebee', '#b71c1c'),
    }

    def status_badge(self, obj):
        bg, color = self.STATUS_COLORS.get(obj.status, ('#f5f5f5', '#555'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 10px;border-radius:20px;font-size:0.8rem;font-weight:700;">{}</span>',
            bg, color, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'
    status_badge.admin_order_field = 'status'

    DELIVERY_LABELS = {
        'NP': ('📦', '#e3f2fd', '#1565c0'),
        'UP': ('✉️', '#f3e5f5', '#6a1b9a'),
        'COURIER': ('🚚', '#e8f5e9', '#2e7d32'),
        'PICKUP': ('🏪', '#fff8e1', '#e65100'),
    }

    def delivery_badge(self, obj):
        icon, bg, color = self.DELIVERY_LABELS.get(obj.delivery_type, ('📦', '#f5f5f5', '#555'))
        return format_html(
            '<span style="background:{};color:{};padding:3px 8px;border-radius:20px;font-size:0.8rem;">{} {}</span>',
            bg, color, icon, obj.get_delivery_type_display()
        )
    delivery_badge.short_description = 'Доставка'
    delivery_badge.admin_order_field = 'delivery_type'

    def get_base_cost_display(self, obj):
        """Відображає загальну вартість до знижки."""
        return f'{obj.get_total_cost():.2f} грн'
    get_base_cost_display.short_description = 'Базова вартість'

    def get_total_cost_display(self, obj):
        """Відображає фінальну вартість після знижки."""
        return format_html('<strong style="color:#e91e63;">{} грн</strong>', f'{obj.get_total_cost():.2f}')
    get_total_cost_display.short_description = 'Сума'
    get_total_cost_display.admin_order_field = 'final_price'


admin_site.register(Order, OrderAdmin)