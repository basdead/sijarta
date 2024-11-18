# from django.db import models
# from PekerjaanJasa.models import Job

# class JobStatus(models.Model):
#     STATUS_CHOICES = [
#         ('menunggu', 'Menunggu Pekerja Berangkat'),
#         ('tiba', 'Pekerja Tiba di Lokasi'),
#         ('dilakukan', 'Pelayanan Jasa Sedang Dilakukan'),
#         ('selesai', 'Pesanan Selesai'),
#         ('dibatalkan', 'Pesanan Dibatalkan'),
#     ]

#     job = models.OneToOneField(Job, on_delete=models.CASCADE, primary_key=True)
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"Status {self.job} - {self.status}"
