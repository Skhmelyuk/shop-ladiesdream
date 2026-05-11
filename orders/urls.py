from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('create/', views.order_create, name='order_create'),
    path('payment-start/<int:order_id>/', views.payment_start, name='payment_start'),
    path('payment-complete/', views.payment_complete, name='payment_complete'),
    path('payment-callback/', views.payment_callback, name='payment_callback'),
    path('discount-stats/', views.user_discount_stats, name='user_discount_stats'),
    path('np-proxy/', views.novaposhta_proxy, name='novaposhta_proxy'),
    path('apply-promo/', views.apply_promo_code, name='apply_promo_code'),
]