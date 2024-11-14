# models.py
from django.db import models
from django.contrib.auth.models import User  # Assuming User model is used for Pengguna

class Voucher(models.Model):
    kode_voucher = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    deskripsi = models.TextField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)  # Price of the voucher

    def __str__(self):
        return self.nama

class Promo(models.Model):
    kode_promo = models.CharField(max_length=10, unique=True)
    nama = models.CharField(max_length=100)
    deskripsi = models.TextField()  # Promo description, no purchasing option

    def __str__(self):
        return self.nama

class Pengguna(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    saldo = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)  # User's balance
