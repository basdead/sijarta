from django.urls import path, re_path
from . import views

app_name = 'subkategori'

urlpatterns = [
    # Subcategory and Service Sessions
    re_path(r'^(?P<subcategory_name>[^/]+)/?$', views.show_subcategory, name='show_subcategory'),
]
