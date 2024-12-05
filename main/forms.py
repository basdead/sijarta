from django import forms

# Form untuk memilih role saat registrasi
class RoleSelectionForm(forms.Form):
    role = forms.ChoiceField(
        choices=[('pengguna', 'Pengguna'), ('pekerja', 'Pekerja')],
        widget=forms.RadioSelect,
        required=True
    )


# Form registrasi untuk Pengguna
class PenggunaForm(forms.Form):
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


# Form registrasi untuk Pekerja
class PekerjaForm(forms.Form):
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


# Form untuk Subkategori Jasa
class SubkategoriForm(forms.Form):
    kategori = forms.CharField(max_length=255, required=True)
    nama_subkategori = forms.CharField(max_length=255, required=True)


# Form untuk Order
class OrderForm(forms.Form):
    details = forms.CharField(widget=forms.Textarea)
    status = forms.ChoiceField(
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled')
        ],
        initial='pending'
    )