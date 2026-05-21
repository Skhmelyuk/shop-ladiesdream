from celery import shared_task
from django.core.mail import send_mail
from .models import Order
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation_email(order_id):
    """
    Task to send an email notification when an order is successfully created.
    """
    try:
        order = Order.objects.get(id=order_id)
        
        subject = f'Ваше замовлення №{order.id} на LadiesDream'
        message = (
            f"Шановний(а) {order.first_name},\n\n"
            f"Дякуємо за Ваше замовлення! Його номер: {order.id}.\n"
            f"Загальна сума до сплати: {order.final_price} грн."
        )
        if order.discounted_amount > 0:
            message += f" (Врахована знижка за промокодом {order.promo_code.code if order.promo_code else 'N/A'} на суму {order.discounted_amount} грн.)\n"
            
        message += f"\nМи зв'яжемося з Вами найближчим часом для уточнення деталей доставки за адресою: {order.city}, {order.delivery_address}.\n\nЗ повагою,\nКоманда ЛейдісДрім"
        
        send_mail(
            subject, 
            message, 
            'support@myshop.com', 
            [order.email]
        )
        return f"Лист для замовлення {order.id} успішно відправлено"
    except Order.DoesNotExist:
        logger.error(f"Замовлення {order_id} не знайдено.")
        return f"Помилка: Замовлення {order_id} не знайдено."
    except Exception as e:
        logger.error(f"Помилка відправки листа для замовлення {order_id}: {e}", exc_info=True)
        return f"Помилка: {str(e)}"

@shared_task
def sync_novaposhta_data():
    """
    Background task to sync Nova Poshta cities and warehouses.
    """
    from django.conf import settings
    from .models import NPCity, NPWarehouse
    import requests
    import json

    api_key = getattr(settings, 'NOVAPOSHTA_API_KEY', None)
    if not api_key:
        logger.error("NOVAPOSHTA_API_KEY is not set in settings.")
        return "Failed: Missing API Key"

    url = "https://api.novaposhta.ua/v2.0/json/"
    
    # 1. Завантаження міст
    city_payload = {
        "apiKey": api_key,
        "modelName": "Address",
        "calledMethod": "getCities",
        "methodProperties": {}
    }
    
    try:
        response = requests.post(url, json=city_payload)
        data = response.json()
        if data.get('success'):
            cities = data.get('data', [])
            logger.info(f"Синхронізація міст Нової Пошти: отримано {len(cities)} записів.")
            
            # Масове оновлення/створення
            cities_to_create = []
            existing_city_refs = set(NPCity.objects.values_list('ref', flat=True))
            
            for c in cities:
                if c['Ref'] not in existing_city_refs:
                    cities_to_create.append(
                        NPCity(
                            ref=c['Ref'],
                            name=c['Description'],
                            area=c.get('AreaDescription', '')
                        )
                    )
            if cities_to_create:
                NPCity.objects.bulk_create(cities_to_create, batch_size=1000)
                logger.info(f"Додано {len(cities_to_create)} нових міст.")
                
        else:
            logger.error("Помилка отримання міст НП: " + str(data.get('errors')))
    except Exception as e:
        logger.error("Помилка під час синхронізації міст: " + str(e))

    # 2. Завантаження відділень
    warehouse_payload = {
        "apiKey": api_key,
        "modelName": "Address",
        "calledMethod": "getWarehouses",
        "methodProperties": {}
    }
    
    try:
        response = requests.post(url, json=warehouse_payload)
        data = response.json()
        if data.get('success'):
            warehouses = data.get('data', [])
            logger.info(f"Синхронізація відділень Нової Пошти: отримано {len(warehouses)} записів.")
            
            warehouses_to_create = []
            existing_wh_refs = set(NPWarehouse.objects.values_list('ref', flat=True))
            city_ref_to_id = dict(NPCity.objects.values_list('ref', 'id'))
            
            for w in warehouses:
                city_ref = w.get('CityRef')
                if w['Ref'] not in existing_wh_refs and city_ref in city_ref_to_id:
                    warehouses_to_create.append(
                        NPWarehouse(
                            ref=w['Ref'],
                            city_id=city_ref_to_id[city_ref],
                            name=w['Description'],
                            number=w.get('Number', '')
                        )
                    )
            if warehouses_to_create:
                NPWarehouse.objects.bulk_create(warehouses_to_create, batch_size=1000)
                logger.info(f"Додано {len(warehouses_to_create)} нових відділень.")
                
    except Exception as e:
        logger.error("Помилка під час синхронізації відділень: " + str(e))

    return "Синхронізація завершена"

