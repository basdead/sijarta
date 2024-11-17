from django.shortcuts import render
from .forms import TransactionForm

def transaksi_mypay_view(request):
    form = TransactionForm(request.POST or None)

    if form.is_valid():
        # Process form data here (e.g., saving the transaction)
        pass

    return render(request, 'transaksi_mypay.html', {'form': form})
