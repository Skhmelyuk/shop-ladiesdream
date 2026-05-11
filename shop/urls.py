from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from admin_site import admin_site

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('main.urls', namespace='main')),
    path('discounts/', include('discounts.urls')),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('cart/', include('cart.urls', namespace='cart')),
    path('orders/', include('orders.urls', namespace='orders')),
    path('reviews/', include('reviews.urls', namespace='reviews')),
    path('ckeditor/', include('ckeditor_uploader.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
