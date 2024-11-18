from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pengguna, Pekerja, SubkategoriJasa, Order


# Form untuk memilih role saat registrasi
class RoleSelectionForm(forms.Form):
    role = forms.ChoiceField(
        choices=[('pengguna', 'Pengguna'), ('pekerja', 'Pekerja')],
        widget=forms.RadioSelect,
        required=True
    )


# Form registrasi untuk Pengguna
class PenggunaForm(UserCreationForm):
    nama = forms.CharField(max_length=255, required=True)
    pwd = forms.CharField(widget=forms.PasswordInput, required=True)
    jenis_kelamin = forms.ChoiceField(
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')],
        widget=forms.RadioSelect,
        required=True
    )
    no_hp = forms.CharField(max_length=20, required=True)
    tgl_lahir = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    alamat = forms.CharField(max_length=255, required=True)

    class Meta:
        model = Pengguna
        fields = (
            'nama', 'pwd', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat'
        )

    def clean_no_hp(self):
        no_hp = self.cleaned_data.get('no_hp')
        if Pengguna.objects.filter(no_hp=no_hp).exists():
            raise forms.ValidationError("No HP sudah terdaftar.")
        return no_hp


# Form registrasi untuk Pekerja
class PekerjaForm(UserCreationForm):
    nama = forms.CharField(max_length=255, required=True)
    pwd = forms.CharField(widget=forms.PasswordInput, required=True)
    jenis_kelamin = forms.ChoiceField(
        choices=[('L', 'Laki-laki'), ('P', 'Perempuan')],
        widget=forms.RadioSelect,
        required=True
    )
    no_hp = forms.CharField(max_length=20, required=True)
    tgl_lahir = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    alamat = forms.CharField(max_length=255, required=True)
    saldomypay = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    nama_bank = forms.CharField(max_length=50, required=True)
    no_rekening = forms.CharField(max_length=20, required=True)
    npwp = forms.CharField(max_length=15, required=True)
    foto_url = forms.URLField(required=True)

    class Meta:
        model = Pekerja
        fields = (
            'nama', 'pwd', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat',
            'saldomypay', 'nama_bank', 'no_rekening', 'npwp', 'foto_url'
        )

    def clean_no_hp(self):
        no_hp = self.cleaned_data.get('no_hp')
        if Pekerja.objects.filter(no_hp=no_hp).exists():
            raise forms.ValidationError("No HP sudah terdaftar.")
        return no_hp

    def clean_npwp(self):
        npwp = self.cleaned_data.get('npwp')
        if Pekerja.objects.filter(npwp=npwp).exists():
            raise forms.ValidationError("NPWP sudah terdaftar.")
        return npwp

    def clean(self):
        cleaned_data = super().clean()
        nama_bank = cleaned_data.get('nama_bank')
        no_rekening = cleaned_data.get('no_rekening')

        # Validasi unik untuk pasangan nama bank dan no rekening
        if Pekerja.objects.filter(nama_bank=nama_bank, no_rekening=no_rekening).exists():
            raise forms.ValidationError("Pasangan nama bank dan nomor rekening sudah terdaftar.")
        return cleaned_data

# Form untuk Subkategori Jasa
class SubkategoriForm(forms.ModelForm):
    class Meta:
        model = SubkategoriJasa
        fields = ['kategori', 'nama_subkategori']

    def clean_nama_subkategori(self):
        nama_subkategori = self.cleaned_data.get('nama_subkategori')
        if SubkategoriJasa.objects.filter(nama_subkategori=nama_subkategori).exists():
            raise forms.ValidationError("Nama subkategori sudah terdaftar.")
        return nama_subkategori

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['details', 'pekerja', 'status']  # Pastikan field sesuai dengan model Anda