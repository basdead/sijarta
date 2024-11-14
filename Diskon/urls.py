from django.urls import path
from . import views

urlpatterns = [
    path('', views.diskon_view, name='diskon'),  # List vouchers and promos
    path('beli/<int:voucher_id>/', views.beli_voucher_view, name='beli_voucher'),  # Purchase a voucher
]
