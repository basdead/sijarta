from django.db import models
from MyPay.models import Guest
from PekerjaanJasa.models import Job

class MyPayTransaction(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE, related_name='mypay_transactions_transaksi')  # related_name ditambahkan
    transaction_type = models.CharField(max_length=20, choices=[
        ('TopUp', 'TopUp'),
        ('PayService', 'PayService'),
        ('Transfer', 'Transfer'),
        ('Withdrawal', 'Withdrawal'),
    ])
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    target_phone = models.CharField(max_length=15, blank=True, null=True)
    service = models.ForeignKey(Job, blank=True, null=True, on_delete=models.SET_NULL)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    bank_account = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.transaction_type} - {self.guest.name}"
