# views.py
from django.shortcuts import render, redirect
from .models import Voucher, Promo, Pengguna
from django.contrib import messages

def diskon_view(request):
    vouchers = Voucher.objects.all()
    promos = Promo.objects.all()
    return render(request, 'diskon.html', {'vouchers': vouchers, 'promos': promos})

def beli_voucher_view(request, voucher_id):
    # Ensure that user is logged in
    pengguna = Pengguna.objects.get(user=request.user)
    voucher = Voucher.objects.get(id=voucher_id)

    # Check if user has enough balance
    if pengguna.saldo >= voucher.harga:
        # Deduct voucher price from user balance
        pengguna.saldo -= voucher.harga
        pengguna.save()
        
        messages.success(request, f"Voucher {voucher.nama} berhasil dibeli!")
        return redirect('diskon')
    else:
        messages.error(request, "Saldo tidak cukup untuk membeli voucher ini.")
        return redirect('diskon')
