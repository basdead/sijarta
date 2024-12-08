from django.urls import path
from . import views

app_name = 'mypay'

urlpatterns = [
    path('', views.show_mypay, name='show_mypay'),
]