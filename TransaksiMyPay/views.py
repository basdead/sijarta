from django.shortcuts import render, redirect
from .forms import MyPayTransactionForm

def transaksi_mypay_view(request):
    if request.method == 'POST':
        form = MyPayTransactionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('mypay')
    else:
        form = MyPayTransactionForm()
    return render(request, 'transaksi_mypay.html', {'form': form})