from django.contrib.auth.models import User
from myapp.models import MyPay, MyPayTransaction

# Tambahkan pengguna
user = User.objects.create_user(username='081234567890', password='password123')
mypay = MyPay.objects.create(user=user, saldo=100000)

# Tambahkan riwayat transaksi
MyPayTransaction.objects.create(mypay=mypay, nominal=50000, kategori='Top Up', deskripsi='Isi saldo')
MyPayTransaction.objects.create(mypay=mypay, nominal=-20000, kategori='Pembayaran', deskripsi='Pembelian')
