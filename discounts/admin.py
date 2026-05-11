from django.contrib import admin
from .models import Discount, PromoCode, PromoCodeUsage
from admin_site import admin_site

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('product', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'min_quantity')
    list_filter = ('discount_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('product__name',)
    ordering = ('-created_at',)

class PromoCodeUsageInline(admin.TabularInline):
    model = PromoCodeUsage
    extra = 0
    readonly_fields = ('user', 'order_amount', 'discount_amount', 'used_at')
    can_delete = False

class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'value', 'start_date', 'end_date', 'is_active', 'usage_limit', 'used_count')
    list_filter = ('discount_type', 'is_active', 'start_date', 'end_date')
    search_fields = ('code',)
    readonly_fields = ('used_count', 'created_at', 'created_by')
    inlines = [PromoCodeUsageInline]


class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ('promo_code', 'user', 'order_amount', 'discount_amount', 'used_at')
    list_filter = ('used_at', 'promo_code')
    search_fields = ('promo_code__code', 'user__username')
    ordering = ('-used_at',)


admin_site.register(Discount, DiscountAdmin)
admin_site.register(PromoCode, PromoCodeAdmin)
admin_site.register(PromoCodeUsage, PromoCodeUsageAdmin)
