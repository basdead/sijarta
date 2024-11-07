from django.urls import path
from . import views

urlpatterns = [
    path('', views.status_pekerjaan_jasa_view, name='status_pekerjaan_jasa'),  # Melihat dan memperbarui status pekerjaan jasa
    path('update/<str:job_id>/', views.update_status_pekerjaan_view, name='update_status_pekerjaan'),  # Memperbarui status pekerjaan jasa
]
