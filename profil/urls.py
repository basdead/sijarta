from django.urls import path
from . import views

app_name = 'profil'

urlpatterns = [
    path('', views.profile, name='profile'),
    path('edit/', views.edit_profile, name='edit_profile'),
]
