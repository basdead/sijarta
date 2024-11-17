from django.urls import path
from .views import mypay_view

urlpatterns = [
    path('', mypay_view, name='mypay'),
]
