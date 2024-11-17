from django.contrib import admin
from PekerjaanJasa.models import MyPayTransaction


@admin.register(MyPayTransaction)
class MyPayTransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'transaction_type', 'user', 'amount', 'date')  # Pastikan id dan date ada di model
    list_filter = ('transaction_type', 'date')  # Pastikan field date ada
    search_fields = ('transaction_type', 'user__nama')
