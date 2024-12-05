from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import logging
from .forms import RoleSelectionForm, PenggunaForm, PekerjaForm, SubkategoriForm, OrderForm
from django.http import HttpResponseRedirect
from django.urls import reverse
from utils.query import *
import uuid

logger = logging.getLogger(__name__)

# Home page view to display categories and subcategories
def get_user_profile_data(user_id, user_type, cursor):
    """Helper function to get user profile data for navbar"""
    profile_data = {}
    if user_type == 'pekerja':
        cursor.execute(
            'SELECT linkfoto FROM PEKERJA WHERE id = %s',
            (user_id,)
        )
        pekerja_data = cursor.fetchone()
        if pekerja_data:
            profile_data['foto_url'] = pekerja_data[0]
    return profile_data

def show_home_page(request):
    """
    Display the home page with all categories and their subcategories.
    """
    context = {}
    if request.session.get('is_authenticated'):
        connection, cursor = get_db_connection()
        if connection and cursor:
            try:
                user_id = request.session.get('user_id')
                user_type = request.session.get('user_type')
                additional_attributes = get_user_profile_data(user_id, user_type, cursor)
                context['additional_attributes'] = additional_attributes
            finally:
                cursor.close()
                connection.close()
    return render(request, 'home.html', context)

@transaction.atomic
def register(request):
    role = request.GET.get('role')
    if request.method == 'POST':
        role = request.POST.get('role')
        logger.info(f"POST data received: {request.POST}")
        
        if not role:
            messages.error(request, 'Role is required')
            return redirect('main:register')
            
        form = PenggunaForm(request.POST) if role == 'pengguna' else PekerjaForm(request.POST)
        logger.info(f"Form data: {form.data}")
        logger.info(f"Form errors: {form.errors}")
        
        if form.is_valid():
            connection, cursor = get_db_connection()
            if connection is None or cursor is None:
                logger.error('Database connection failed during registration')
                messages.error(request, 'Database connection failed')
                return redirect('main:register')
                
            try:
                # Generate UUID for the new user
                user_id = str(uuid.uuid4())
                
                # First, insert into USER table
                cursor.execute(
                    'INSERT INTO "USER" (id, nama, pwd, jeniskelamin, nohp, tgllahir, alamat, saldomypay) '
                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
                    (
                        user_id,
                        form.cleaned_data['nama'],
                        form.cleaned_data['pwd'],
                        form.cleaned_data['jenis_kelamin'],
                        form.cleaned_data['no_hp'],
                        form.cleaned_data['tgl_lahir'],
                        form.cleaned_data['alamat'],
                        0.00  # default saldomypay
                    )
                )
                
                # Then, insert into role-specific table
                if role == 'pengguna':
                    cursor.execute(
                        'INSERT INTO PELANGGAN (id, level) VALUES (%s, %s)',
                        (user_id, 'Basic')
                    )
                else:  # pekerja
                    cursor.execute(
                        'INSERT INTO PEKERJA (id, namabank, nomorrekening, npwp, linkfoto, rating, jmlpesananselesai) '
                        'VALUES (%s, %s, %s, %s, %s, %s, %s)',
                        (
                            user_id,
                            form.cleaned_data['nama_bank'],
                            form.cleaned_data['no_rekening'],
                            form.cleaned_data['npwp'],
                            form.cleaned_data['foto_url'],
                            0.00,  # default rating
                            0  # default jumlah_pesanan_selesai
                        )
                    )
                
                connection.commit()
                logger.info(f'Successfully registered new {role}')
                
                # Set session variables after successful registration
                request.session['user_id'] = user_id
                request.session['user_name'] = form.cleaned_data['nama']
                request.session['is_authenticated'] = True
                request.session['user_type'] = 'pelanggan' if role == 'pengguna' else 'pekerja'
                
                return redirect('main:show_home_page')
                
            except Exception as error:
                connection.rollback()
                error_message = str(error).split('CONTEXT')[0]
                logger.error(f'Error during {role} registration: {error_message}')
                messages.error(request, error_message)
            finally:
                cursor.close()
                connection.close()
        else:
            logger.error(f'Form validation failed: {form.errors}')
            messages.error(request, 'Please check your input and try again')
    else:
        if role == 'pengguna':
            form = PenggunaForm()
        elif role == 'pekerja':
            form = PekerjaForm()
        else:
            form = None

    return render(request, 'register.html', {'form': form, 'role': role})

# Login view
def login_user(request):
    """
    Handle user login and redirect to homepage upon successful login.
    """
    if request.method == 'POST':
        no_hp = request.POST.get('no_hp')
        password = request.POST.get('password')
        
        connection, cursor = get_db_connection()
        if connection is None or cursor is None:
            logger.error('Database connection failed during login')
            messages.error(request, 'Database connection failed')
        else:
            try:
                # First check in USER table to get common user data
                cursor.execute('SELECT id, nama FROM "USER" WHERE nohp = %s AND pwd = %s', (no_hp, password))
                user_data = cursor.fetchone()
                
                if user_data:
                    user_id, user_name = user_data
                    
                    # Check if user is a PELANGGAN
                    cursor.execute('SELECT id FROM PELANGGAN WHERE id = %s', (user_id,))
                    is_pelanggan = cursor.fetchone() is not None
                    
                    # Check if user is a PEKERJA
                    cursor.execute('SELECT id FROM PEKERJA WHERE id = %s', (user_id,))
                    is_pekerja = cursor.fetchone() is not None
                    
                    # Create session data - convert UUID to string
                    request.session['user_id'] = str(user_id)
                    request.session['user_name'] = user_name
                    request.session['is_authenticated'] = True
                    request.session['user_type'] = 'pelanggan' if is_pelanggan else 'pekerja'
                    
                    logger.info(f'User {user_name} successfully logged in')
                    return redirect('main:show_home_page')
                else:
                    logger.error('Invalid No HP or password')
                    messages.error(request, 'Invalid No HP or password')
                    return redirect('main:login_user')
                    
            except Exception as error:
                error_message = str(error).split('CONTEXT')[0]
                logger.error(f'Error during login: {error_message}')
                messages.error(request, error_message)
            finally:
                cursor.close()
                connection.close()

    return render(request, 'login.html')


# Logout view
def logout_user(request):
    """
    Handle user logout.
    """
    # Clear session variables
    request.session['user_id'] = None
    request.session['user_name'] = None
    request.session['is_authenticated'] = False
    request.session['user_type'] = None
    
    # Flush the session
    request.session.flush()
    
    return redirect('main:show_home_page')

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
    context = {}
    if request.session.get('is_authenticated'):
        connection, cursor = get_db_connection()
        if connection and cursor:
            try:
                user_id = request.session.get('user_id')
                user_type = request.session.get('user_type')
                additional_attributes = get_user_profile_data(user_id, user_type, cursor)
                context['additional_attributes'] = additional_attributes
                orders = Order.objects.filter(pengguna=request.user.pengguna)
                context['orders'] = orders
            finally:
                cursor.close()
                connection.close()
    return render(request, 'orders.html', context)

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
            return redirect('main:show_home_page')  
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
            return redirect('main:show_home_page')  
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
    if not request.user.is_staff:  
        return redirect('main:show_home_page')

    if request.method == 'POST':
        subkategori.delete()
        return redirect('main:show_home_page')

    return render(request, 'delete_subcategory.html', {'subcategory': subkategori})
