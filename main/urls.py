from django.urls import path
from . import views  # Mengimpor semua views

app_name = 'main'

urlpatterns = [
    # Home Page
    path('', views.show_home_page, name='show_home_page'),

    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login_user'),
    path('logout/', views.logout_user, name='logout_user'),
]
