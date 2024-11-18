from django.urls import path
from . import views

app_name = 'mypay'

urlpatterns = [
    path('', views.mypay_home, name='my_pay'),  # Display MyPay balance and transaction history
    path('transaction/', views.create_transaction, name='create_transaction'),  # Create a new transaction
]
