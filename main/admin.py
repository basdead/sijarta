from django.contrib import admin
from .models import Pengguna, Pekerja

@admin.register(Pengguna)
class PenggunaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'saldomypay', 'level')
    search_fields = ('nama', 'no_hp')
    list_filter = ('jenis_kelamin', 'tgl_lahir', 'level')
    ordering = ('nama',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nama', 'jenis_kelamin', 'no_hp', 'pwd', 'tgl_lahir', 'alamat', 'saldomypay', 'level')
        }),
    )

@admin.register(Pekerja)
class PekerjaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'nama_bank', 'no_rekening', 'npwp', 'saldomypay', 'rating', 'jumlah_pesanan_selesai', 'kategori_pekerjaan')
    search_fields = ('nama', 'no_hp', 'npwp', 'nama_bank', 'no_rekening')
    list_filter = ('jenis_kelamin', 'nama_bank', 'tgl_lahir', 'kategori_pekerjaan')
    ordering = ('nama',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nama', 'jenis_kelamin', 'no_hp', 'pwd', 'tgl_lahir', 'alamat', 'saldomypay', 'nama_bank', 'no_rekening', 'npwp', 'foto_url', 'rating', 'jumlah_pesanan_selesai', 'kategori_pekerjaan')
        }),
    )
