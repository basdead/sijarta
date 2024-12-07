from django.urls import path
from . import views

app_name = 'pemesanan_jasa'

urlpatterns = [
    path('form/<str:subcategory_name>/', views.order_jasa, name='order_form'),
]