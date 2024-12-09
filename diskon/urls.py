from django.urls import path
from . import views

app_name = 'diskon'

urlpatterns = [
    path('', views.show_discount_page, name='show_discount_page'),
    path('form/<str:voucher_code>/', views.show_voucher_form, name='show_voucher_form'),
    path('purchase/<str:voucher_code>/', views.voucher_purchase, name='voucher_purchase'),
]