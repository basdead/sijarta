from django.db import models

class Guest(models.Model):
    id_tamu = models.CharField(max_length=10, primary_key=True)
    nama = models.CharField(max_length=100)
    alamat = models.TextField()
    no_telp = models.CharField(max_length=15)
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.nama

class RoomType(models.Model):
    tipe = models.CharField(max_length=50, primary_key=True)
    kapasitas = models.IntegerField()
    harga_per_malam = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.tipe

class Room(models.Model):
    no_kamar = models.IntegerField(primary_key=True)
    tipe = models.ForeignKey(RoomType, on_delete=models.CASCADE)
    ketersediaan = models.BooleanField(default=True)

    def __str__(self):
        return f"Kamar {self.no_kamar} - {self.tipe}"

class Reservation(models.Model):
    id_reservasi = models.CharField(max_length=10, primary_key=True)
    id_tamu = models.ForeignKey(Guest, on_delete=models.CASCADE)
    no_kamar = models.ForeignKey(Room, on_delete=models.CASCADE)
    tanggal_check_in = models.DateField()
    tanggal_check_out = models.DateField()
    status = models.CharField(max_length=20, choices=[
        ('diproses', 'Diproses'),
        ('selesai', 'Selesai'),
        ('batal', 'Batal')
    ])

    def __str__(self):
        return f"Reservasi {self.id_reservasi} oleh {self.id_tamu}"

class Payment(models.Model):
    id_pembayaran = models.CharField(max_length=10, primary_key=True)
    id_reservasi = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    biaya = models.DecimalField(max_digits=10, decimal_places=2)
    metode = models.CharField(max_length=20, choices=[
        ('transfer_bank', 'Transfer Bank'),
        ('kredit', 'Kredit')
    ])

    def __str__(self):
        return f"Pembayaran {self.id_pembayaran} - {self.id_reservasi}"

class Facility(models.Model):
    id_fasilitas = models.CharField(max_length=10, primary_key=True)
    nama_fasilitas = models.CharField(max_length=100)
    deskripsi = models.TextField()

    def __str__(self):
        return self.nama_fasilitas

class FacilityBooking(models.Model):
    id_reservasi = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    id_fasilitas = models.ForeignKey(Facility, on_delete=models.CASCADE)

    def __str__(self):
        return f"Booking Fasilitas {self.id_fasilitas} untuk Reservasi {self.id_reservasi}"
