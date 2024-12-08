from django.urls import path
from . import views

app_name = 'diskon'

urlpatterns = [
    path('', views.show_discount_page, name='show_discount_page'),
]