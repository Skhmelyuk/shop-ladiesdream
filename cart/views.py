from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.contrib import messages
from main.models import Product, ProductImage
from .cart import Cart
from .wishlist import Wishlist
from .forms import CartAddProductForm, CartRemoveProductForm
from decimal import Decimal



@require_POST
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        quantity = cleaned_data['quantity']
        override_quantity = cleaned_data['override']
        final_price = product.get_current_price()

        # Отримуємо колір та розмір з форми
        selected_color = request.POST.get('selected_color', '')
        selected_size = request.POST.get('selected_size', '')
        
        # Для оновлення кошика може не бути selected_color/selected_size
        # Спробуємо отримати їх з поточного запису кошика
        if not selected_color and not selected_size:
            # Шукаємо існуючий запис в кошику для цього товару
            for cart_key, cart_item in cart.cart.items():
                if cart_key.startswith(f"{product.id}_") and 'product_id' in cart_item:
                    selected_color = cart_item.get('color', '')
                    selected_size = cart_item.get('size', '')
                    break
        
        # Знаходимо конкретний варіант товару та його stock
        variant_stock = 0
        if selected_color and selected_size:
            try:
                from main.models import ProductVariant, Size, Color
                variant = ProductVariant.objects.get(
                    product=product,
                    color__name=selected_color,
                    size__name=selected_size
                )
                variant_stock = variant.stock
            except ProductVariant.DoesNotExist:
                variant_stock = 0
        else:
            # Якщо немає кольору/розміру, беремо загальний stock
            variant_stock = sum(v.stock for v in product.variants.all())
        
        # Знаходимо фото для вибраного кольору
        variant_image = ''
        if selected_color:
            color_images = ProductImage.objects.filter(
                product=product, 
                color__name=selected_color
            ).order_by('order').first()
            if color_images:
                variant_image = color_images.image.url
            elif product.image:
                variant_image = product.image.url
        elif product.image:
            variant_image = product.image.url

        # Створюємо ключ для пошуку в кошику
        color_key = selected_color.lower().replace(' ', '_') if selected_color else 'no_color'
        size_key = selected_size.upper().replace(' ', '_') if selected_size else 'no_size'
        cart_key = f"{product.id}_{color_key}_{size_key}"
        
        current_in_cart = cart.cart.get(cart_key, {}).get('quantity', 0)
        if override_quantity:
            new_qty = quantity
        else:
            new_qty = current_in_cart + quantity

        # Серверна валідація кількості
        if variant_stock > 0 and new_qty > variant_stock:
            messages.warning(
                request,
                f'Максимально доступно {variant_stock} шт. товару "{product.name}" ({selected_color} {selected_size}).'
            )
            quantity = max(1, variant_stock - current_in_cart) if not override_quantity else variant_stock
            if quantity <= 0:
                return redirect('cart:cart_detail')

        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=override_quantity,
            price=final_price,
            color=selected_color,
            size=selected_size,
            variant_image=variant_image
        )
        messages.success(request, f'Кількість товару "{product.name}" оновлено')

    if getattr(request, 'htmx', False) and '/cart/' not in request.META.get('HTTP_HX_CURRENT_URL', ''):
        return render(request, 'cart/partials/cart_badge.html', {'cart': cart})
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    """
    Видаляє конкретний варіант товару з кошика. Вимагає POST-запиту.
    """
    cart = Cart(request)
    
    # Отримуємо колір та розмір з POST для визначення конкретного варіанту
    color = request.POST.get('color', '')
    size = request.POST.get('size', '')
    
    # Створюємо ключ для видалення
    color_key = color.lower().replace(' ', '_') if color else 'no_color'
    size_key = size.upper().replace(' ', '_') if size else 'no_size'
    cart_key = f"{product_id}_{color_key}_{size_key}"
    
    cart.remove_by_key(cart_key)
    return redirect('cart:cart_detail')


def cart_detail(request):
    """
    Відображає вміст кошика.
    """
    cart = Cart(request)
  
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(initial={'quantity': item['quantity'], 'override': True})
        item['remove_form'] = CartRemoveProductForm()
        
        # Отримуємо доступний stock для варіанту
        item_color = item.get('color', '')
        item_size = item.get('size', '')
        
        if item_color and item_size:
            try:
                from main.models import ProductVariant
                variant = ProductVariant.objects.get(
                    product=item['product'],
                    color__name=item_color,
                    size__name=item_size
                )
                item['available_stock'] = variant.stock
                item['max_quantity'] = variant.stock
            except ProductVariant.DoesNotExist:
                item['available_stock'] = 0
                item['max_quantity'] = 0
        else:
            # Якщо немає кольору/розміру, беремо загальний stock
            total_stock = sum(v.stock for v in item['product'].variants.all())
            item['available_stock'] = total_stock
            item['max_quantity'] = total_stock
  
    if getattr(request, 'htmx', False):
        return render(request, 'cart/partials/cart_content.html', {'cart': cart})
    return render(request, 'cart/detail.html', {'cart': cart})

@require_POST
def wishlist_toggle(request, product_id):
    wishlist = Wishlist(request)
    product = get_object_or_404(Product, id=product_id)
    added = wishlist.toggle(product)
    
    # Якщо запит від HTMX, повертаємо тільки кнопку і бейдж OOB
    if getattr(request, 'htmx', False):
        return render(request, 'wishlist/partials/wishlist_button.html', {
            'product': product,
            'in_wishlist': added
        })
    return redirect('cart:wishlist_detail')

def wishlist_detail(request):
    wishlist = Wishlist(request)
    return render(request, 'wishlist/detail.html', {'wishlist': wishlist})