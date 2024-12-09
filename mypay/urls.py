from django.urls import path
from . import views

app_name = 'mypay'

urlpatterns = [
    path('', views.show_mypay, name='show_mypay'),
    path('transactions/', views.show_transaction_page, name='show_transaction_page'),
    path('update-transaction-form/', views.update_transaction_form, name='update_transaction_form'),
]