@shared_task
def cancel_unpaid_orders():
    """
    Task to cancel orders that are 'online' payment method, 
    unpaid, and older than 24 hours.
    """
    from django.utils import timezone
    from datetime import timedelta
    from .models import Order

    time_threshold = timezone.now() - timedelta(hours=24)
    
    unpaid_orders = Order.objects.filter(
        payment_method='online',
        paid=False,
        status='new',
        created__lte=time_threshold
    )
    
    count = unpaid_orders.count()
    if count > 0:
        for order in unpaid_orders:
            order.status = 'cancelled'
            order.save()
        logger.info(f"Автоматично скасовано {count} неоплачених замовлень старше 24 годин. Залишки повернуто.")
    
    return f"Скасовано {count} замовлень"


@shared_task
def send_abandoned_cart_reminders():
    """
    Періодична задача для надсилання нагадувань про покинуті кошики.
    Знаходить кошики, які не оновлювалися більше 2 годин, і надсилає нагадування.
    """
    from django.utils import timezone
    from datetime import timedelta
    from cart.models import AbandonedCart
    from main.models import Product
    from django.conf import settings
    from decimal import Decimal

    threshold_time = timezone.now() - timedelta(hours=2)
    abandoned_carts = AbandonedCart.objects.filter(
        updated_at__lte=threshold_time,
        reminder_sent=False
    ).select_related('user')

    sent_count = 0
    for ac in abandoned_carts:
        user = ac.user
        if not user.email:
            continue

        cart_data = ac.cart_data
        if not cart_data:
            continue

        items_list = []
        total_price = Decimal("0.00")
        
        product_ids = [item.get('product_id') for item in cart_data.values() if item.get('product_id')]
        products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}

        for item in cart_data.values():
            product_id = item.get('product_id')
            product = products.get(product_id)
            if not product:
                continue
            
            name = product.name
            quantity = item.get('quantity', 1)
            price = Decimal(item.get('price', product.price))
            color = item.get('color', '')
            size = item.get('size', '')
            
            variant_desc = f" ({color}, {size})" if color or size else ""
            item_desc = f"- {name}{variant_desc} x {quantity} — {price * quantity} грн"
            items_list.append(item_desc)
            total_price += price * quantity

        if not items_list:
            ac.delete()
            continue

        subject = "Ваші товари чекають на Вас у кошику LadiesDream!"
        items_text = "\n".join(items_list)
        message = (
            f"Вітаємо, {user.first_name or user.username}!\n\n"
            f"Ми помітили, що у Вашому кошику залишилися товари. Ми зберегли їх для Вас, "
            f"щоб Ви могли повернутися та завершити покупку в будь-який зручний момент.\n\n"
            f"Ось список Ваших товарів:\n"
            f"{items_text}\n\n"
            f"Загальна сума: {total_price} грн.\n\n"
            f"Перейти до кошика та оформити замовлення: http://127.0.0.1:8000/cart/\n\n"
            f"З повагою,\nКоманда LadiesDream"
        )
        
        try:
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@myshop.com'),
                [user.email]
            )
            ac.reminder_sent = True
            ac.save()
            sent_count += 1
            logger.info(f"Надіслано нагадування про кошик користувачу {user.username} ({user.email})")
        except Exception as e:
            logger.error(f"Помилка при надсиланні нагадування про кошик користувачу {user.username}: {e}")

    return f"Надіслано {sent_count} нагадувань про покинуті кошики."


