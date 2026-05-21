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
    products = Product.objects.filter(is_available=True).select_related('category').prefetch_related('variants', 'gallery')

    category = None
    if category_slug:
        from django.shortcuts import get_object_or_404
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = products.filter(category=category)

    # Визначаємо, чи запит на повне скидання (якщо є параметр reset)
    is_reset = request.GET.get('reset') == '1'

    if is_reset:
        request.session['selected_categories'] = []
        request.session['selected_suppliers'] = []
        request.session['selected_sizes'] = []
        request.session['selected_colors'] = []
        selected_categories = []
        selected_suppliers = []
        selected_sizes = []
        selected_colors = []
    else:
        # Отримуємо фільтри з GET
        selected_categories = request.GET.getlist('category')
        selected_suppliers = request.GET.getlist('supplier')
        selected_sizes = request.GET.getlist('size')
        selected_colors = request.GET.getlist('color')

        # Флаг, що користувач активно взаємодіяв з формою фільтрів
        is_filter_interaction = request.GET.get('filter_applied') == '1'

        # Якщо в GET порожньо
        if not any([selected_categories, selected_suppliers, selected_sizes, selected_colors]):
            if is_filter_interaction:
                # Користувач вручну зняв ВСІ фільтри — очищуємо сесію
                request.session['selected_categories'] = []
                request.session['selected_suppliers'] = []
                request.session['selected_sizes'] = []
                request.session['selected_colors'] = []
            else:
                # Звичайний перехід на сторінку — відновлюємо з сесії
                selected_categories = request.session.get('selected_categories', [])
                selected_suppliers = request.session.get('selected_suppliers', [])
                selected_sizes = request.session.get('selected_sizes', [])
                selected_colors = request.session.get('selected_colors', [])
        else:
            # В GET щось є — оновлюємо сесію
            request.session['selected_categories'] = selected_categories
            request.session['selected_suppliers'] = selected_suppliers
            request.session['selected_sizes'] = selected_sizes
            request.session['selected_colors'] = selected_colors

    if selected_categories:
        products = products.filter(category__name__in=selected_categories)

    if selected_suppliers:
        products = products.filter(supplier__name__in=selected_suppliers)

    if selected_sizes:
        products = products.filter(variants__size__name__in=selected_sizes).distinct()

    if selected_colors:
        products = products.filter(variants__color__name__in=selected_colors).distinct()

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
        'category': category,
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

    if getattr(request, 'htmx', False) and request.htmx.target in ['catalog-content', 'catalog-results']:
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

    # --- Sizes & Colors stock (SINGLE SOURCE OF TRUTH: variants) ---
    all_variants = product.variants.select_related('size', 'color').all()
    
    # 1. Створюємо список розмірів (унікальні, очищені, відсортовані)
    sizes = sorted(list(set(v.size.name.strip() for v in all_variants)))
    
    # 2. Створюємо список кольорів (унікальні, очищені, зберігаємо hex)
    colors_dict = {}
    for v in all_variants:
        c_name = v.color.name.strip()
        if c_name not in colors_dict:
            colors_dict[c_name] = getattr(v.color, 'hex_code', '#ccc')
    colors = sorted([(name, hex) for name, hex in colors_dict.items()])

    # 3. Карта "Колір -> [Розміри]" та точні залишки
    sizes_with_stock = {} # для відображення в шаблоні (загальний сток на розмір)
    color_to_sizes = {}
    variant_stock_data = {}
    
    for variant in all_variants:
        s_name = variant.size.name.strip()
        c_name = variant.color.name.strip()
        
        # Загальний сток розміру
        sizes_with_stock[s_name] = sizes_with_stock.get(s_name, 0) + variant.stock
        
        # Наявність розміру для конкретного кольору
        if c_name not in color_to_sizes:
            color_to_sizes[c_name] = {}
        color_to_sizes[c_name][s_name] = variant.stock > 0
        
        # Точний залишок для JS (ключ в нижньому регістрі для надійності)
        v_key = f"{c_name}_{s_name}".lower()
        variant_stock_data[v_key] = variant.stock

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
        'color_to_sizes_json': color_to_sizes_json,
        'variant_stock_json': variant_stock_json,
        'sizes': sizes,
        'colors': colors,
        'color_images_json': color_images_json,
    }

    return render(request, 'main/product-detail.html', context)


def google_merchant_feed(request):
    import os
    from django.conf import settings
    from django.http import Http404, FileResponse
    
    feed_path = os.path.join(settings.MEDIA_ROOT, 'google_merchant_feed.xml')
    if not os.path.exists(feed_path):
        from main.tasks import generate_xml_feeds
        generate_xml_feeds.delay()
        raise Http404("Фід ще не згенеровано. Запит на генерацію надіслано, спробуйте через хвилину.")
        
    return FileResponse(open(feed_path, 'rb'), content_type='application/xml')


def robots_txt(request):
    from django.http import HttpResponse
    
    content = """User-agent: *
Disallow: /admin/
Disallow: /cart/
Disallow: /orders/
Disallow: /accounts/
Disallow: /ckeditor/
Disallow: /*?*sort=
Disallow: /*?*q=
Disallow: /*?*category=
Disallow: /*?*size=
Disallow: /*?*color=
Disallow: /*?*supplier=

Sitemap: {scheme}://{host}/sitemap.xml
""".format(
        scheme=request.scheme,
        host=request.get_host()
    )
    return HttpResponse(content, content_type="text/plain")