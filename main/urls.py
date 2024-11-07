from django.urls import path
from main.views import show_home_page
from main.views import register, login_user, logout_user

app_name = 'main'

urlpatterns = [
    path('', show_home_page, name='show_home_page'),
    path('register/', register, name='register'),
    path('login/', login_user, name='login_user'),
    path('logout/', logout_user, name='logout_user'),
]