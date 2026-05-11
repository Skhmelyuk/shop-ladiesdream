from .cart import Cart
from .wishlist import Wishlist

def cart(request):
    """
    Повертає об'єкт кошика та списку бажань для контексту шаблону.
    """
    return {
        'cart': Cart(request),
        'wishlist': Wishlist(request)
    }