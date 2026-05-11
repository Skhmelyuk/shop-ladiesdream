from django.urls import path
from . import views

app_name = 'discounts'

urlpatterns = [
    # Знижки
    path('add/<int:product_id>/', views.add_discount, name='add_discount'),
    path('product/<int:product_id>/discounts/', views.product_discounts, name='product_discounts'),
    path('edit/<int:discount_id>/', views.edit_discount, name='edit_discount'),
    path('delete/<int:discount_id>/', views.delete_discount, name='delete_discount'),

    # Промокоди
    path('promo/create/', views.create_promo_code, name='create_promo_code'),
    path('promo/list/', views.promo_code_list, name='promo_code_list'),
    path('promo/<int:code_id>/stats/', views.promo_code_stats, name='promo_code_stats'),

    path('promo/apply/', views.apply_promo_code, name='apply_promo_code'),
    path('promo/remove/', views.remove_promo_code, name='remove_promo_code'),
    path('apply/', views.apply_promo_code, name='apply_promo_code'),
]
