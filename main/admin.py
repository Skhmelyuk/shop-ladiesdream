from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, Color, Size, ProductVariant, ProductImage, Supplier
from admin_site import admin_site

# ========== PRODUCT IMAGE ADMIN ==========
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image", "order")
    list_editable = ("order",)

# Inline для ProductImage
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ("image", "color", "order")

# Inline для ProductVariant
class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ("size", "color", "stock")
    autocomplete_fields = ("size", "color")

# ========== COLOR ADMIN ==========
class ColorAdmin(admin.ModelAdmin):
    list_display = ("name", "hex_color_display", "in_stock")
    list_editable = ("in_stock",)
    search_fields = ("name",)
    fields = ("name", "hex_code", "in_stock")

    def formfield_for_dbfield(self, db_field, **kwargs):
        """Enable color-picker for hex field in color admin."""
        formfield = super().formfield_for_dbfield(db_field, **kwargs)
        if db_field.name == "hex_code":
            formfield.widget.input_type = "color"
        return formfield

    def hex_color_display(self, obj):
        return format_html(
            '<div style="width:25px; height:25px; border-radius:50%; background:{}; border:1px solid #999;"></div>',
            obj.hex_code,
        )
    hex_color_display.short_description = "Колір"

# ========== SIZE ADMIN ==========
class SizeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

# ========== CATEGORY ADMIN ==========
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    list_filter = ("is_active",)
    search_fields = ("name",)

# ========== PRODUCT ADMIN ==========
class ProductAdmin(admin.ModelAdmin):
    list_display = ("image_preview", "name", "price", "category", "supplier", "discount_percent", "show_colors", "total_stock", "created_at")
    list_filter = ("category", "supplier", "created_at",)
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVariantInline]
    filter_horizontal = ("colors", "sizes")
    autocomplete_fields = ("supplier",)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("variants__color", "colors")

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width:48px;height:48px;object-fit:cover;border-radius:6px;border:1px solid #f8bbd0;">', obj.image.url)
        return format_html('<span style="color:#ccc;font-size:1.3rem;">📷</span>')
    image_preview.short_description = ''

    def total_stock(self, obj):
        total = sum(v.stock for v in obj.variants.all())
        if total == 0:
            color = "#e53935"
        elif total < 5:
            color = "#f57c00"
        else:
            color = "#2e7d32"
        return format_html(
            '<span style="font-weight:700; color:{};">{}</span>',
            color, total
        )
    total_stock.short_description = "Залишок"
    total_stock.admin_order_field = None

    def show_colors(self, obj):
        """Кольори з варіантів: кружечок + кількість у tooltip, сірий = закінчився."""
        from collections import defaultdict
        stock_by_color = defaultdict(int)
        color_obj = {}
        for v in obj.variants.all():
            if v.color:
                stock_by_color[v.color.id] += v.stock
                color_obj[v.color.id] = v.color
        if not color_obj:
            return "—"
        parts = []
        for color_id, color in color_obj.items():
            qty = stock_by_color[color_id]
            if qty > 0:
                style = (
                    f"display:inline-flex;align-items:center;justify-content:center;"
                    f"width:22px;height:22px;border-radius:50%;"
                    f"background:{color.hex_code};border:2px solid #555;"
                    f"font-size:9px;font-weight:700;color:#fff;"
                    f"text-shadow:0 0 2px #000;margin-right:3px;cursor:default;"
                )
                title = f"{color.name}: {qty} шт"
            else:
                style = (
                    f"display:inline-flex;align-items:center;justify-content:center;"
                    f"width:22px;height:22px;border-radius:50%;"
                    f"background:#ccc;border:2px solid #999;"
                    f"font-size:9px;font-weight:700;color:#888;"
                    f"margin-right:3px;cursor:default;opacity:0.5;"
                    f"text-decoration:line-through;"
                )
                title = f"{color.name}: немає"
            parts.append(
                f'<span style="{style}" title="{title}">{qty if qty > 0 else "✕"}</span>'
            )
        return format_html(" ".join(parts))
    show_colors.short_description = "Кольори / залишок"

# ========== PRODUCT VARIANT ADMIN ==========
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ("product", "size", "color_circle", "stock")
    list_filter = ("product", "size", "color")
    search_fields = ("product__name",)

    def color_circle(self, obj):
        return format_html(
            '<span style="display:inline-block; width:18px; height:18px; border-radius:50%; '
            'background:{}; border:1px solid #444;"></span>',
            obj.color.hex_code,
        )
    color_circle.short_description = "Колір"

# ========== SUPPLIER ADMIN ==========
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'product_count')
    search_fields = ('name',)

    def product_count(self, obj):
        return obj.product_set.count()
    product_count.short_description = 'Товарів'

# ========== РЕЄСТРАЦІЯ ==========
admin_site.register(ProductImage, ProductImageAdmin)
admin_site.register(Color, ColorAdmin)
admin_site.register(Size, SizeAdmin)
admin_site.register(Category, CategoryAdmin)
admin_site.register(Product, ProductAdmin)
admin_site.register(ProductVariant, ProductVariantAdmin)
admin_site.register(Supplier, SupplierAdmin)
