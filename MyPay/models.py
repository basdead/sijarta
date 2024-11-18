from django.db import models
from main.models import Pengguna

# Model MyPay
class MyPay(models.Model):
    guest = models.ForeignKey(Pengguna, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"MyPay account for {self.guest.nama}"

# Model MyPayTransaction
class MyPayTransaction(models.Model):
    mypay = models.ForeignKey(MyPay, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
