from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import F, Q, Avg
from .models import Product, Category, Supplier
from django.core.paginator import Paginator
from reviews.forms import ReviewForm
from cart.forms import CartAddProductForm
from django.contrib import messages
from django.db.models import Count
from discounts.models import Discount
from django.utils import timezone
from decimal import Decimal
import json
import random



def about_view(request):
    """Сторінка 'Про нас'."""
    return render(request, 'main/about.html')

def contact_view(request):
    """Сторінка 'Контакти'."""
    return render(request, 'main/contact.html')



def product_list(request, category_slug=None):
    categories = Category.objects.filter(is_active=True).order_by('name')
    products = Product.objects.filter(is_available=True)

    # --- Мультивибір ---
    selected_categories = request.GET.getlist('category')
    selected_suppliers  = request.GET.getlist('supplier')

    if selected_categories:
        products = products.filter(category__name__in=selected_categories)

    if selected_suppliers:
        products = products.filter(supplier__name__in=selected_suppliers)

    search_query = request.GET.get('q')
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(category__name__icontains=search_query)
        ).distinct()

    sort_by = request.GET.get('sort', 'new')
    if sort_by == 'price_asc':
        products = products.order_by('price')
    elif sort_by == 'price_desc':
        products = products.order_by('-price')
    elif sort_by == 'views':
        products = products.order_by('-views')
    elif sort_by == 'old':
        products = products.order_by('created_at')
    else:
        products = products.order_by('-created_at')

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    products_on_page = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'products': products_on_page,
        'page_obj': products_on_page,
        'paginator': paginator,
        'suppliers': Supplier.objects.all(),
        'selected_categories': selected_categories,
        'selected_suppliers': selected_suppliers,
        # зворотна сумісність для chip-блоку
        'selected_category': ', '.join(selected_categories) if selected_categories else '',
        'selected_supplier': ', '.join(selected_suppliers) if selected_suppliers else '',
    }

    if getattr(request, 'htmx', False):
        return render(request, 'main/partials/product_grid.html', context)
    return render(request, 'main/product-list.html', context)

def product_detail(request, id, slug):
    product = get_object_or_404(
        Product.objects.prefetch_related(
            'colors',
            'variants__size',
            'variants__color',
            'gallery__color',
            'reviews__author',
        ),
        id=id, slug=slug, is_available=True
    )

    # --- Colors with style ---
    colors_with_style = []
    for color in product.colors.all():
        hex_code = getattr(color, 'hex_code', None) or '#ccc'
        if not hex_code.startswith("#"):
            hex_code = f"#{hex_code}"
        colors_with_style.append({
            'name': getattr(color, 'name', 'Unknown'),
            'in_stock': getattr(color, 'in_stock', False),
            'color_style': hex_code,
        })

    # --- Reviews ---
    reviews = product.reviews.select_related('author').filter(is_active=True)
    average_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0

    # --- Discount --- використовуємо готовий метод моделі як єдине джерело правди
    active_discount = Discount.objects.filter(
        product=product,
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
    ).first()

    base_price = Decimal(str(product.price))
    final_price = Decimal(str(product.get_current_price()))
    is_on_sale = final_price < base_price

    # --- Sizes & Colors stock ---
    sizes = list(product.variants.values_list("size__name", flat=True).distinct())
    colors = list(product.variants.values_list("color__name", "color__hex_code").distinct())

    sizes_with_stock = {}
    colors_with_stock = {}
    color_to_sizes = {}
    variant_stock_data = {}
    for variant in product.variants.all():
        size_name = variant.size.name
        color_name = variant.color.name
        
        sizes_with_stock[size_name] = sizes_with_stock.get(size_name, 0) + variant.stock
        key = (variant.size.name, variant.color.name)
        colors_with_stock[key] = variant.stock > 0
        
        if color_name not in color_to_sizes:
            color_to_sizes[color_name] = {}
        color_to_sizes[color_name][size_name] = variant.stock > 0
        
        # Зберігаємо точну кількість для кожного варіанту
        variant_key = f"{color_name}_{size_name}"
        variant_stock_data[variant_key] = variant.stock

    # --- Handle Review Form ---
    if request.method == 'POST' and request.user.is_authenticated:
        form = ReviewForm(request.POST)
        if form.is_valid():
            new_review = form.save(commit=False)
            new_review.product = product
            new_review.author = request.user
            new_review.is_active = True
            try:
                new_review.save()
                messages.success(request, "Ваш відгук успішно додано!")
            except Exception:
                messages.error(request, "Ви вже залишили відгук на цей товар. Можна залишити лише один.")
            return redirect('main:product-detail', id=product.id, slug=slug)
    else:
        form = ReviewForm()

    cart_product_form = CartAddProductForm()

    # --- Color images map ---
    color_images = {}
    for img in product.gallery.all().select_related('color'):
        key = img.color.name if img.color else '__all__'
        color_images.setdefault(key, []).append(img.image.url)
    color_images_json = json.dumps(color_images, ensure_ascii=False)
    
    # --- Color to sizes map for JavaScript ---
    color_to_sizes_json = json.dumps(color_to_sizes, ensure_ascii=False)
    
    # --- Variant stock data for JavaScript ---
    variant_stock_json = json.dumps(variant_stock_data, ensure_ascii=False)

    # --- Increase views ---
    product.views = F('views') + 1
    product.save(update_fields=['views'])

    # --- Related products (random.sample ефективніше ніж ORDER BY RANDOM()) ---
    related_ids = list(
        Product.objects.filter(category=product.category, is_available=True)
        .exclude(id=product.id)
        .values_list('id', flat=True)
    )
    sample_ids = random.sample(related_ids, min(4, len(related_ids)))
    related_products = Product.objects.filter(id__in=sample_ids)

    # Додаємо розраховані значення для прогрес-барів відгуків
    reviews_with_width = []
    for review in reviews:
        reviews_with_width.append({
            'review': review,
            'rating_width': review.rating * 20,
            'admin_replies': review.admin_replies.filter(is_active=True),
        })

    context = {
        'product': product,
        'colors_with_style': colors_with_style,
        'related_products': related_products,
        'reviews': reviews,
        'reviews_with_width': reviews_with_width,
        'average_rating': average_rating,
        'form': form,
        'cart_product_form': cart_product_form,
        'active_discount': active_discount,
        'base_price': base_price,
        'final_price': final_price,
        'is_on_sale': is_on_sale,
        'sizes_with_stock': sizes_with_stock,
        'colors_with_stock': colors_with_stock,
        'color_to_sizes_json': color_to_sizes_json,
        'variant_stock_json': variant_stock_json,
        'sizes': sizes,
        'colors': colors,
        'color_images_json': color_images_json,
    }

    return render(request, 'main/product-detail.html', context)