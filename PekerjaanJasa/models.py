from django.db import models
from MyPay.models import Guest  # Asumsi Guest adalah model yang ada di MyPay


class JobCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name


class JobSubcategory(models.Model):
    category = models.ForeignKey(JobCategory, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class Job(models.Model):
    id_job = models.CharField(max_length=10, primary_key=True)
    category = models.ForeignKey(JobCategory, related_name="jobs", on_delete=models.CASCADE)
    subcategory = models.ForeignKey(JobSubcategory, related_name="jobs", on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="Mencari Pekerja Terdekat")

    def __str__(self):
        return f"Job {self.id_job} - {self.category.name} - {self.subcategory.name}"


class MyPayTransaction(models.Model):
    TOP_UP = 'TopUp'
    PAY_SERVICE = 'PayService'
    TRANSFER = 'Transfer'
    WITHDRAWAL = 'Withdrawal'

    TRANSACTION_CHOICES = [
        (TOP_UP, 'TopUp'),
        (PAY_SERVICE, 'PayService'),
        (TRANSFER, 'Transfer'),
        (WITHDRAWAL, 'Withdrawal'),
    ]

    user = models.ForeignKey(Guest, related_name="pekerjaanjasa_transactions", on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    target_phone = models.CharField(max_length=15, blank=True, null=True)  # Hanya untuk Transfer
    service = models.ForeignKey(Job, related_name="pekerjaanjasa_transactions", blank=True, null=True, on_delete=models.SET_NULL)
    bank_name = models.CharField(max_length=100, blank=True, null=True)  # Hanya untuk Withdrawal
    bank_account = models.CharField(max_length=20, blank=True, null=True)  # Hanya untuk Withdrawal
    date = models.DateTimeField(auto_now_add=True)  # Menambahkan field date

    def __str__(self):
        return f"{self.transaction_type} - {self.user.nama}"
