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

class Order(models.Model):
    pengguna = models.ForeignKey(Pengguna, on_delete=models.CASCADE, related_name='orders')
    pekerja = models.ForeignKey(Pekerja, on_delete=models.SET_NULL, related_name='orders', null=True, blank=True)
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