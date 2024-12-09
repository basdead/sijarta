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
    path('profile/pengguna/', views.profile_pengguna, name='profile_pengguna'),

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

    # R MyPay
    path('mypay/', views.mypay_dashboard, name='mypay_dashboard'),

    # CR Transaksi MyPay
    path('mypay/transaction/create/', views.create_mypay_transaction, name='create_mypay_transaction'),

    # RU Pekerjaan Jasa
    path('pekerjaan/', views.pekerjaan_list, name='pekerjaan_list'),
    path('pekerjaan/<int:pekerjaan_id>/update/', views.update_pekerjaan, name='update_pekerjaan'),

    # RU Status Pekerjaan Jasa
    path('pekerjaan/status/', views.pekerjaan_status_list, name='pekerjaan_status_list'),
    path('pekerjaan/<int:pekerjaan_id>/status/update/', views.update_pekerjaan_status, name='update_pekerjaan_status'),
]
