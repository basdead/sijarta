from django.db import models
from MyPay.models import Guest  # Mengimpor Guest dari aplikasi MyPay

class MyPayTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('top_up', 'Top Up'),
        ('payment', 'Pembayaran Jasa'),
        ('transfer', 'Transfer'),
        ('withdrawal', 'Penarikan'),
    ]

    id_transaksi = models.CharField(max_length=10, primary_key=True)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    destination_phone = models.CharField(max_length=15, blank=True, null=True)  # Only for transfers
    bank_account = models.CharField(max_length=30, blank=True, null=True)  # Only for withdrawals
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaksi {self.id_transaksi} - {self.transaction_type}"
