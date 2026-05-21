from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import AbandonedCart
from main.models import Product
from admin_site import admin_site

class AbandonedCartAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at', 'reminder_sent', 'items_count')
    list_filter = ('reminder_sent', 'updated_at')
    search_fields = ('user__username', 'user__email')
    
    fields = ('user', 'cart_contents_display', 'reminder_sent', 'updated_at')
    readonly_fields = ('user', 'cart_contents_display', 'updated_at')

    def items_count(self, obj):
        return sum(item.get('quantity', 0) for item in obj.cart_data.values())
    items_count.short_description = "Кількість товарів"

    def cart_contents_display(self, obj):
        if not obj.cart_data:
            return "Кошик порожній"
        
        product_ids = [item.get('product_id') for item in obj.cart_data.values() if item.get('product_id')]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
        
        html = [
            '<table style="width:100%; border-collapse: collapse; margin-top: 10px; border: 1px solid #e0e0e0;">',
            '<thead>',
            '<tr style="background-color: #f5f5f5; border-bottom: 2px solid #e0e0e0; text-align: left;">',
            '<th style="padding: 10px 12px; font-weight: 600;">Фото</th>',
            '<th style="padding: 10px 12px; font-weight: 600;">Товар</th>',
            '<th style="padding: 10px 12px; font-weight: 600;">Характеристики</th>',
            '<th style="padding: 10px 12px; font-weight: 600;">Ціна</th>',
            '<th style="padding: 10px 12px; font-weight: 600;">Кількість</th>',
            '<th style="padding: 10px 12px; font-weight: 600;">Сума</th>',
            '</tr>',
            '</thead>',
            '<tbody>'
        ]
        
        total_price = 0
        for item in obj.cart_data.values():
            product_id = item.get('product_id')
            product = products.get(product_id)
            if not product:
                continue
            
            qty = item.get('quantity', 0)
            price = float(item.get('price', product.price))
            subtotal = price * qty
            total_price += subtotal
            
            # Зображення
            image_html = ""
            image_url = item.get('variant_image') or (product.image.url if product.image else None)
            if image_url:
                image_html = f'<img src="{image_url}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />'
            else:
                image_html = '<span style="color: #999; font-style: italic;">Немає фото</span>'
                
            # Посилання на товар в адмінці
            admin_url = reverse('admin:main_product_change', args=[product.id])
            product_link = f'<a href="{admin_url}" style="font-weight: bold; color: #e91e63; text-decoration: none;">{product.name}</a>'
            
            # Характеристики
            attributes = []
            if item.get('color'):
                attributes.append(f'Колір: <strong>{item["color"]}</strong>')
            if item.get('size'):
                attributes.append(f'Розмір: <strong>{item["size"]}</strong>')
            attrs_str = "<br>".join(attributes) or "—"
            
            html.append(f'<tr style="border-bottom: 1px solid #e0e0e0;">')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{image_html}</td>')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{product_link}</td>')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{attrs_str}</td>')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{price:.2f} грн</td>')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{qty} шт</td>')
            html.append(f'<td style="padding: 10px 12px; vertical-align: middle;">{subtotal:.2f} грн</td>')
            html.append('</tr>')
            
        html.append('</tbody>')
        html.append('<tfoot>')
        html.append(f'<tr style="font-weight: bold; background-color: #fafafa;">')
        html.append(f'<td colspan="5" style="padding: 12px 12px; text-align: right; border-top: 2px solid #e0e0e0;">Загальна сума:</td>')
        html.append(f'<td style="padding: 12px 12px; color: #e91e63; font-size: 1.2rem; border-top: 2px solid #e0e0e0;">{total_price:.2f} грн</td>')
        html.append('</tr>')
        html.append('</tfoot>')
        html.append('</table>')
        
        return format_html("".join(html))
    
    cart_contents_display.short_description = "Вміст кошика"

admin_site.register(AbandonedCart, AbandonedCartAdmin)
