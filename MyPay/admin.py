from django.contrib import admin
from .models import Guest, RoomType, Room, Reservation, Payment, Facility, FacilityBooking

@admin.register(Guest)
class GuestAdmin(admin.ModelAdmin):
    list_display = ('id_tamu', 'nama', 'alamat', 'no_telp', 'email')
    search_fields = ('nama', 'no_telp', 'email')

@admin.register(RoomType)
class RoomTypeAdmin(admin.ModelAdmin):
    list_display = ('tipe', 'kapasitas', 'harga_per_malam')
    search_fields = ('tipe',)

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('no_kamar', 'tipe', 'ketersediaan')
    list_filter = ('tipe', 'ketersediaan')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id_reservasi', 'id_tamu', 'no_kamar', 'tanggal_check_in', 'tanggal_check_out', 'status')
    search_fields = ('id_reservasi', 'id_tamu__nama')
    list_filter = ('status',)

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id_pembayaran', 'id_reservasi', 'biaya', 'metode')
    search_fields = ('id_reservasi__id_reservasi', 'metode')

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('id_fasilitas', 'nama_fasilitas', 'deskripsi')

@admin.register(FacilityBooking)
class FacilityBookingAdmin(admin.ModelAdmin):
    list_display = ('id_reservasi', 'id_fasilitas')
    search_fields = ('id_reservasi__id_reservasi', 'id_fasilitas__nama_fasilitas')
