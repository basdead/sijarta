# pekerjaanjasa/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('pekerjaan-jasa/', views.pekerjaan_jasa, name='pekerjaan_jasa'),
    path('kerjakan-pesanan/<str:pesanan_id>/', views.kerjakan_pesanan, name='kerjakan_pesanan'),
]