@shared_task
def send_daily_sales_report():
    """
    Щоденний звіт про продажі для адміністрації.
    Збирає статистику за останні 24 години та надсилає HTML-лист адміністраторам.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth.models import User
    from django.db.models import Sum, Count
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from .models import Order, OrderItem, SalesReportSetting
    from decimal import Decimal

    config = SalesReportSetting.objects.first()

    now = timezone.now()
    start_time = now - timedelta(hours=24)
    
    orders_last_24h = Order.objects.filter(created__gte=start_time)
    
    total_orders = orders_last_24h.count()
    paid_orders_qs = orders_last_24h.filter(paid=True)
    paid_orders = paid_orders_qs.count()
    unpaid_orders = total_orders - paid_orders
    
    total_revenue = paid_orders_qs.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
    avg_check = total_revenue / paid_orders if paid_orders else Decimal('0.00')
    
    new_users = User.objects.filter(date_joined__gte=start_time).count()
    
    top_products = (
        OrderItem.objects
        .filter(order__created__gte=start_time, order__paid=True)
        .values('product__name', 'product__id')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )
    
    recent_orders = orders_last_24h.select_related('user').order_by('-created')[:15]
    
    recipient_list = []
    if config:
        recipient_list = config.get_emails()
        
    context = {
        'date': now,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'total_revenue': total_revenue,
        'avg_check': avg_check,
        'new_users': new_users,
        'top_products': top_products,
        'recent_orders': recent_orders,
    }
    
    subject = f"LadiesDream: Звіт про продажі за останні 24 години ({now.strftime('%d.%m.%Y')})"
    
    text_message = (
        f"Звіт про продажі LadiesDream за {now.strftime('%d.%m.%Y')}\n\n"
        f"Виручка (оплачено): {total_revenue:.2f} грн\n"
        f"Всього замовлень: {total_orders} (оплачено: {paid_orders}, neoплачено: {unpaid_orders})\n"
        f"Середній чек: {avg_check:.2f} грн\n"
        f"Нових користувачів: {new_users}\n"
    )
    
    html_message = render_to_string('orders/admin_daily_report.html', context)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@myshop.com')
    
    if (not config or config.is_active) and recipient_list:
        email = EmailMultiAlternatives(
            subject,
            text_message,
            from_email,
            recipient_list
        )
        email.attach_alternative(html_message, "text/html")
        try:
            email.send()
            logger.info("Daily sales report distributed successfully.")
        except Exception as e:
            logger.error(f"Error during report distribution: {e}")
            
    return "Daily report processed successfully"


@shared_task
def send_weekly_sales_report():
    """
    Щотижневий аналітичний звіт про продажі для адміністрації.
    Збирає статистику за останні 7 днів та надсилає HTML-лист адміністраторам.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.contrib.auth.models import User
    from django.db.models import Sum, Count
    from django.template.loader import render_to_string
    from django.core.mail import EmailMultiAlternatives
    from django.conf import settings
    from .models import Order, OrderItem, SalesReportSetting
    from decimal import Decimal

    config = SalesReportSetting.objects.first()

    now = timezone.now()
    start_time = now - timedelta(days=7)
    
    orders_last_week = Order.objects.filter(created__gte=start_time)
    
    total_orders = orders_last_week.count()
    paid_orders_qs = orders_last_week.filter(paid=True)
    paid_orders = paid_orders_qs.count()
    unpaid_orders = total_orders - paid_orders
    
    total_revenue = paid_orders_qs.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
    avg_check = total_revenue / paid_orders if paid_orders else Decimal('0.00')
    
    new_users = User.objects.filter(date_joined__gte=start_time).count()
    
    daily_stats = []
    today_midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
    for i in range(6, -1, -1):
        day_start = today_midnight - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        day_orders = Order.objects.filter(created__range=(day_start, day_end))
        day_paid = day_orders.filter(paid=True)
        day_rev = day_paid.aggregate(total=Sum('final_price'))['total'] or Decimal('0.00')
        
        daily_stats.append({
            'date': day_start,
            'total': day_orders.count(),
            'paid': day_paid.count(),
            'revenue': day_rev
        })
    
    top_products = (
        OrderItem.objects
        .filter(order__created__gte=start_time, order__paid=True)
        .values('product__name', 'product__id')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )
    
    top_categories = (
        OrderItem.objects
        .filter(order__created__gte=start_time, order__paid=True)
        .values('product__category__name')
        .annotate(total_qty=Sum('quantity'))
        .order_by('-total_qty')[:5]
    )
    
    recipient_list = []
    if config:
        recipient_list = config.get_emails()
        
    context = {
        'start_date': start_time,
        'end_date': now,
        'total_orders': total_orders,
        'paid_orders': paid_orders,
        'unpaid_orders': unpaid_orders,
        'total_revenue': total_revenue,
        'avg_check': avg_check,
        'new_users': new_users,
        'daily_stats': daily_stats,
        'top_products': top_products,
        'top_categories': top_categories,
    }
    
    subject = f"LadiesDream: Щотижневий аналітичний звіт про продажі ({start_time.strftime('%d.%m')} - {now.strftime('%d.%m.%Y')})"
    
    text_message = (
        f"Щотижневий звіт про продажі LadiesDream за період з {start_time.strftime('%d.%m.%Y')} по {now.strftime('%d.%m.%Y')}\n\n"
        f"Загальна тижнева виручка: {total_revenue:.2f} грн\n"
        f"Всього замовлень: {total_orders} (оплачено: {paid_orders}, неоплачено: {unpaid_orders})\n"
        f"Середній чек: {avg_check:.2f} грн\n"
        f"Нових користувачів за тиждень: {new_users}\n"
    )
    
    html_message = render_to_string('orders/admin_weekly_report.html', context)
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@myshop.com')
    
    if (not config or config.is_active) and recipient_list:
        email = EmailMultiAlternatives(
            subject,
            text_message,
            from_email,
            recipient_list
        )
        email.attach_alternative(html_message, "text/html")
        try:
            email.send()
            logger.info("Weekly sales report distributed successfully.")
        except Exception as e:
            logger.error(f"Error during weekly report distribution: {e}")
            
    return "Weekly report processed successfully"


