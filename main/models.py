from django.db import models
from django.contrib.auth.models import User


# Model Pengguna
class Pengguna(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pengguna')
    nama = models.CharField(max_length=255)
    jenis_kelamin = models.CharField(
        max_length=1,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')]
    )
    no_hp = models.CharField(max_length=20, unique=True)
    tgl_lahir = models.DateField()
    alamat = models.CharField(max_length=255)
    npwp = models.CharField(max_length=15, unique=True, default="000000000000000")

    class Meta:
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        return self.nama


# Model Pekerja
class Pekerja(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='pekerja')
    nama = models.CharField(max_length=255)
    jenis_kelamin = models.CharField(
        max_length=1,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')]
    )
    no_hp = models.CharField(max_length=20, unique=True)
    tgl_lahir = models.DateField()
    alamat = models.CharField(max_length=255)
    nama_bank = models.CharField(
        max_length=50,
        choices=[
            ('GoPay', 'GoPay'),
            ('OVO', 'OVO'),
            ('VA BCA', 'Virtual Account BCA'),
            ('VA BNI', 'Virtual Account BNI'),
            ('VA Mandiri', 'Virtual Account Mandiri')
        ]
    )
    no_rekening = models.CharField(max_length=20)
    npwp = models.CharField(max_length=15, unique=True, default="000000000000000")
    foto_url = models.URLField()

    class Meta:
        unique_together = ('nama_bank', 'no_rekening')
        verbose_name = 'Pekerja'
        verbose_name_plural = 'Pekerja'

    def __str__(self):
        return self.nama


# Model MyPay (Saldo dan Transaksi)
class MyPay(models.Model):
    pengguna = models.OneToOneField(Pengguna, on_delete=models.CASCADE, related_name='mypay')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.pengguna.nama} - Saldo: {self.balance}"


class MyPayTransaction(models.Model):
    mypay = models.ForeignKey(MyPay, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(
        max_length=10,
        choices=[
            ('credit', 'Credit'),
            ('debit', 'Debit')
        ]
    )
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.mypay.pengguna.nama} - {self.transaction_type} - {self.amount}"


# Model Kategori Jasa
class KategoriJasa(models.Model):
    nama_kategori = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Kategori Jasa'
        verbose_name_plural = 'Kategori Jasa'

    def __str__(self):
        return self.nama_kategori


# Model Subkategori Jasa
class SubkategoriJasa(models.Model):
    kategori = models.ForeignKey(
        KategoriJasa,
        on_delete=models.CASCADE,
        related_name='subkategori'
    )
    nama_subkategori = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name = 'Subkategori Jasa'
        verbose_name_plural = 'Subkategori Jasa'

    def __str__(self):
        return f"{self.nama_subkategori} - {self.kategori.nama_kategori}"


# Model Pekerjaan Jasa
class PekerjaanJasa(models.Model):
    pekerja = models.ForeignKey(Pekerja, on_delete=models.CASCADE, related_name='pekerjaan')
    subkategori = models.ForeignKey(SubkategoriJasa, on_delete=models.CASCADE, related_name='pekerjaan')
    deskripsi = models.TextField()
    harga = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('available', 'Available'),
            ('booked', 'Booked'),
            ('completed', 'Completed')
        ],
        default='available'
    )

    class Meta:
        verbose_name = 'Pekerjaan Jasa'
        verbose_name_plural = 'Pekerjaan Jasa'

    def __str__(self):
        return f"{self.subkategori.nama_subkategori} - {self.pekerja.nama} ({self.status})"


# Model Order Jasa
class Order(models.Model):
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, related_name='orders')
    pekerjaan = models.ForeignKey(PekerjaanJasa, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
    details = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        default='pending'
    )

    def __str__(self):
        return f"Order {self.id} - {self.status}"
