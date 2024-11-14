from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Voucher, Promo
from MyPay.models import MyPayTransaction  # Assuming this handles transactions or balance tracking
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def diskon_view(request):
    vouchers = Voucher.objects.filter(is_active=True)
    promos = Promo.objects.filter(is_active=True)
    return render(request, 'diskon.html', {'vouchers': vouchers, 'promos': promos})

@login_required
def beli_voucher_view(request, voucher_id):
    voucher = Voucher.objects.get(id=voucher_id)
    user = request.user
    
    # Assuming we have a balance field on the user (or user profile)
    if user.profile.balance >= voucher.price:
        # Deduct the price from the user's balance
        user.profile.balance -= voucher.price
        user.profile.save()
        
        # Record the transaction
        MyPayTransaction.objects.create(
            user=user,
            transaction_type='purchase_voucher',
            amount=voucher.price,
            description=f"Purchased voucher {voucher.code}"
        )
        
        messages.success(request, f"Voucher {voucher.code} successfully purchased!")
    else:
        messages.error(request, "Insufficient balance to purchase this voucher.")
    
    return redirect('diskon')