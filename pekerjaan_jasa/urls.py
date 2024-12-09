from django.urls import path
from pekerjaan_jasa.views import show_my_works, show_work_status, accept_work

app_name = 'pekerjaan_jasa'

urlpatterns = [
    path('my/', show_my_works, name='show_my_works'),
    path('status/', show_work_status, name='show_work_status'),
    path('accept/', accept_work, name='accept_work'),
]