@shared_task
def clear_expired_sessions_and_carts():
    """
    Раз на тиждень очищає прострочені сесії Django, покинуті кошики старші за 60 днів,
    а також записи покинутих кошиків без товарів.
    """
    from django.core.management import call_command
    from django.utils import timezone
    from datetime import timedelta
    from cart.models import AbandonedCart
    
    # 1. Очищення сесій через стандартну команду Django
    try:
        call_command('clearsessions')
        logger.info("Успішно очищено прострочені сесії Django.")
    except Exception as e:
        logger.error(f"Помилка при очищенні сесій: {e}")
        
    # 2. Очищення покинутих кошиків старших за 60 днів
    cutoff = timezone.now() - timedelta(days=60)
    try:
        deleted_old, _ = AbandonedCart.objects.filter(updated_at__lt=cutoff).delete()
        if deleted_old > 0:
            logger.info(f"Видалено {deleted_old} застарілих покинутих кошиків (старших за 60 днів).")
    except Exception as e:
        logger.error(f"Помилка при очищенні старих кошиків: {e}")
        
    # 3. Очищення покинутих кошиків без товарів
    try:
        deleted_empty = 0
        for cart in AbandonedCart.objects.all():
            is_empty = True
            if isinstance(cart.cart_data, dict):
                for item in cart.cart_data.values():
                    if isinstance(item, dict) and item.get('quantity', 0) > 0:
                        is_empty = False
                        break
            if is_empty:
                cart.delete()
                deleted_empty += 1
        if deleted_empty > 0:
            logger.info(f"Видалено {deleted_empty} порожніх записів покинутих кошиків.")
    except Exception as e:
        logger.error(f"Помилка при очищенні порожніх кошиків: {e}")
        
    return "Очищення застарілих даних завершено"


