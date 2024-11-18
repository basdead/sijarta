from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.db import transaction
from django.contrib.auth.decorators import login_required
from .forms import RoleSelectionForm, PenggunaForm, OrderForm
from .models import Pengguna, KategoriJasa, SubkategoriJasa, Order

# Home page view to display categories and subcategories
def show_home_page(request):
    """
    Display the home page with all categories and their subcategories.
    """
    categories = KategoriJasa.objects.prefetch_related('subkategori').all()
    return render(request, 'home.html', {'categories': categories})

# Registration view
@transaction.atomic
def register(request):
    """
    Handle registration for Pengguna.
    """
    form = None
    if request.method == 'POST':
        form = PenggunaForm(request.POST)
        if form.is_valid():
            user = form.save()
            Pengguna.objects.create(
                user=user,
                nama=form.cleaned_data['nama'],
                jenis_kelamin=form.cleaned_data['jenis_kelamin'],
                no_hp=form.cleaned_data['no_hp'],
                tgl_lahir=form.cleaned_data['tgl_lahir'],
                alamat=form.cleaned_data['alamat'],
                npwp=form.cleaned_data['npwp']
            )
            login(request, user)
            return redirect('main:show_home_page')
    else:
        form = PenggunaForm()

    return render(request, 'register.html', {'form': form})

# Login view
def login_user(request):
    """
    Handle user login and redirect to homepage upon successful login.
    """
    if request.method == 'POST':
        no_hp = request.POST.get('no_hp')
        password = request.POST.get('password')
        user = None

        try:
            pengguna = Pengguna.objects.get(no_hp=no_hp)
            user = pengguna.user
        except Pengguna.DoesNotExist:
            try:
                pekerja = Pekerja.objects.get(no_hp=no_hp)
                user = pekerja.user
            except Pekerja.DoesNotExist:
                user = None

        if user and user.check_password(password):
            login(request, user)
            return redirect('main:show_home_page')  # Redirect to the homepage
        else:
            return render(request, 'login.html', {'error': 'Invalid No HP or password'})

    return render(request, 'login.html')


# Logout view
def logout_user(request):
    """
    Handle user logout.
    """
    logout(request)
    return redirect('main:login_user')

# Profile view for Pengguna
@login_required
def profile_pengguna(request):
    """
    View and update profile for Pengguna.
    """
    pengguna = get_object_or_404(Pengguna, user=request.user)
    if request.method == 'POST':
        form = PenggunaForm(request.POST, instance=pengguna)
        if form.is_valid():
            form.save()
            return redirect('main:profile_pengguna')
    else:
        form = PenggunaForm(instance=pengguna)
    return render(request, 'profile_pengguna.html', {'form': form})

# Subcategory session view
def subcategory_session(request, subcategory_id):
    """
    Display details for a specific subcategory and its services.
    """
    subkategori = get_object_or_404(SubkategoriJasa, id=subcategory_id)
    return render(request, 'subcategory_session.html', {'subkategori': subkategori})

# CRUD Orders (Pemesanan Jasa)
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
    order = get_object_or_404(Order, id=order_id)

    # Pastikan hanya pengguna yang berhak mengedit pesanannya
    if order.pengguna.user != request.user:
        return redirect('main:view_orders')

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
    order = get_object_or_404(Order, id=order_id)

    # Pastikan hanya pengguna yang berhak menghapus pesanannya
    if order.pengguna.user != request.user:
        return redirect('main:view_orders')

    if request.method == 'POST':
        order.delete()
        return redirect('main:view_orders')

    return render(request, 'delete_order.html', {'order': order})

@login_required
def create_subcategory(request):
    """
    Create a new subcategory.
    """
    if request.method == 'POST':
        form = SubkategoriForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main:show_home_page')  # Arahkan kembali ke halaman utama setelah sukses
    else:
        form = SubkategoriForm()
    
    return render(request, 'create_subcategory.html', {'form': form})

@login_required
def update_subcategory(request, subcategory_id):
    """
    Update an existing subcategory.
    """
    subkategori = get_object_or_404(SubkategoriJasa, id=subcategory_id)

    if request.method == 'POST':
        form = SubkategoriForm(request.POST, instance=subkategori)
        if form.is_valid():
            form.save()
            return redirect('main:show_home_page')  # Arahkan kembali ke halaman utama setelah sukses
    else:
        form = SubkategoriForm(instance=subkategori)

    return render(request, 'update_subcategory.html', {'form': form, 'subcategory': subkategori})

@login_required
def delete_subcategory(request, subcategory_id):
    """
    Delete an existing subcategory.
    """
    subkategori = get_object_or_404(SubkategoriJasa, id=subcategory_id)

    # Pastikan hanya admin atau pengguna tertentu yang dapat menghapus
    if not request.user.is_staff:  # Contoh aturan, hanya admin
        return redirect('main:show_home_page')

    if request.method == 'POST':
        subkategori.delete()
        return redirect('main:show_home_page')

    return render(request, 'delete_subcategory.html', {'subcategory': subkategori})
