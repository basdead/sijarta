from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Pengguna(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nama = models.CharField(max_length=255)
    pwd = models.CharField(max_length=20)
    jenis_kelamin = models.CharField(max_length=1)
    no_hp = models.CharField(max_length=20)
    tgl_lahir = models.DateField()
    alamat = models.CharField(max_length=255)

    def __str__(self):
        return self.nama