@shared_task
def send_birthday_greetings():
    """
    Щоденна задача для привітання користувачів з Днем народження.
    Надсилає промокод на знижку 15% (percentage, value=15), який діє 7 днів.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from accounts.models import Profile
    from discounts.models import PromoCode
    
    today = timezone.now().date()
    profiles = Profile.objects.filter(
        birth_date__month=today.month,
        birth_date__day=today.day,
        user__email__isnull=False
    ).select_related('user')
    
    sent_count = 0
    for profile in profiles:
        code_prefix = f"BDAY-{profile.user.id}-{today.year}"
        
        # Перевірка, чи вже було створено промокод на цей рік
        if PromoCode.objects.filter(code=code_prefix).exists():
            continue
            
        try:
            # Створюємо промокод
            promo = PromoCode.objects.create(
                code=code_prefix,
                discount_type='percentage',
                value=15,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=7),
                usage_limit=1,
                min_order_amount=0,
                is_active=True,
                description=f"День народження {profile.user.username}"
            )
            
            site_domain = getattr(settings, 'SITE_DOMAIN', None)
            if not site_domain:
                hosts = [h for h in getattr(settings, 'ALLOWED_HOSTS', []) if h and h not in ('*', 'localhost', '127.0.0.1')]
                if hosts:
                    site_domain = hosts[0]
                else:
                    site_domain = "ladiesdream.com.ua"
            if site_domain.startswith('http'):
                site_url = site_domain
            else:
                site_url = f"https://{site_domain}"
                
            subject = "З Днем народження від LadiesDream! 🌸"
            context = {
                'user': profile.user,
                'promo_code': promo.code,
                'value_display': "15%",
                'valid_until': promo.end_date,
                'site_url': site_url,
            }
            html_message = render_to_string('orders/birthday_email.html', context)
            text_message = f"З Днем народження, {profile.user.first_name or profile.user.username}! Ваш промокод на знижку 15%: {promo.code}. Діє до {promo.end_date.strftime('%d.%m.%Y')}."
            
            email = EmailMultiAlternatives(
                subject,
                text_message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@myshop.com'),
                [profile.user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            sent_count += 1
            logger.info(f"Надіслано привітання з Днем народження для {profile.user.email}")
        except Exception as e:
            logger.error(f"Помилка при відправці привітання для {profile.user.username}: {e}")
            
    return f"Надіслано привітань: {sent_count}"


@shared_task
def send_winback_campaign():
    """
    Щоденна задача для повернення «сплячих» клієнтів.
    Знаходить тих, хто не купував 90+ днів, та надсилає промокод на 100 грн (fixed, value=100) при замовленні від 800 грн.
    """
    from django.utils import timezone
    from datetime import timedelta
    from django.conf import settings
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.contrib.auth.models import User
    from django.db.models import Max, Q
    from discounts.models import PromoCode
    import random
    import string
    
    ninety_days_ago = timezone.now() - timedelta(days=90)
    
    # Шукаємо користувачів, у яких останнє замовлення було > 90 днів тому або немає взагалі
    users = User.objects.annotate(
        last_order_date=Max('orders__created')
    ).filter(email__isnull=False)
    
    sleeping_users = users.filter(
        Q(last_order_date__isnull=True, date_joined__lt=ninety_days_ago) |
        Q(last_order_date__lt=ninety_days_ago)
    )
    
    sent_count = 0
    for user in sleeping_users:
        # Перевіряємо, чи надсилали ми вже winback промокод за останні 180 днів
        recent_winback = PromoCode.objects.filter(
            code__startswith=f"MISSYOU-{user.id}-",
            created_at__gte=timezone.now() - timedelta(days=180)
        ).exists()
        
        if recent_winback:
            continue
            
        try:
            # Генеруємо унікальний код
            suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
            code = f"MISSYOU-{user.id}-{suffix}"
            
            promo = PromoCode.objects.create(
                code=code,
                discount_type='fixed',
                value=100,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=14),
                usage_limit=1,
                min_order_amount=800,
                is_active=True,
                description=f"Повернення сплячого клієнта {user.username}"
            )
            
            site_domain = getattr(settings, 'SITE_DOMAIN', None)
            if not site_domain:
                hosts = [h for h in getattr(settings, 'ALLOWED_HOSTS', []) if h and h not in ('*', 'localhost', '127.0.0.1')]
                if hosts:
                    site_domain = hosts[0]
                else:
                    site_domain = "ladiesdream.com.ua"
            if site_domain.startswith('http'):
                site_url = site_domain
            else:
                site_url = f"https://{site_domain}"
                
            subject = "Ми сумуємо за Вами в LadiesDream! 💖"
            context = {
                'user': user,
                'promo_code': promo.code,
                'value_display': "100 грн",
                'valid_until': promo.end_date,
                'min_amount': 800,
                'site_url': site_url,
            }
            html_message = render_to_string('orders/winback_email.html', context)
            text_message = f"Ми сумуємо за Вами, {user.first_name or user.username}! Даруємо промокод {promo.code} на 100 грн знижки (при замовленні від 800 грн). Діє до {promo.end_date.strftime('%d.%m.%Y')}."
            
            email = EmailMultiAlternatives(
                subject,
                text_message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@myshop.com'),
                [user.email]
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
            sent_count += 1
            logger.info(f"Надіслано win-back лист для {user.email}")
        except Exception as e:
            logger.error(f"Помилка при відправці win-back листа для {user.username}: {e}")
            
    return f"Надіслано win-back листів: {sent_count}"


@shared_task
def track_novaposhta_parcels():
    """
    Автоматичний трекінг ТТН Нової Пошти.
    Перевіряє статус надісланих посилок і змінює статус замовлення на 'delivered' (Доставлено).
    """
    from django.conf import settings
    from .models import Order
    import requests
    
    api_key = getattr(settings, 'NOVAPOSHTA_API_KEY', None)
    if not api_key:
        logger.error("NOVAPOSHTA_API_KEY не вказано в налаштуваннях.")
        return "Failed: Missing API Key"
        
    orders = Order.objects.filter(
        status='shipped',
        delivery_type='NP',
        tracking_number__isnull=False
    ).exclude(tracking_number='')
    
    if not orders.exists():
        logger.info("Немає замовлень зі статусом 'shipped' для трекінгу.")
        return "No orders to track"
        
    documents = []
    order_map = {}
    for order in orders:
        ttn = order.tracking_number.strip()
        if ttn:
            documents.append({
                "DocumentNumber": ttn,
                "Phone": order.phone.strip() if order.phone else ""
            })
            order_map[ttn] = order
            
    if not documents:
        return "No valid tracking numbers found"
        
    url = "https://api.novaposhta.ua/v2.0/json/"
    payload = {
        "apiKey": api_key,
        "modelName": "TrackingDocument",
        "calledMethod": "getStatusDocuments",
        "methodProperties": {
            "Documents": documents
        }
    }
     
    try:
        response = requests.post(url, json=payload, timeout=15)
        data = response.json()
        if data.get('success'):
            results = data.get('data', [])
            updated_count = 0
            for doc in results:
                ttn = doc.get('Number')
                status_code = str(doc.get('StatusCode', ''))
                status_desc = doc.get('Status', '')
                
                # StatusCode 10, 11, 106 означає, що посилку отримано клієнтом
                is_delivered = status_code in ['10', '11', '106'] or any(
                    word in status_desc.lower() for word in ['забрано', 'одержано', 'отримано']
                )
                
                if is_delivered:
                    order = order_map.get(ttn)
                    if order and order.status != 'delivered':
                        order.status = 'delivered'
                        order.save()
                        updated_count += 1
                        logger.info(f"Замовлення #{order.id} (ТТН {ttn}) успішно отримано клієнтом. Статус оновлено на 'delivered'.")
            return f"Оновлено статусів замовлень: {updated_count}"
        else:
            error_msg = f"🚨 <b>Помилка API Нової Пошти при трекінгу ТТН:</b> {data.get('errors')}"
            logger.error(error_msg)
            send_telegram_notification.delay(error_msg)
            return f"API Error: {data.get('errors')}"
    except Exception as e:
        logger.error(f"Помилка при трекінгу ТТН Нової Пошти: {e}")
        return f"Error: {str(e)}"


@shared_task
def reconcile_online_payments():
    """
    Контроль онлайн-оплат (LiqPay).
    Перевіряє статус замовлень, які зависли в статусі неоплачених онлайн-оплат за останні 7 днів.
    """
    from django.conf import settings
    from django.utils import timezone
    from datetime import timedelta
    from .models import Order
    from .liqpay import liqpay_client
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    unpaid_online_orders = Order.objects.filter(
        paid=False,
        payment_method='online',
        created__gte=seven_days_ago
    )
    
    if not unpaid_online_orders.exists():
        logger.info("Немає неоплачених онлайн-замовлень за останні 7 днів для звірки.")
        return "No orders to reconcile"
        
    updated_count = 0
    for order in unpaid_online_orders:
        try:
            res = liqpay_client.check_status(order.id)
            if res:
                status = res.get('status')
                if status in ['success', 'sandbox']:
                    order.paid = True
                    if hasattr(order, 'liqpay_status'):
                        order.liqpay_status = status
                    order.save()
                    updated_count += 1
                    logger.info(f"Замовлення #{order.id} оплачено через LiqPay (виявлено звіркою). Статус оновлено.")
        except Exception as e:
            error_msg = f"🚨 <b>Помилка при звірці оплати замовлення #{order.id}:</b> {e}"
            logger.error(error_msg)
            send_telegram_notification.delay(error_msg)
            
    return f"Успішно підтверджено оплат: {updated_count}"


@shared_task
def send_telegram_notification(message, parse_mode='HTML'):
    """
    Надсилає повідомлення у закритий Telegram-чат розробника/адміністратора.
    """
    from django.conf import settings
    import requests
    
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    chat_id = getattr(settings, 'TELEGRAM_CHAT_ID', None)
    
    if not token or not chat_id:
        logger.warning("Telegram Bot Token або Chat ID не налаштовані.")
        return "Telegram credentials missing"
        
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": parse_mode
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            return "Notification sent successfully"
        else:
            logger.error(f"Помилка надсилання Telegram сповіщення: {response.text}")
            return f"Telegram error: {response.text}"
    except Exception as e:
        logger.error(f"Помилка при підключенні до API Telegram: {e}")
        return f"Request error: {str(e)}"


from celery.signals import task_failure

@task_failure.connect
def handle_task_failure(sender, task_id, exception, args, kwargs, traceback, einfo, **extra):
    # Запобігаємо нескінченній рекурсії, якщо падає сама задача надсилання сповіщення
    if sender.name == 'orders.tasks.send_telegram_notification':
        return
        
    message = (
        f"🚨 <b>Критична помилка в Celery Beat/Worker!</b>\n\n"
        f"<b>Задача:</b> <code>{sender.name}</code>\n"
        f"<b>ID:</b> <code>{task_id}</code>\n"
        f"<b>Помилка:</b> <code>{exception}</code>\n\n"
        f"📌 <i>Будь ласка, перевірте логи Celery.</i>"
    )
    send_telegram_notification.delay(message)



