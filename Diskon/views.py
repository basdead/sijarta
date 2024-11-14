from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Voucher, Promo
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User

@login_required
def diskon_view(request):
    vouchers = Voucher.objects.filter(is_active=True)
    promos = Promo.objects.filter(is_active=True)
    return render(request, 'diskon/diskon.html', {'vouchers': vouchers, 'promos': promos})

@login_required
def beli_voucher_view(request, voucher_id):
    voucher = Voucher.objects.get(id=voucher_id)
    user_profile = request.user.profile  # Assuming UserProfile is set up with a balance field

    if user_profile.balance >= voucher.price:
        # Deduct the voucher price from the user's balance
        user_profile.balance -= voucher.price
        user_profile.save()
        
        # Display success message
        messages.success(request, f"Voucher {voucher.code} successfully purchased!")
    else:
        # Display error message if balance is insufficient
        messages.error(request, "Insufficient balance to purchase this voucher.")
    
    return redirect('diskon')