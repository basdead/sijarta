from django.urls import path
from . import views

urlpatterns = [
    path('', views.mypay_view, name='mypay'),  # Menampilkan saldo dan riwayat transaksi MyPay
]
