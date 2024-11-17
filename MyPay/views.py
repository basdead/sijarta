from django.shortcuts import render, get_object_or_404
from .models import MyPay, MyPayTransaction

def mypay_view(request):
    # Pastikan user memiliki data MyPay
    mypay = get_object_or_404(MyPay, user=request.user)
    transactions = MyPayTransaction.objects.filter(mypay=mypay).order_by('-tanggal')  # Urutkan riwayat terbaru

    return render(request, 'mypay.html', {
        'mypay': mypay,
        'transactions': transactions
    })
