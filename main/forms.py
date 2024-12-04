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
class PenggunaForm(forms.ModelForm):
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

    def __init__(self, *args, **kwargs):
        super(PenggunaForm, self).__init__(*args, **kwargs)
        if 'pwd' in self.fields:
            del self.fields['pwd']
        # Store the initial no_hp value
        if self.instance:
            self.initial_no_hp = self.instance.no_hp

    def clean_no_hp(self):
        no_hp = self.cleaned_data.get('no_hp')
        # Only validate if phone number has changed
        if hasattr(self, 'initial_no_hp') and no_hp != self.initial_no_hp:
            if Pengguna.objects.filter(no_hp=no_hp).exists():
                raise forms.ValidationError("No HP sudah terdaftar.")
        return no_hp

# Form registrasi untuk Pekerja
class PekerjaForm(forms.ModelForm):
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
    nama_bank = forms.ChoiceField(
        choices=[
            ('', 'Pilih Bank'),
            ('GoPay', 'GoPay'),
            ('OVO', 'OVO'),
            ('VA BCA', 'Virtual Account BCA'),
            ('VA BNI', 'Virtual Account BNI'),
            ('VA Mandiri', 'Virtual Account Mandiri')
        ],
        required=True
    )
    no_rekening = forms.CharField(max_length=20, required=True)
    npwp = forms.CharField(max_length=15, required=True)
    foto_url = forms.URLField(required=True)

    class Meta:
        model = Pekerja
        fields = (
            'nama', 'pwd', 'jenis_kelamin', 'no_hp', 'tgl_lahir', 'alamat','nama_bank', 'no_rekening', 'npwp', 'foto_url'
        )

    def __init__(self, *args, **kwargs):
        super(PekerjaForm, self).__init__(*args, **kwargs)
        if 'pwd' in self.fields:
            del self.fields['pwd']
        if self.instance:
            self.initial_no_hp = self.instance.no_hp
            self.initial_npwp = self.instance.npwp
            self.initial_nama_bank = self.instance.nama_bank
            self.initial_no_rekening = self.instance.no_rekening

    def clean_no_hp(self):
        no_hp = self.cleaned_data.get('no_hp')
        if not self.instance.pk or (hasattr(self, 'initial_no_hp') and no_hp != self.initial_no_hp):
            if Pekerja.objects.filter(no_hp=no_hp).exists():
                raise forms.ValidationError("No HP sudah terdaftar.")
        return no_hp

    def clean_npwp(self):
        npwp = self.cleaned_data.get('npwp')
        if not self.instance.pk or (hasattr(self, 'initial_npwp') and npwp != self.initial_npwp):
            if Pekerja.objects.filter(npwp=npwp).exists():
                raise forms.ValidationError("NPWP sudah terdaftar.")
        return npwp

    def clean(self):
        cleaned_data = super().clean()
        nama_bank = cleaned_data.get('nama_bank')
        no_rekening = cleaned_data.get('no_rekening')

        if not self.instance.pk or (
            hasattr(self, 'initial_nama_bank') and
            hasattr(self, 'initial_no_rekening') and
            (nama_bank != self.initial_nama_bank or no_rekening != self.initial_no_rekening)
        ):
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