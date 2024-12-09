from django.shortcuts import render, redirect
from django.contrib import messages
import logging
from utils.query import get_db_connection
from main.forms import PenggunaForm, PekerjaForm
from django.http import Http404

logger = logging.getLogger(__name__)

def profile(request, username):
    """
    View and update profile based on user role and username.
    """
    # Check if user is authenticated via session
    if not request.session.get('is_authenticated'):
        return redirect('main:login_user')
        
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed while fetching profile')
        messages.error(request, 'Database connection failed')
        return redirect('main:show_home_page')
        
    try:
        # Get user by nama
        cursor.execute('SELECT id, nama FROM "USER" WHERE REPLACE(nama, \' \', \'\') = %s', (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            raise Http404("Profile not found")
            
        profile_user_id = user_result[0]
        profile_nama = user_result[1]
        
        # Check if this is the user's own profile
        is_own_profile = (request.session.get('user_name', '').replace(' ', '') == username and 
                         request.session.get('user_id') == str(profile_user_id))
        
        # Get basic user info
        cursor.execute('SELECT nama, jeniskelamin, nohp, tgllahir, alamat, saldomypay FROM "USER" WHERE id = %s', (profile_user_id,))
        user_data = cursor.fetchone()
            
        form_data = {
            'nama': user_data[0],
            'jenis_kelamin': user_data[1],
            'no_hp': user_data[2],
            'tgl_lahir': user_data[3],
            'alamat': user_data[4]
        }

        profile_data = {
            'nama': user_data[0],
            'foto_url': None  # Will be updated if it's a pekerja
        }

        additional_attributes = {'saldomypay': user_data[5]}

        # Check if the profile being viewed is a pekerja
        cursor.execute('SELECT id FROM PEKERJA WHERE id = %s', (profile_user_id,))
        is_pekerja = cursor.fetchone() is not None
        viewed_user_type = 'pekerja' if is_pekerja else 'pelanggan'

        # Get additional info based on user type
        if viewed_user_type == 'pekerja':
            # First get pekerja data
            cursor.execute(
                'SELECT namabank, nomorrekening, npwp, LinkFoto, rating '
                'FROM PEKERJA WHERE id = %s', (profile_user_id,)
            )
            pekerja_data = cursor.fetchone()
            
            # Then calculate completed orders count
            cursor.execute("""
                SELECT COUNT(DISTINCT pj.Id)
                FROM TR_PEMESANAN_JASA pj
                JOIN TR_PEMESANAN_STATUS tps ON pj.Id = tps.IdTrPemesanan
                JOIN STATUS_PEMESANAN sp ON tps.IdStatus = sp.Id
                WHERE pj.IdPekerja = %s
                AND sp.Status = 'Pesanan selesai'
                AND tps.TglWaktu = (
                    SELECT MAX(TglWaktu)
                    FROM TR_PEMESANAN_STATUS
                    WHERE IdTrPemesanan = pj.Id
                )
            """, [profile_user_id])
            completed_orders = cursor.fetchone()[0]
            
            if pekerja_data:
                additional_attributes.update({
                    'nama_bank': pekerja_data[0],
                    'no_rekening': pekerja_data[1],
                    'npwp': pekerja_data[2],
                    'rating': pekerja_data[4],
                    'jumlah_pesanan_selesai': completed_orders
                })
                profile_data['foto_url'] = pekerja_data[3]  # LinkFoto from PEKERJA table
                form = PekerjaForm(initial=form_data)
        else:
            cursor.execute('SELECT level FROM PELANGGAN WHERE id = %s', (profile_user_id,))
            pelanggan_data = cursor.fetchone()
            if pelanggan_data:
                additional_attributes['level'] = pelanggan_data[0]
            form = PenggunaForm(initial=form_data)

        # Get navbar profile data - only for pekerja users
        navbar_attributes = {}
        if request.session.get('user_type') == 'pekerja':
            cursor.execute('SELECT LinkFoto FROM PEKERJA WHERE id = %s', (request.session.get('user_id'),))
            navbar_data = cursor.fetchone()
            if navbar_data:
                navbar_attributes['foto_url'] = navbar_data[0]

        context = {
            'form': form,
            'profile': profile_data,
            'additional_attributes': additional_attributes,
            'is_own_profile': is_own_profile,
            'navbar_attributes': navbar_attributes,
            'viewed_user_type': viewed_user_type
        }
        
        return render(request, 'profile.html', context)
        
    except Http404:
        raise
    except Exception as error:
        error_message = str(error).split('CONTEXT')[0]
        logger.error(f'Error fetching profile: {error_message}')
        messages.error(request, error_message)
        return redirect('main:show_home_page')
    finally:
        cursor.close()
        connection.close()

def edit_profile(request, username):
    """
    Edit profile view that handles both Pengguna and Pekerja profiles using session authentication
    """
    # Check if user is authenticated via session
    if not request.session.get('is_authenticated'):
        logger.error('User not authenticated')
        return redirect('main:login_user')
        
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed while editing profile')
        messages.error(request, 'Database connection failed')
        return redirect('main:show_home_page')
        
    try:
        # Get user by nama
        cursor.execute('SELECT id FROM "USER" WHERE REPLACE(nama, \' \', \'\') = %s', (username,))
        user_result = cursor.fetchone()
        
        if not user_result:
            logger.error(f'No user found with username {username}')
            raise Http404("Profile not found")
            
        profile_user_id = user_result[0]
        
        # Check if the logged-in user is editing their own profile
        if str(request.session.get('user_id')) != str(profile_user_id):
            messages.error(request, "You can only edit your own profile")
            return redirect('profil:profile', username=username)
            
        logger.info(f'Editing profile for user_id: {profile_user_id}')

        # Get basic user info for edit
        cursor.execute('SELECT nama, jeniskelamin, nohp, tgllahir, alamat, saldomypay FROM "USER" WHERE id = %s', (profile_user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'No user found with id {profile_user_id}')
            return redirect('main:login_user')
            
        form_data = {
            'nama': user_data[0],
            'jenis_kelamin': user_data[1],
            'no_hp': user_data[2],
            'tgl_lahir': user_data[3],
            'alamat': user_data[4],
            'saldomypay': user_data[5]
        }

        # Check user type
        cursor.execute('SELECT id FROM PEKERJA WHERE id = %s', (profile_user_id,))
        is_pekerja = cursor.fetchone() is not None
        viewed_user_type = 'pekerja' if is_pekerja else 'pelanggan'

        if request.method == 'POST':
            logger.info(f'POST data received: {request.POST}')
            
            form_class = PenggunaForm if viewed_user_type == 'pelanggan' else PekerjaForm
            # Create form instance without requiring password field
            post_data = request.POST.copy()
            if 'pwd' not in post_data:
                post_data['pwd'] = ''  # Add empty password if not provided
            form = form_class(post_data)
            form.fields['pwd'].required = False  # Make password not required for editing
            
            logger.info(f'Form data: {form.data}')
            logger.info(f'Form errors before validation: {form.errors}')
            
            if form.is_valid():
                logger.info('Form is valid, updating profile')
                try:
                    # Update USER table
                    update_user_query = '''
                        UPDATE "USER" 
                        SET nama = %s, 
                            jeniskelamin = %s, 
                            nohp = %s, 
                            tgllahir = %s, 
                            alamat = %s
                        WHERE id = %s
                    '''
                    cursor.execute(
                        update_user_query,
                        (
                            form.cleaned_data['nama'],
                            form.cleaned_data['jenis_kelamin'],
                            form.cleaned_data['no_hp'],
                            form.cleaned_data['tgl_lahir'],
                            form.cleaned_data['alamat'],
                            profile_user_id
                        )
                    )
                    logger.info('Updated USER table')
                    
                    # Update role-specific table if needed
                    if viewed_user_type == 'pekerja':
                        logger.info('Updating PEKERJA table')
                        update_pekerja_query = '''
                            UPDATE PEKERJA 
                            SET namabank = %s, 
                                nomorrekening = %s, 
                                npwp = %s, 
                                linkfoto = %s 
                            WHERE id = %s
                        '''
                        try:
                            cursor.execute(
                                update_pekerja_query,
                                (
                                    form.cleaned_data.get('nama_bank'),
                                    form.cleaned_data.get('no_rekening'),
                                    form.cleaned_data.get('npwp'),
                                    form.cleaned_data.get('foto_url'),
                                    profile_user_id
                                )
                            )
                            logger.info('Successfully updated PEKERJA table')
                        except Exception as pe:
                            logger.error(f'Error updating PEKERJA table: {str(pe)}')
                            raise
                    
                    connection.commit()
                    logger.info('Successfully committed changes to database')
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('profil:profile', username=username)
                except Exception as e:
                    connection.rollback()
                    error_message = str(e).split('CONTEXT')[0]
                    logger.error(f'Database error during profile update: {error_message}')
                    messages.error(request, f'Failed to update profile: {error_message}')
                    return redirect('profil:edit_profile', username=username)  # Stay on edit page instead of going home
            else:
                logger.error(f'Form validation failed. Form errors: {form.errors}')
                messages.error(request, 'Please check your input and try again')
                context = {'form': form}
                if viewed_user_type == 'pekerja':
                    additional_attributes = get_user_profile_data(profile_user_id, viewed_user_type, cursor)
                    context['additional_attributes'] = additional_attributes
                return render(request, 'profile_pekerja.html', context)  # Stay on edit page with form errors
        else:
            # If it's a pekerja, get additional fields
            if viewed_user_type == 'pekerja':
                cursor.execute(
                    'SELECT namabank, nomorrekening, npwp, linkfoto FROM PEKERJA WHERE id = %s',
                    (profile_user_id,)
                )
                pekerja_data = cursor.fetchone()
                if pekerja_data:
                    form_data.update({
                        'nama_bank': pekerja_data[0],
                        'no_rekening': pekerja_data[1],
                        'npwp': pekerja_data[2],
                        'foto_url': pekerja_data[3]
                    })
            
            form_class = PenggunaForm if viewed_user_type == 'pelanggan' else PekerjaForm
            form = form_class(initial=form_data)
            form.fields['pwd'].required = False  # Make password not required for editing

        template_name = 'profile_pengguna.html' if viewed_user_type == 'pelanggan' else 'profile_pekerja.html'
        context = {'form': form}
        if viewed_user_type == 'pekerja':
            additional_attributes = get_user_profile_data(profile_user_id, viewed_user_type, cursor)
            context['additional_attributes'] = additional_attributes
        context['viewed_user_type'] = viewed_user_type
        return render(request, template_name, context)
        
    except Http404:
        raise
    except Exception as error:
        error_message = str(error).split('CONTEXT')[0]
        logger.error(f'Error editing profile: {error_message}')
        messages.error(request, error_message)
        return redirect('main:show_home_page')
    finally:
        cursor.close()
        connection.close()

def get_user_profile_data(user_id, user_type, cursor):
    """Helper function to get user profile data for navbar"""
    profile_data = {}
    try:
        if user_type == 'pekerja':
            cursor.execute(
                'SELECT p.LinkFoto FROM PEKERJA p WHERE p.Id = %s',
                (user_id,)
            )
            pekerja_data = cursor.fetchone()
            if pekerja_data:
                profile_data['foto_url'] = pekerja_data[0]
        else:
            # For regular users, set a default profile picture or leave it empty
            profile_data['foto_url'] = None
    except Exception as e:
        logger.error(f"Error fetching profile data: {str(e)}")
        profile_data['foto_url'] = None
    
    return profile_data

def show_discount_page(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please login first')
        return redirect('main:login')
    
    if not request.user.is_customer:
        messages.error(request, 'Only customers can access this page')
        return redirect('main:home')
    
    # Fetch vouchers with their discount info
    vouchers = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT v.kode, d.potongan, d.mintrpemesanan, v.jmlhariberlaku, v.kuotapenggunaan, v.harga 
            FROM VOUCHER v 
            JOIN DISKON d ON v.kode = d.kode
        """)
        vouchers = cursor.fetchall()
    
    # Fetch promos with their discount info
    promos = []
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT p.kode, d.potongan, d.mintrpemesanan, p.tglakhirberlaku 
            FROM PROMO p 
            JOIN DISKON d ON p.kode = d.kode
        """)
        promos = cursor.fetchall()
    
    def format_price(value):
        return "{:,.0f}".format(value).replace(",", ".")
    
    # Convert vouchers to list of dictionaries for easier template access
    voucher_list = []
    for v in vouchers:
        voucher_list.append({
            'kode': v[0],
            'potongan': format_price(v[1]),
            'mintrpemesanan': format_price(v[2]),
            'jmlhariberlaku': v[3],
            'kuota': v[4],
            'harga': format_price(v[5])
        })
    
    # Convert promos to list of dictionaries
    promo_list = []
    for p in promos:
        promo_list.append({
            'kode': p[0],
            'potongan': format_price(p[1]),
            'mintrpemesanan': format_price(p[2]),
            'tglakhirberlaku': p[3]
        })
    
    # Organize vouchers into rows of 3
    voucher_rows = [voucher_list[i:i+3] for i in range(0, len(voucher_list), 3)]
    
    # Organize promos into rows of 3
    promo_rows = [promo_list[i:i+3] for i in range(0, len(promo_list), 3)]
    
    context = {
        'voucher_rows': voucher_rows,
        'promo_rows': promo_rows,
    }
    
    return render(request, 'diskon.html', context)
