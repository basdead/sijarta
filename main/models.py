from django.db import models
from django.contrib.auth.models import User
import uuid

# Model Pengguna
class Pengguna(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama = models.CharField(max_length=255)
    jenis_kelamin = models.CharField(
        max_length=1,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')]
    )
    no_hp = models.CharField(max_length=20, unique=True)
    pwd = models.CharField(max_length=255, default='default_password')
    tgl_lahir = models.DateField()
    alamat = models.CharField(max_length=255)
    saldomypay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    level = models.CharField(max_length=50, default='basic')

    USERNAME_FIELD = 'no_hp'

    class Meta:
        verbose_name = 'Pengguna'
        verbose_name_plural = 'Pengguna'

    def __str__(self):
        return self.nama

# Model Pekerja
class Pekerja(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nama = models.CharField(max_length=255)
    jenis_kelamin = models.CharField(
        max_length=1,
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')]
    )
    no_hp = models.CharField(max_length=20, unique=True)
    pwd = models.CharField(max_length=255, default='default_password')
    tgl_lahir = models.DateField()
    alamat = models.CharField(max_length=255)
    saldomypay = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
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
    no_rekening = models.CharField(max_length=20, unique=True)
    npwp = models.CharField(max_length=15, unique=True)
    foto_url = models.URLField()
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    jumlah_pesanan_selesai = models.IntegerField(default=0)
    kategori_pekerjaan = models.ForeignKey(
        'KategoriJasa',
        on_delete=models.CASCADE,
        related_name='pekerja',
        null=True,  # Allow null temporarily for migration
        blank=True,
        default=None
    )

    USERNAME_FIELD = 'no_hp'

    class Meta:
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
    
    @classmethod
    def get_default_categories(cls):
        defaults = [
            'Home Cleaning',
            'Deep Cleaning',
            'Service AC',
            'Massage',
            'Hair Care'
        ]
        for category in defaults:
            cls.objects.get_or_create(nama_kategori=category)
            
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.__class__.objects.exists():
            self.__class__.get_default_categories()

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

# Model Order
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