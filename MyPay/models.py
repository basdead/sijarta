from django.db import models

# Model Guest
class Guest(models.Model):
    id_tamu = models.CharField(max_length=10, primary_key=True)
    nama = models.CharField(max_length=100)
    alamat = models.TextField()
    no_telp = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nama

# Model MyPay
class MyPay(models.Model):
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"MyPay account for {self.guest.nama}"

# Model MyPayTransaction
class MyPayTransaction(models.Model):
    mypay = models.ForeignKey(MyPay, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Transaction {self.id} for {self.mypay.guest.nama}"
