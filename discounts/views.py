from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import PromoCode
from main.models import Product
from .models import Discount, PromoCode, PromoCodeUsage
from .forms import DiscountForm, PromoCodeForm, ApplyPromoCodeForm

@staff_member_required
def add_discount(request, product_id):
    """Додавання знижки до товару"""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = DiscountForm(request.POST)
        if form.is_valid():
            discount = form.save(commit=False)
            discount.product = product
            discount.save()
            messages.success(request, f"✅ Знижку для «{product.name}» успішно створено!")
            return redirect('discounts:product_discounts', product_id=product.id)
        else:
            messages.error(request, "⚠️ Перевірте правильність заповнення форми.")
    else:
        form = DiscountForm()

    return render(request, 'discounts/add_discount.html', {'form': form, 'product': product})


@staff_member_required
def product_discounts(request, product_id):
    """Список активних знижок для товару"""
    product = get_object_or_404(Product, id=product_id)
    discounts = product.discounts.all().order_by('-created_at')

    context = {
        'product': product,
        'discounts': discounts,
    }
    return render(request, 'discounts/product_discounts.html', context)


@staff_member_required
def edit_discount(request, discount_id):
    """Редагування існуючої знижки"""
    discount = get_object_or_404(Discount, id=discount_id)
    product = discount.product

    if request.method == 'POST':
        form = DiscountForm(request.POST, instance=discount)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Знижку успішно оновлено!")
            return redirect('discounts:product_discounts', product_id=product.id)
    else:
        form = DiscountForm(instance=discount)

    return render(request, 'discounts/add_discount.html', {'form': form, 'product': product})


@staff_member_required
def delete_discount(request, discount_id):
    """Видалення знижки"""
    discount = get_object_or_404(Discount, id=discount_id)
    product_id = discount.product.id
    discount.delete()
    messages.success(request, "🗑️ Знижку видалено.")
    return redirect('discounts:product_discounts', product_id=product_id)


@staff_member_required
def create_promo_code(request):
    """Створення нового промокоду"""
    if request.method == 'POST':
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            promo = form.save(commit=False)
            promo.created_by = request.user
            promo.save()
            messages.success(request, f"🎁 Промокод «{promo.code}» успішно створено!")
            return redirect('discounts:promo_code_list')
        else:
            messages.error(request, "⚠️ Перевірте правильність введених даних.")
    else:
        form = PromoCodeForm()

    return render(request, 'discounts/promo_code_form.html', {'form': form})


@staff_member_required
def promo_code_list(request):
    """Список промокодів"""
    promo_codes = PromoCode.objects.all().order_by('-created_at')

    query = request.GET.get('q')
    if query:
        promo_codes = promo_codes.filter(code__icontains=query)

    filter_status = request.GET.get('status')
    if filter_status == 'active':
        promo_codes = promo_codes.filter(is_active=True)
    elif filter_status == 'inactive':
        promo_codes = promo_codes.filter(is_active=False)

    context = {
        'promo_codes': promo_codes,
    }
    return render(request, 'discounts/promo_code_list.html', context)


@login_required
def apply_promo_code(request):
    """Застосування промокоду"""
    if request.method == 'POST':
        form = ApplyPromoCodeForm(request.POST)
        if form.is_valid():
            code = form.cleaned_data['promo_code']
            try:
                promo = PromoCode.objects.get(code=code)
            except PromoCode.DoesNotExist:
                messages.error(request, "❌ Промокод не знайдено.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            if not promo.is_valid():
                messages.error(request, "⏰ Цей промокод більше не дійсний.")
                return redirect(request.META.get('HTTP_REFERER', '/'))

            request.session['promo_code'] = promo.code
            messages.success(request, f"✅ Промокод «{promo.code}» застосовано!")
            return redirect(request.META.get('HTTP_REFERER', '/'))
        else:
            messages.error(request, "⚠️ Перевірте правильність введення коду.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def remove_promo_code(request):
    """Видалення промокоду з сесії"""
    if 'promo_code' in request.session:
        del request.session['promo_code']
        messages.info(request, "🎀 Промокод видалено.")
    return redirect(request.META.get('HTTP_REFERER', '/'))


@staff_member_required
def promo_code_stats(request, code_id):
    """Статистика використання промокоду"""
    promo = get_object_or_404(PromoCode, id=code_id)
    usages = PromoCodeUsage.objects.filter(promo_code=promo)

    total_discount = sum(u.discount_amount for u in usages)
    total_orders = len(usages)

    context = {
        'promo': promo,
        'usages': usages,
        'total_discount': total_discount,
        'total_orders': total_orders,
    }
    return render(request, 'discounts/promo_code_stats.html', context)

def apply_promo_code(request):
    if request.method == 'POST':
        code = request.POST.get('promo_code', '').strip()

        if code:
            try:
                promo = PromoCode.objects.get(code__iexact=code, is_active=True)
                request.session['promo_discount'] = float(promo.value)
                request.session['promo_code'] = promo.code

                messages.success(request, f'Промокод "{promo.code}" застосовано! Знижка {promo.value}%')

            except PromoCode.DoesNotExist:
                request.session.pop('promo_discount', None)
                request.session.pop('promo_code', None)
                messages.error(request, 'Невірний промокод або він не активний.')

        else:
            messages.error(request, 'Будь ласка, введіть промокод.')

    return redirect('orders:order_create')