from django.db import models
from django.contrib.auth.models import User  # Assuming you're using the default User model

class MyPayTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('top_up', 'Top Up'),
        ('payment', 'Pembayaran Jasa'),
        ('transfer', 'Transfer'),
        ('withdrawal', 'Penarikan'),
    ]

    id_transaksi = models.CharField(max_length=10, primary_key=True)
    guest = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transaksimypay')  # Relate to User
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    destination_phone = models.CharField(max_length=15, blank=True, null=True)  # Only for transfers
    bank_account = models.CharField(max_length=30, blank=True, null=True)  # Only for withdrawals
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaksi {self.id_transaksi} - {self.transaction_type}"
