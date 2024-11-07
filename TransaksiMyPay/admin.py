from django.contrib import admin
from .models import MyPayTransaction

@admin.register(MyPayTransaction)
class MyPayTransactionAdmin(admin.ModelAdmin):
    list_display = ('id_transaksi', 'guest', 'transaction_type', 'amount', 'date')
    list_filter = ('transaction_type', 'date')
    search_fields = ('guest__nama', 'id_transaksi')
