from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.product_list, name='product-list'),
    path('category/<slug:category_slug>/', views.product_list, name='product_list_by_category'),
    path('product/<int:id>/<slug:slug>/', views.product_detail, name='product-detail'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('google-merchant-feed.xml', views.google_merchant_feed, name='google_merchant_feed'),
    path('robots.txt', views.robots_txt, name='robots_txt'),
]