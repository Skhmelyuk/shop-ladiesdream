from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import TemplateView
from django.contrib import messages
from main.models import Product, ProductImage, ProductVariant
from .cart import Cart
from .wishlist import Wishlist
from .forms import CartAddProductForm, CartRemoveProductForm
import json

class CartAddView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        product = get_object_or_404(Product, id=product_id)
        msg = "Помилка при оновленні кошика"
        form = CartAddProductForm(request.POST)
        
        if form.is_valid():
            cleaned_data = form.cleaned_data
            quantity = cleaned_data['quantity']
            override_quantity = cleaned_data['override']
            final_price = product.get_current_price()

            # Отримуємо колір та розмір (підтримка обох імен полів)
            selected_color = (request.POST.get('color') or request.POST.get('selected_color') or '').strip()
            selected_size = (request.POST.get('size') or request.POST.get('selected_size') or '').strip()
            
            # Якщо параметрів немає (оновлення з кошика), шукаємо існуючий запис
            if not selected_color and not selected_size:
                for cart_key, cart_item in cart.cart.items():
                    if cart_key.startswith(f"{product.id}_") and 'product_id' in cart_item:
                        selected_color = cart_item.get('color', '').strip()
                        selected_size = cart_item.get('size', '').strip()
                        break
            
            # Знаходимо конкретний варіант товару та його stock
            variant_stock = 0
            variant_query = ProductVariant.objects.filter(product=product)
            
            if selected_color:
                variant_query = variant_query.filter(color__name__iexact=selected_color)
            else:
                if product.variants.filter(color__isnull=False).exists():
                    variant_query = variant_query.filter(color__isnull=True)
                
            if selected_size:
                variant_query = variant_query.filter(size__name__iexact=selected_size)
                
            variant = variant_query.first()
            if variant:
                variant_stock = variant.stock
            else:
                if not selected_color or not selected_size:
                    variant_stock = sum(v.stock for v in variant_query)
                else:
                    variant_stock = 0

            # Знаходимо фото
            variant_image = ''
            if selected_color:
                color_images = ProductImage.objects.filter(product=product, color__name__iexact=selected_color).order_by('order').first()
                variant_image = color_images.image.url if color_images else (product.image.url if product.image else '')
            elif product.image:
                variant_image = product.image.url

            # Створюємо ключ для пошуку в кошику
            color_key = selected_color.lower().replace(' ', '_') if selected_color else 'no_color'
            size_key = selected_size.upper().replace(' ', '_') if selected_size else 'no_size'
            cart_key = f"{product.id}_{color_key}_{size_key}"
            
            current_in_cart = cart.cart.get(cart_key, {}).get('quantity', 0)
            new_qty = quantity if override_quantity else (current_in_cart + quantity)

            # Серверна валідація кількості
            if new_qty > variant_stock:
                if variant_stock <= 0:
                    quantity = 0
                    override_quantity = True
                    msg = 'Товар закінчився'
                    messages.error(request, msg)
                else:
                    limit = variant_stock if override_quantity else (variant_stock - current_in_cart)
                    quantity = max(0, limit)
                    msg = f'Доступно лише {variant_stock} шт.'
                    messages.warning(request, msg)
            else:
                msg = 'Кошик оновлено'

            # Завжди викликаємо cart.add, щоб синхронізувати стан
            cart.add(
                product=product,
                quantity=quantity,
                override_quantity=override_quantity,
                price=final_price,
                color=selected_color,
                size=selected_size,
                variant_image=variant_image,
                variant_id=variant.id if variant else None
            )
        else:
            # Помилки форми
            msg = "Некоректні дані"
            if form.errors:
                msg = list(form.errors.values())[0][0]
            messages.error(request, msg)

        if getattr(request, 'htmx', False):
            if '/cart/' in request.META.get('HTTP_HX_CURRENT_URL', ''):
                response = render(request, 'cart/partials/cart_content.html', {'cart': cart})
            else:
                response = render(request, 'cart/partials/cart_badge.html', {'cart': cart})
            
            # Визначаємо тип тосту на основі останнього повідомлення
            toast_type = "success"
            storage = messages.get_messages(request)
            for message in storage:
                msg = str(message)
                if message.level == messages.ERROR: toast_type = "error"
                elif message.level == messages.WARNING: toast_type = "warning"
            
            response["HX-Trigger"] = json.dumps({"showToast": {"message": msg, "type": toast_type}})
            return response
        
        return redirect('cart:cart_detail')

class CartRemoveView(View):
    def post(self, request, product_id):
        cart = Cart(request)
        color = request.POST.get('color', '')
        size = request.POST.get('size', '')
        
        color_key = color.lower().replace(' ', '_') if color else 'no_color'
        size_key = size.upper().replace(' ', '_') if size else 'no_size'
        cart_key = f"{product_id}_{color_key}_{size_key}"
        
        cart.remove_by_key(cart_key)
        
        if getattr(request, 'htmx', False):
            response = render(request, 'cart/partials/cart_content.html', {'cart': cart})
            msg = "Товар видалено з кошика"
            response["HX-Trigger"] = json.dumps({"showToast": {"message": msg, "type": "info"}})
            return response
            
        return redirect('cart:cart_detail')

class CartDetailView(TemplateView):
    template_name = 'cart/detail.html'

    def get(self, request, *args, **kwargs):
        cart = Cart(request)
        if cart.validate():
            messages.info(request, "Деякі товари в кошику були оновлені відповідно до наявності на складі.")
      
        for item in cart:
            item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True})
            item['remove_form'] = CartRemoveProductForm()
      
        if getattr(request, 'htmx', False) and request.htmx.target == 'cart-container':
            return render(request, 'cart/partials/cart_content.html', {'cart': cart})
            
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cart'] = Cart(self.request)
        return context

class WishlistToggleView(View):
    def post(self, request, product_id):
        wishlist = Wishlist(request)
        product = get_object_or_404(Product, id=product_id)
        added = wishlist.toggle(product)
        
        if getattr(request, 'htmx', False):
            response = render(request, 'wishlist/partials/wishlist_button.html', {
                'product': product,
                'in_wishlist': added
            })
            msg = "Додано до списку бажань" if added else "Видалено зі списку бажань"
            response["HX-Trigger"] = json.dumps({"showToast": {"message": msg, "type": "success" if added else "info"}})
            return response
        return redirect('cart:wishlist_detail')

class WishlistDetailView(TemplateView):
    template_name = 'wishlist/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['wishlist'] = Wishlist(self.request)
        return context