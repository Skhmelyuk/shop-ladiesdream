from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.CartDetailView.as_view(), name='cart_detail'), 
    path('add/<int:product_id>/', views.CartAddView.as_view(), name='cart_add'),
    path('remove/<int:product_id>/', views.CartRemoveView.as_view(), name='cart_remove'),
    path('wishlist/', views.WishlistDetailView.as_view(), name='wishlist_detail'),
    path('wishlist/toggle/<int:product_id>/', views.WishlistToggleView.as_view(), name='wishlist_toggle'),
]