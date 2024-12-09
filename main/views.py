from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db import transaction
from .models import Pengguna, Pekerja, MyPay, MyPayTransaction, PekerjaanJasa, Order
from .forms import PenggunaForm, OrderForm, MyPayTransactionForm, PekerjaanJasaForm


# ---------------------------
# FITUR 1: R MyPay
# ---------------------------
@login_required
def mypay_dashboard(request):
    """
    Display MyPay balance and transaction history for the logged-in user.
    """
    try:
        mypay = MyPay.objects.get(pengguna=request.user.pengguna)
    except MyPay.DoesNotExist:
        return render(request, 'mypay_dashboard.html', {'error': 'MyPay account not found!'})

    transactions = MyPayTransaction.objects.filter(mypay=mypay).order_by('-timestamp')
    return render(request, 'mypay_dashboard.html', {'mypay': mypay, 'transactions': transactions})


# ---------------------------
# FITUR 2: CR Transaksi MyPay
# ---------------------------
@login_required
def create_mypay_transaction(request):
    """
    Create a new MyPay transaction for the logged-in user's MyPay account.
    """
    try:
        mypay = MyPay.objects.get(pengguna=request.user.pengguna)
    except MyPay.DoesNotExist:
        return redirect('main:mypay_dashboard')  # Redirect to MyPay dashboard if no account exists

    if request.method == 'POST':
        form = MyPayTransactionForm(request.POST)
        if form.is_valid():
            transaction = form.save(commit=False)
            transaction.mypay = mypay

            # Update balance based on transaction type
            if transaction.transaction_type == 'credit':
                mypay.balance += transaction.amount
            elif transaction.transaction_type == 'debit' and mypay.balance >= transaction.amount:
                mypay.balance -= transaction.amount
            else:
                return render(request, 'create_transaction.html', {'form': form, 'error': 'Insufficient balance!'})

            mypay.save()
            transaction.save()
            return redirect('main:mypay_dashboard')
    else:
        form = MyPayTransactionForm()

    return render(request, 'create_transaction.html', {'form': form})


# ---------------------------
# FITUR 3: RU Pekerjaan Jasa
# ---------------------------
@login_required
def pekerjaan_list(request):
    """
    Display all available job services for the logged-in pekerja.
    """
    jobs = PekerjaanJasa.objects.filter(pekerja__user=request.user).order_by('status')
    return render(request, 'pekerjaan_list.html', {'jobs': jobs})


@login_required
def update_pekerjaan(request, pekerjaan_id):
    """
    Update an existing job service for the logged-in pekerja.
    """
    pekerjaan = get_object_or_404(PekerjaanJasa, id=pekerjaan_id, pekerja__user=request.user)

    if request.method == 'POST':
        form = PekerjaanJasaForm(request.POST, instance=pekerjaan)
        if form.is_valid():
            form.save()
            return redirect('main:pekerjaan_list')
    else:
        form = PekerjaanJasaForm(instance=pekerjaan)

    return render(request, 'update_pekerjaan.html', {'form': form, 'pekerjaan': pekerjaan})


# ---------------------------
# FITUR 4: RU Status Pekerjaan Jasa
# ---------------------------
@login_required
def pekerjaan_status_list(request):
    """
    Display job services grouped by their status for the logged-in pekerja.
    """
    jobs = PekerjaanJasa.objects.filter(pekerja__user=request.user).order_by('status')
    return render(request, 'pekerjaan_status_list.html', {'jobs': jobs})


@login_required
def update_pekerjaan_status(request, pekerjaan_id):
    """
    Update the status of an existing job service.
    """
    pekerjaan = get_object_or_404(PekerjaanJasa, id=pekerjaan_id, pekerja__user=request.user)

    if request.method == 'POST':
        status = request.POST.get('status')
        if status in ['available', 'booked', 'completed']:
            pekerjaan.status = status
            pekerjaan.save()
            return redirect('main:pekerjaan_status_list')
        else:
            return render(request, 'update_status.html', {'pekerjaan': pekerjaan, 'error': 'Invalid status!'})

    return render(request, 'update_status.html', {'pekerjaan': pekerjaan})


# ---------------------------
# Order Management (CRUD Orders)
# ---------------------------
@login_required
def view_orders(request):
    """
    Display all orders for the logged-in pengguna.
    """
    orders = Order.objects.filter(pengguna=request.user.pengguna)
    return render(request, 'orders.html', {'orders': orders})


@login_required
def create_order(request):
    """
    Handle the creation of a new order by the logged-in pengguna.
    """
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.pengguna = request.user.pengguna
            order.save()
            return redirect('main:view_orders')
    else:
        form = OrderForm()

    return render(request, 'create_order.html', {'form': form})


@login_required
def update_order(request, order_id):
    """
    Update an existing order.
    """
    order = get_object_or_404(Order, id=order_id, pengguna__user=request.user)

    if request.method == 'POST':
        form = OrderForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect('main:view_orders')
    else:
        form = OrderForm(instance=order)

    return render(request, 'update_order.html', {'form': form, 'order': order})


@login_required
def delete_order(request, order_id):
    """
    Delete an existing order.
    """
    order = get_object_or_404(Order, id=order_id, pengguna__user=request.user)

    if request.method == 'POST':
        order.delete()
        return redirect('main:view_orders')

    return render(request, 'delete_order.html', {'order': order})
