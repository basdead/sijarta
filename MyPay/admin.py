from django.contrib import admin
from .models import Pengguna, MyPay, MyPayTransaction

@admin.register(MyPay)
class MyPayAdmin(admin.ModelAdmin):
    list_display = ('guest', 'balance')  # Display guest and current balance
    search_fields = ('guest__nama',)  # Search by guest name
    readonly_fields = ('balance',)  # Make balance readonly in admin
    # Add actions to make transactions or update balance if needed
    
@admin.register(MyPayTransaction)
class MyPayTransactionAdmin(admin.ModelAdmin):
    list_display = ('mypay', 'amount', 'transaction_date')  # Show transaction details
    search_fields = ('mypay__guest__nama', 'mypay__guest__id_tamu')  # Search by guest name or ID
    list_filter = ('transaction_date',)  # Filter by transaction date
