from decimal import Decimal
import time
from django.conf import settings
from main.models import Product

class Cart:
    def __init__(self, request):
        """
        Ініціалізація кошика.
        """
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart
        # Очищення запускається не частіше ніж раз на 5 хвилин
        self._purge_missing_products()


    def add(self, product, quantity=1, override_quantity=False, price=None, color='', size='', variant_image=''):
        """
        Додати товар до кошика або оновити його кількість.
        Ключ: product_id_color_size (унікальний для кожного варіанту)
        """
        # Створюємо унікальний ключ для варіанту товару
        color_key = color.lower().replace(' ', '_') if color else 'no_color'
        size_key = size.upper().replace(' ', '_') if size else 'no_size'
        cart_key = f"{product.id}_{color_key}_{size_key}"
        
        if price is None:
            current_price = product.price 
        else:
            current_price = price 
            
        if cart_key not in self.cart:
            self.cart[cart_key] = {
                'quantity': 0,
                'price': str(current_price),
                'color': color,
                'size': size,
                'variant_image': variant_image,
                'product_id': product.id  # Зберігаємо ID для пошуку продукту
            }
        
        self.cart[cart_key]['price'] = str(current_price)
        
        # Оновлюємо дані варіанту
        self.cart[cart_key]['color'] = color
        self.cart[cart_key]['size'] = size
        self.cart[cart_key]['variant_image'] = variant_image

        if override_quantity:
            self.cart[cart_key]['quantity'] = quantity
        else:
            self.cart[cart_key]['quantity'] += quantity
        
        if self.cart[cart_key]['quantity'] <= 0:
            self.remove_by_key(cart_key)
        else:
            self.save()

    def _purge_missing_products(self):
        """
        Видаляє з сесії записи для товарів, яких більше немає в БД.
        Виконується не частіше ніж раз на 5 хвилин (PURGE_INTERVAL_SECONDS).
        """
        PURGE_INTERVAL_SECONDS = 300  # 5 хвилин
        last_purge = self.session.get('cart_last_purge', 0)
        if time.time() - last_purge < PURGE_INTERVAL_SECONDS:
            return
        keys_to_remove = []
        product_ids_in_cart = set()
        
        for cart_key in self.cart.keys():
            # Перевіряємо формат ключа - повинен бути product_id_color_size
            key_parts = cart_key.split('_')
            if len(key_parts) < 3:
                # Старий формат ключа - видаляємо
                keys_to_remove.append(cart_key)
                continue
                
            product_id = key_parts[0]
            product_ids_in_cart.add(product_id)
        
        # Видаляємо старі ключі
        for key in keys_to_remove:
            del self.cart[key]
        
        # Перевіряємо існуючі товари
        existing_ids = set(
            str(i) for i in Product.objects.filter(id__in=product_ids_in_cart).values_list('id', flat=True)
        )
        stale_product_ids = product_ids_in_cart - existing_ids
        
        if stale_product_ids:
            keys_to_remove = []
            for cart_key in self.cart.keys():
                product_id = cart_key.split('_')[0]
                if product_id in stale_product_ids:
                    keys_to_remove.append(cart_key)
            
            for key in keys_to_remove:
                del self.cart[key]
        
        if keys_to_remove or stale_product_ids:
            self.save()

        # Оновлюємо мітку часу для throttling
        self.session['cart_last_purge'] = time.time()
        self.session.modified = True

    def save(self):
        self.session.modified = True

    def remove(self, product):
        """
        Видалити товар із кошика (усі варіанти).
        """
        product_id = str(product.id)
        keys_to_remove = [key for key in self.cart.keys() if key.startswith(f"{product_id}_")]
        for key in keys_to_remove:
            del self.cart[key]
        self.save()
    
    def remove_by_key(self, cart_key):
        """
        Видалити конкретний варіант товару за ключем.
        """
        if cart_key in self.cart:
            del self.cart[cart_key]
            self.save()
            
    def __iter__(self):
        """
        Перебір елементів у кошику та отримання товарів з бази даних.
        """
        # Отримуємо унікальні product_id з ключів кошика
        product_ids = set()
        for cart_key in self.cart.keys():
            # Витягуємо product_id з ключа формата "product_id_color_size"
            product_id = cart_key.split('_')[0]
            product_ids.add(product_id)
        
        products = Product.objects.filter(id__in=product_ids)

        cart = self.cart.copy()
        # Створюємо словник продуктів для швидкого доступу
        product_dict = {str(p.id): p for p in products}
        
        for cart_key, item in cart.items():
            product_id = cart_key.split('_')[0]
            if product_id in product_dict:
                item['product'] = product_dict[product_id]
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                
                # Переконуємось що всі поля існують для сумісності
                if 'color' not in item:
                    item['color'] = ''
                if 'size' not in item:
                    item['size'] = ''
                if 'variant_image' not in item:
                    item['variant_image'] = ''
                    
                yield item

    def __len__(self):
        """
        Підрахувати загальну кількість товарів у кошику.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """
        Підрахувати загальну вартість товарів у кошику.
        """
        return sum(Decimal(item['price']) * item['quantity'] 
                   for item in self.cart.values())

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.save()