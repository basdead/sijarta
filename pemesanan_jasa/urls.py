from django.urls import path
from . import views

app_name = 'pemesanan_jasa'

urlpatterns = [
    path('', views.show_my_orders, name='show_my_orders'),
    path('form/<str:subcategory_name>/', views.order_jasa, name='order_form'),
    path('validate-discount/', views.validate_discount, name='validate_discount'),
    path('cancel/', views.cancel_order, name='cancel_order'),
]