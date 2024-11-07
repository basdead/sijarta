from django.urls import path
from . import views

urlpatterns = [
    path('new/', views.transaksi_mypay_view, name='transaksi_mypay'),  # Form untuk transaksi baru MyPay
]
