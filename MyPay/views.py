from django.shortcuts import render, redirect
from .models import MyPay, MyPayTransaction
from main.models import Pengguna
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

# View for MyPay balance and transaction history
@login_required
def mypay_home(request):
    try:
        # Fetch the logged-in user's MyPay account
        mypay = MyPay.objects.get(guest=request.user)
        # Retrieve transactions related to the account
        transactions = mypay.mypaytransaction_set.all().order_by('-transaction_date')
    except MyPay.DoesNotExist:
        # If no account is found, handle gracefully
        mypay = None
        transactions = []

    # Render template with MyPay details and transactions
    return render(request, 'mypay/mypay.html', {
        'mypay': mypay,
        'transactions': transactions,
    })


# View for creating a new transaction (e.g., top-up, withdrawal, etc.)
@login_required
def create_transaction(request):
    if request.method == "POST":
        # Get amount from form
        amount = request.POST.get('amount')
        try:
            amount = float(amount)
        except ValueError:
            return HttpResponse("Invalid amount", status=400)

        try:
            # Get MyPay object for the logged-in user
            mypay = MyPay.objects.get(guest=request.user)
            # Create a new transaction
            transaction = MyPayTransaction.objects.create(
                mypay=mypay,
                amount=amount
            )
            # Update the balance after the transaction
            mypay.balance += amount  # Add the transaction amount to the balance
            mypay.save()

            # Redirect to MyPay home page to see updated balance
            return redirect('mypay:mypay_home')
        except MyPay.DoesNotExist:
            return HttpResponse("MyPay account not found", status=404)

    return render(request, 'mypay/create_transaction.html')  # Render a form for creating a transaction
