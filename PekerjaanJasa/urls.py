from django.urls import path
from . import views

urlpatterns = [
    path('', views.pekerjaan_jasa_view, name='pekerjaan_jasa'),  # Menampilkan daftar pekerjaan jasa yang tersedia
    path('ambil/<str:job_id>/', views.ambil_pekerjaan_view, name='ambil_pekerjaan'),  # Mengambil pekerjaan tertentu
]
