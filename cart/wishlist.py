from django.conf import settings
from main.models import Product

class Wishlist:
    def __init__(self, request):
        """
        Ініціалізація списку бажань.
        """
        self.session = request.session
        wishlist = self.session.get(settings.WISHLIST_SESSION_ID)
        if not wishlist:
            # Зберігаємо порожній список у сесії
            wishlist = self.session[settings.WISHLIST_SESSION_ID] = []
        self.wishlist = wishlist

    def toggle(self, product):
        """
        Додати товар до списку бажань, якщо його там немає, 
        або видалити, якщо він уже є.
        Повертає True, якщо товар було додано, і False - якщо видалено.
        """
        product_id = str(product.id)
        if product_id in self.wishlist:
            self.wishlist.remove(product_id)
            self.save()
            return False
        else:
            self.wishlist.append(product_id)
            self.save()
            return True

    def save(self):
        # Позначаємо сесію як змінену
        self.session.modified = True

    def has_product(self, product_id):
        """
        Перевіряє, чи є товар у списку бажань.
        """
        return str(product_id) in self.wishlist

    def clear(self):
        """
        Очищає список бажань з сесії.
        """
        del self.session[settings.WISHLIST_SESSION_ID]
        self.save()

    def __iter__(self):
        """
        Перебір елементів у списку бажань та отримання товарів з БД.
        """
        product_ids = self.wishlist
        products = Product.objects.filter(id__in=product_ids)
        for product in products:
            yield product

    def __len__(self):
        """
        Підрахувати загальну кількість товарів у списку бажань.
        """
        return len(self.wishlist)
