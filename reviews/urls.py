from django.urls import path
from .views import ReviewView, AddReplyView

app_name = 'reviews'

urlpatterns = [
    path('add/<int:product_pk>/', ReviewView.as_view(), name='add_review'),
    path('add-reply/', AddReplyView.as_view(), name='add_reply'),
]
