from django.db import models
from django.contrib.auth.models import User  # Assuming we're using Django's User model

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price to purchase the voucher
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Voucher {self.code}"

class Promo(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField()
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    valid_until = models.DateField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Promo {self.title}"
