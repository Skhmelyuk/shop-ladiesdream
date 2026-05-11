from .cart import Cart

def cart(request):
    """
    Повертає об'єкт кошика для контексту шаблону.
    """
    return {'cart': Cart(request)}