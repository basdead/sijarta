# Diskon/models.py
from django.db import models
from django.contrib.auth.models import User  # Using Django's User model

class Voucher(models.Model):
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField()
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Price for purchasing the voucher
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

# Optional: Profile model to manage balance if User does not have a balance attribute
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    def __str__(self):
        return f"{self.user.username}'s Profile"