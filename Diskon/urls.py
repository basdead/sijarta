# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('diskon/', views.diskon_view, name='diskon'),  # List of Vouchers and Promos
    path('beli-voucher/<int:voucher_id>/', views.beli_voucher_view, name='beli_voucher'),  # Buy voucher
]