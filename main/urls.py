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

    # Profile Management
    path('profile/', views.profile, name='profile'),
    path('profile/pengguna/', views.profile_pengguna, name='profile_pengguna'),
    path('profile/pekerja/', views.profile_pekerja, name='profile_pekerja'),

    # Subcategory and Service Sessions
    path('subcategory/<int:subcategory_id>/', views.subcategory_session, name='subcategory_session'),

    # CRUD Subcategory (Admin or Authorized Users)
    path('subcategory/create/', views.create_subcategory, name='create_subcategory'),
    path('subcategory/<int:subcategory_id>/update/', views.update_subcategory, name='update_subcategory'),
    path('subcategory/<int:subcategory_id>/delete/', views.delete_subcategory, name='delete_subcategory'),

    # CRUD Orders (Pemesanan Jasa)
    path('orders/', views.view_orders, name='view_orders'),
    path('orders/create/', views.create_order, name='create_order'),
    path('orders/<int:order_id>/update/', views.update_order, name='update_order'),
    path('orders/<int:order_id>/delete/', views.delete_order, name='delete_order'),
]
