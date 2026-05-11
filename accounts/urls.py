from django.urls import path
from . import views  
app_name = "accounts"

urlpatterns = [
    path('profile/', views.profile_view, name="profile"), 
    path('orders/', views.order_history_view, name='order_history'),
]