from django.db import models
from MyPay.models import RoomType, Room, Guest  # Mengimpor model dari aplikasi MyPay

class JobCategory(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name

class Job(models.Model):
    id_job = models.CharField(max_length=10, primary_key=True)
    category = models.ForeignKey(JobCategory, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    guest = models.ForeignKey(Guest, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default="Mencari Pekerja Terdekat")

    def __str__(self):
        return f"Job {self.id_job} - {self.category}"
