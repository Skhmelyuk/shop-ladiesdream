
import os
import django
from django.test import RequestFactory
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.messages.middleware import MessageMiddleware

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shop.settings')
django.setup()

from cart.views import cart_add
from main.models import Product

def test_cart_add_traceback():
    factory = RequestFactory()
    product = Product.objects.get(id=1)
    
    # Simulate POST data from cart
    post_data = {
        'quantity': '2',
        'override': '1',
        'color': 'Масло',
        'size': 'M'
    }
    
    request = factory.post(f'/cart/add/{product.id}/', post_data)
    
    # Mock HTMX headers
    request.META['HTTP_HX_REQUEST'] = 'true'
    request.META['HTTP_HX_CURRENT_URL'] = 'http://127.0.0.1:8000/cart/'
    
    # Add session and messages
    middleware = SessionMiddleware(lambda x: None)
    middleware.process_request(request)
    request.session.save()
    
    msg_middleware = MessageMiddleware(lambda x: None)
    msg_middleware.process_request(request)
    
    try:
        response = cart_add(request, product.id)
        print(f"Response status: {response.status_code}")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cart_add_traceback()
