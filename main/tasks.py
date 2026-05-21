import os
import logging
import xml.etree.ElementTree as ET
from celery import shared_task
from django.apps import apps
from django.conf import settings
from PIL import Image

logger = logging.getLogger(__name__)

@shared_task
def process_product_image(model_name, instance_id):
    """
    Фонова конвертація фото в WebP та генерація різних розмірів.
    """
    try:
        Model = apps.get_model('main', model_name)
    except LookupError as e:
        logger.error(f"Модель {model_name} не знайдена в додатку main: {e}")
        return "Model not found"
        
    try:
        instance = Model.objects.get(pk=instance_id)
    except Model.DoesNotExist:
        logger.warning(f"Об'єкт {model_name} з ID={instance_id} не існує.")
        return "Instance not found"
        
    if not instance.image or not os.path.exists(instance.image.path):
        return "No image file found"
        
    orig_path = instance.image.path
    dir_name = os.path.dirname(orig_path)
    base_name = os.path.splitext(os.path.basename(orig_path))[0]
    
    # Визначаємо шляхи для згенерованих файлів
    webp_path = os.path.join(dir_name, f"{base_name}.webp")
    thumb_path = os.path.join(dir_name, f"{base_name}_thumbnail.webp")
    catalog_path = os.path.join(dir_name, f"{base_name}_catalog.webp")
    card_path = os.path.join(dir_name, f"{base_name}_card.webp")
    
    # Перевіряємо, чи всі файли вже існують
    if (orig_path.lower().endswith('.webp') and 
        os.path.exists(thumb_path) and 
        os.path.exists(catalog_path) and 
        os.path.exists(card_path)):
        return "All files already processed"
        
    try:
        with Image.open(orig_path) as img:
            # 1. Конвертуємо оригінал в WebP, якщо це ще не WebP
            if not orig_path.lower().endswith('.webp'):
                img.save(webp_path, 'WEBP', quality=85)
                # Оновлюємо поле в БД без виклику сигналів save()
                rel_dir = os.path.dirname(instance.image.name)
                instance.image.name = os.path.join(rel_dir, f"{base_name}.webp")
                Model.objects.filter(pk=instance_id).update(image=instance.image.name)
                # Видаляємо старий неоригінальний файл
                if os.path.exists(orig_path) and orig_path != webp_path:
                    os.remove(orig_path)
                orig_path = webp_path
                
            # 2. Генеруємо мініатюру (max 150px)
            img_thumb = img.copy()
            img_thumb.thumbnail((150, 150))
            img_thumb.save(thumb_path, 'WEBP', quality=80)
            
            # 3. Генеруємо зображення для каталогу (max 400px)
            img_catalog = img.copy()
            img_catalog.thumbnail((400, 400))
            img_catalog.save(catalog_path, 'WEBP', quality=85)
            
            # 4. Генеруємо зображення для картки (max 800px)
            img_card = img.copy()
            img_card.thumbnail((800, 800))
            img_card.save(card_path, 'WEBP', quality=85)
            
        logger.info(f"Успішно оброблено фото для {model_name} ID={instance_id}")
        return "Processed successfully"
    except Exception as e:
        logger.error(f"Помилка при обробці зображення {orig_path}: {e}")
        from orders.tasks import send_telegram_notification
        send_telegram_notification.delay(
            f"🚨 <b>Помилка при обробці зображення товару:</b>\n"
            f"Модель: <code>{model_name}</code> (ID: {instance_id})\n"
            f"Помилка: <code>{e}</code>"
        )
        return f"Error: {e}"


@shared_task
def generate_xml_feeds():
    """
    Генерує XML фід для Google Merchant Center та Facebook Ads.
    Записує результат у settings.MEDIA_ROOT / 'google_merchant_feed.xml'.
    """
    from main.models import Product
    
    try:
        domain = getattr(settings, 'SITE_DOMAIN', None)
        if not domain:
            hosts = [h for h in getattr(settings, 'ALLOWED_HOSTS', []) if h and h not in ('*', 'localhost', '127.0.0.1')]
            if hosts:
                domain = f"https://{hosts[0]}"
            else:
                domain = "https://ladiesdream.com.ua"
        if not domain.startswith('http'):
            domain = f"https://{domain}"
            
        products = Product.objects.filter(is_available=True)
        
        ET.register_namespace('g', 'http://base.google.com/ns/1.0')
        rss = ET.Element("rss", {
            "version": "2.0"
        })
        channel = ET.SubElement(rss, "channel")
        
        ET.SubElement(channel, "title").text = "LadiesDream E-commerce Platform"
        ET.SubElement(channel, "link").text = domain
        ET.SubElement(channel, "description").text = "LadiesDream - найкращий вибір жіночого одягу"
        
        for product in products:
            item = ET.SubElement(channel, "item")
            
            ET.SubElement(item, "{http://base.google.com/ns/1.0}id").text = str(product.id)
            ET.SubElement(item, "{http://base.google.com/ns/1.0}title").text = product.name
            
            from django.utils.html import strip_tags
            description = strip_tags(product.description or product.name)
            ET.SubElement(item, "{http://base.google.com/ns/1.0}description").text = description[:5000]
            
            product_url = f"{domain}{product.get_absolute_url()}"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}link").text = product_url
            
            if product.image:
                image_url = f"{domain}{product.image.url}"
            elif product.gallery.exists():
                image_url = f"{domain}{product.gallery.first().image.url}"
            else:
                image_url = f"{domain}/static/main/default_product.jpg"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}image_link").text = image_url
            
            ET.SubElement(item, "{http://base.google.com/ns/1.0}brand").text = "LadiesDream"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}condition").text = "new"
            ET.SubElement(item, "{http://base.google.com/ns/1.0}availability").text = "in stock"
            
            price = product.price
            discounted_price = product.get_current_price()
            
            ET.SubElement(item, "{http://base.google.com/ns/1.0}price").text = f"{price:.2f} UAH"
            if discounted_price < price:
                ET.SubElement(item, "{http://base.google.com/ns/1.0}sale_price").text = f"{discounted_price:.2f} UAH"
                
        os.makedirs(settings.MEDIA_ROOT, exist_ok=True)
        feed_path = os.path.join(settings.MEDIA_ROOT, 'google_merchant_feed.xml')
        
        tree = ET.ElementTree(rss)
        with open(feed_path, 'wb') as f:
            f.write(b'<?xml version="1.0" encoding="utf-8"?>\n')
            tree.write(f, encoding='utf-8', xml_declaration=False)
            
        logger.info(f"Успішно згенеровано Google Merchant XML фід: {feed_path}")
        return "Feed generated successfully"
    except Exception as e:
        logger.error(f"Помилка при генерації XML фіду: {e}")
        from orders.tasks import send_telegram_notification
        send_telegram_notification.delay(f"🚨 <b>Помилка генерації XML-фіду:</b> <code>{e}</code>")
        return f"Error: {e}"
