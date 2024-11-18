from django.contrib import admin
from .models import Pengguna, Pekerja

@admin.register(Pengguna)
class PenggunaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'npwp')
    search_fields = ('nama', 'no_hp', 'npwp')
    list_filter = ('jenis_kelamin', 'tgl_lahir')
    ordering = ('nama',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'npwp')
        }),
    )

@admin.register(Pekerja)
class PekerjaAdmin(admin.ModelAdmin):
    list_display = ('nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'nama_bank', 'no_rekening', 'npwp')
    search_fields = ('nama', 'no_hp', 'npwp', 'nama_bank', 'no_rekening')
    list_filter = ('jenis_kelamin', 'nama_bank', 'tgl_lahir')
    ordering = ('nama',)
    fieldsets = (
        (None, {
            'fields': ('user', 'nama', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat', 'nama_bank', 'no_rekening', 'npwp', 'foto_url')
        }),
    )
