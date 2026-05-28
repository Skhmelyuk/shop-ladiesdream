from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.db import transaction
from django.views.decorators.csrf import csrf_exempt  # потрібен лише для payment_callback (LiqPay webhook)
from discounts.models import PromoCode
from discounts.forms import PromoCodeForm
from .models import Order, OrderItem
from .forms import OrderCreateForm
from cart.cart import Cart
from django.http import HttpResponse
from .liqpay import liqpay_client
import base64
import json
from .utils import get_user_discount_stats
from decimal import Decimal
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import logging
logger = logging.getLogger(__name__)


NP_BASE_URL = 'https://api.novaposhta.ua/v2.0/json/'

@login_required
@require_http_methods(["POST"])
def novaposhta_proxy(request):
    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    called_method = body.get("calledMethod")
    props = body.get("methodProperties", {})

    from .models import NPCity, NPWarehouse

    if called_method == "searchSettlements":
        city_name = props.get("CityName", "")
        limit = props.get("Limit", 8)
        cities = NPCity.objects.filter(name__icontains=city_name)[:limit]
        
        addresses = []
        for c in cities:
            addresses.append({
                "MainDescription": c.name,
                "Area": c.area,
                "Ref": c.ref,
                "SettlementRef": c.ref
            })
            
        return JsonResponse({
            "success": True, 
            "data": [{"Addresses": addresses}] if addresses else []
        })

    elif called_method == "getWarehouses":
        settlement_ref = props.get("SettlementRef", "")
        limit = props.get("Limit", 200)
        warehouses = NPWarehouse.objects.filter(city__ref=settlement_ref)[:limit]
        
        data = []
        for w in warehouses:
            data.append({
                "Ref": w.ref,
                "Description": w.name,
                "Number": w.number,
                "CityRef": settlement_ref
            })
            
        return JsonResponse({"success": True, "data": data})

    # Фолбек на реальне API, якщо викликається щось інше
    payload = {
        "apiKey": settings.NOVAPOSHTA_API_KEY,
        "modelName": body.get("modelName"),
        "calledMethod": called_method,
        "methodProperties": props
    }

    response = requests.post(
        "https://api.novaposhta.ua/v2.0/json/",
        json=payload
    )

    return JsonResponse(response.json(), safe=False)

def order_create(request):
    cart = Cart(request)
    
    if not cart:
        return redirect('main:product-list')
    
    cart_total = cart.get_total_price()
    discount_amount = Decimal(request.session.get('promo_discount', 0))
    promo_code_str = request.session.get('promo_code', '')
    total_price_before_promo = cart_total
    total_price_after_discount = max(total_price_before_promo - discount_amount, 0)

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        
        if form.is_valid():
            from django.db import transaction
            
            with transaction.atomic():
                order = form.save(commit=False)
                
                if request.user.is_authenticated:
                    order.user = request.user

                # Зберігаємо дані промокоду та знижки
                order.promo_code = promo_code_str
                order.discounted_amount = discount_amount
                order.final_price = total_price_after_discount
                    
                order.save()

                # Створення OrderItem
                from main.models import ProductVariant
                for item in cart:
                    variant_id = item.get('variant_id')
                    variant = None
                    if variant_id:
                        # select_for_update() блокує рядок для інших транзакцій до завершення поточної
                        variant = ProductVariant.objects.select_for_update().filter(id=variant_id).first()
                    else:
                        item_color = item.get('color', '')
                        item_size = item.get('size', '')
                        v_query = ProductVariant.objects.select_for_update().filter(product=item['product'])
                        if item_color: v_query = v_query.filter(color__name__iexact=item_color)
                        if item_size: v_query = v_query.filter(size__name__iexact=item_size)
                        variant = v_query.first()

                    OrderItem.objects.create(
                        order=order,
                        product=item['product'],
                        price=item['price'],
                        quantity=item['quantity'],
                        variant=variant
                    )

                    # Зменшення кількості на складі
                    if variant:
                        variant.stock = max(0, variant.stock - item['quantity'])
                        variant.save()

            # Відправка email асинхронно через Celery
            from .tasks import send_order_confirmation_email
            send_order_confirmation_email.delay(order.id)
            liqpay_data = None
            if form.cleaned_data['payment_method'] == 'online':
                params = {
                    'action': 'pay',
                    'version': '3',
                    'order_id': str(order.id),
                    'amount': str(order.final_price),
                    'description': f'Оплата замовлення №{order.id}',
                    'currency': 'UAH',
                    'sandbox': 1 if settings.LIQPAY_PUBLIC_KEY.startswith('sandbox_') else 0,
                    'result_url': request.build_absolute_uri(reverse('orders:payment_complete')),
                    'server_url': request.build_absolute_uri(reverse('orders:payment_callback')),
                }
                liqpay_data = liqpay_client.cpay_params(params)

            cart.clear()
            request.session.pop('promo_discount', None)
            request.session.pop('promo_code', None)

            return render(request, 'orders/checkout.html', {
                'order': order,
                'discount_amount': discount_amount,
                'total_price_after_discount': total_price_after_discount,
                'liqpay_data': liqpay_data,
            })
    else:
        initial_data = {}
        if request.user.is_authenticated:
            initial_data = {
                'first_name': request.user.first_name,
                'last_name': request.user.last_name,
                'email': request.user.email
            }
        form = OrderCreateForm(initial=initial_data)

    return render(request, 'orders/order/create.html', {
        'cart': cart,
        'form': form,
        'total_price': total_price_after_discount,
        'original_price': total_price_before_promo,
        'discount_amount': discount_amount,
        'promo_code': promo_code_str,
    })

