from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Pengguna

class RegisterForm(UserCreationForm):
    nama = forms.CharField(max_length=255)
    pwd = forms.CharField(widget=forms.PasswordInput, max_length=20)
    jenis_kelamin = forms.ChoiceField(choices=[('L', 'Laki-laki'), ('P', 'Perempuan')])
    no_hp = forms.CharField(max_length=20)
    tgl_lahir = forms.DateField()
    alamat = forms.CharField(max_length=255)

    class Meta:
        model = User
        fields = ('nama', 'pwd', 'jenis_kelamin', 'no_hp',  'tgl_lahir', 'alamat')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            pengguna = Pengguna.objects.create(user=user, nama=self.cleaned_data['nama'], jenis_kelamin=self.cleaned_data['jenis_kelamin'], no_hp=self.cleaned_data['no_hp'], tgl_lahir=self.cleaned_data['tgl_lahir'], alamat=self.cleaned_data['alamat'])
        return user