@login_required
def payment_start(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.paid:
        return redirect(reverse('accounts:order_history')) 

    params = {
        'action': 'pay',
        'amount': str(order.final_price),
        'currency': 'UAH',
        'description': f'Оплата замовлення №{order.id}',
        'order_id': str(order.id),
        'version': '3',
        'sandbox': 1 if settings.LIQPAY_PUBLIC_KEY.startswith('sandbox_') else 0,
        'result_url': request.build_absolute_uri(reverse('orders:payment_complete')),
        'server_url': request.build_absolute_uri(reverse('orders:payment_callback')),
    }
    
    liqpay_data = liqpay_client.cpay_params(params)
    
    return render(request, 'orders/payment_start.html', {
        'order': order, 
        'liqpay_data': liqpay_data
    })
def user_discount_stats(request):
    total_usage, total_savings, orders = get_user_discount_stats(request.user)
    return render(request, 'orders/user_discount_stats.html', {
        'total_usage': total_usage,
        'total_savings': total_savings,
        'orders': orders,
    })
@csrf_exempt 
def payment_callback(request):
    """
    Обробляє POST-запит від LiqPay (Server URL).
    Перевіряє підпис (signature) та оновлює статус замовлення.
    """
    if request.method == 'POST':
        data = request.POST.get('data')
        signature = request.POST.get('signature')
        generated_signature = liqpay_client._generate_signature(data)

        if generated_signature != signature:
            return HttpResponse(status=403)
        try:
            decoded_data = base64.b64decode(data).decode('utf-8')
            params = json.loads(decoded_data)
        except:
            return HttpResponse(status=400)
        order_id = params.get('order_id')
        status = params.get('status')
        if status in ['success', 'sandbox']:
            order = Order.objects.filter(id=order_id).first()
            if order:
                order.paid = True
                order.liqpay_status = status
                order.save()
        return HttpResponse(status=200)
    return HttpResponse(status=400)        

@login_required
def payment_complete(request):
    return render(request, 'orders/payment_complete.html', {})

@require_http_methods(["POST"])
def apply_promo_code(request):
    # Отримуємо код із POST-запиту
    code = request.POST.get("promo_code", "").strip().upper()
    if not code:
        return JsonResponse({"success": False, "error": "Введіть промокод"})

    try:
        # select_for_update запобігає race condition при одночасних запитах
        with transaction.atomic():
            promo = PromoCode.objects.select_for_update().get(code=code)

            if not promo.can_be_used():
                return JsonResponse({"success": False, "error": "Промокод недійсний або перевищено ліміт використання"})

            # Беремо загальну суму кошика з сесії
            cart_total = Decimal(request.session.get("cart_total", 0))
            discount_amount = Decimal(promo.apply_discount(cart_total))

            # Зберігаємо дані у сесії
            request.session['promo_code'] = promo.code
            request.session['promo_discount'] = float(discount_amount)
            request.session.modified = True

    except PromoCode.DoesNotExist:
        return JsonResponse({"success": False, "error": "Промокод не знайдено"})

    return JsonResponse({
        "success": True,
        "promo_code": promo.code,
        "discount_amount": float(discount_amount),
        "total_after_discount": float(cart_total - discount_amount)
    })