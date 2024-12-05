from django.shortcuts import render, redirect
from django.contrib import messages
import logging
from utils.query import get_db_connection
from main.forms import PenggunaForm, PekerjaForm

logger = logging.getLogger(__name__)

def profile(request):
    """
    View and update profile based on user role.
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
        user_id = request.session.get('user_id')
        user_type = request.session.get('user_type')
        
        # Get basic user info
        cursor.execute('SELECT nama, jeniskelamin, nohp, tgllahir, alamat, saldomypay FROM "USER" WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'No user found with id {user_id}')
            return redirect('main:login_user')
            
        form_data = {
            'nama': user_data[0],
            'jenis_kelamin': user_data[1],
            'no_hp': user_data[2],
            'tgl_lahir': user_data[3],
            'alamat': user_data[4]
        }
        
        additional_attributes = {'saldomypay': user_data[5]}
        
        if user_type == 'pelanggan':
            cursor.execute('SELECT level FROM PELANGGAN WHERE id = %s', (user_id,))
            pelanggan_data = cursor.fetchone()
            if pelanggan_data:
                additional_attributes['level'] = pelanggan_data[0]
            form = PenggunaForm(initial=form_data)
            
        elif user_type == 'pekerja':
            cursor.execute(
                'SELECT namabank, nomorrekening, npwp, linkfoto, rating, jmlpesananselesai '
                'FROM PEKERJA WHERE id = %s', (user_id,)
            )
            pekerja_data = cursor.fetchone()
            if pekerja_data:
                additional_attributes.update({
                    'nama_bank': pekerja_data[0],
                    'no_rekening': pekerja_data[1],
                    'npwp': pekerja_data[2],
                    'foto_url': pekerja_data[3],
                    'rating': pekerja_data[4],
                    'jumlah_pesanan_selesai': pekerja_data[5]
                })
            form = PekerjaForm(initial=form_data)
            
        context = {
            'form': form,
            'profile': additional_attributes,
            'additional_attributes': additional_attributes
        }
        
        return render(request, 'profile.html', context)
        
    except Exception as error:
        error_message = str(error).split('CONTEXT')[0]
        logger.error(f'Error fetching profile: {error_message}')
        messages.error(request, error_message)
        return redirect('main:show_home_page')
    finally:
        cursor.close()
        connection.close()

def edit_profile(request):
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
        user_id = request.session.get('user_id')
        user_type = request.session.get('user_type')
        
        logger.info(f'Editing profile for user_id: {user_id}, user_type: {user_type}')
        
        # Get basic user info
        cursor.execute('SELECT nama, jeniskelamin, nohp, tgllahir, alamat FROM "USER" WHERE id = %s', (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'No user found with id {user_id}')
            return redirect('main:login_user')
            
        initial_data = {
            'nama': user_data[0],
            'jenis_kelamin': user_data[1],
            'no_hp': user_data[2],
            'tgl_lahir': user_data[3],
            'alamat': user_data[4]
        }

        if request.method == 'POST':
            logger.info(f'POST data received: {request.POST}')
            
            form_class = PenggunaForm if user_type == 'pelanggan' else PekerjaForm
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
                            user_id
                        )
                    )
                    logger.info('Updated USER table')
                    
                    # Update role-specific table if needed
                    if user_type == 'pekerja':
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
                                    user_id
                                )
                            )
                            logger.info('Successfully updated PEKERJA table')
                        except Exception as pe:
                            logger.error(f'Error updating PEKERJA table: {str(pe)}')
                            raise
                    
                    connection.commit()
                    logger.info('Successfully committed changes to database')
                    messages.success(request, 'Profile updated successfully!')
                    return redirect('profil:profile')
                except Exception as e:
                    connection.rollback()
                    error_message = str(e).split('CONTEXT')[0]
                    logger.error(f'Database error during profile update: {error_message}')
                    messages.error(request, f'Failed to update profile: {error_message}')
                    return redirect('profil:edit_profile')  # Stay on edit page instead of going home
            else:
                logger.error(f'Form validation failed. Form errors: {form.errors}')
                messages.error(request, 'Please check your input and try again')
                context = {'form': form}
                if user_type == 'pekerja':
                    additional_attributes = get_user_profile_data(user_id, user_type, cursor)
                    context['additional_attributes'] = additional_attributes
                return render(request, template_name, context)  # Stay on edit page with form errors
        else:
            # If it's a pekerja, get additional fields
            if user_type == 'pekerja':
                cursor.execute(
                    'SELECT namabank, nomorrekening, npwp, linkfoto FROM PEKERJA WHERE id = %s',
                    (user_id,)
                )
                pekerja_data = cursor.fetchone()
                if pekerja_data:
                    initial_data.update({
                        'nama_bank': pekerja_data[0],
                        'no_rekening': pekerja_data[1],
                        'npwp': pekerja_data[2],
                        'foto_url': pekerja_data[3]
                    })
            
            form_class = PenggunaForm if user_type == 'pelanggan' else PekerjaForm
            form = form_class(initial=initial_data)
            form.fields['pwd'].required = False  # Make password not required for editing

        template_name = 'profile_pengguna.html' if user_type == 'pelanggan' else 'profile_pekerja.html'
        context = {'form': form}
        if user_type == 'pekerja':
            additional_attributes = get_user_profile_data(user_id, user_type, cursor)
            context['additional_attributes'] = additional_attributes
        return render(request, template_name, context)
        
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
    if user_type == 'pekerja':
        cursor.execute(
            'SELECT linkfoto FROM PEKERJA WHERE id = %s',
            (user_id,)
        )
        pekerja_data = cursor.fetchone()
        if pekerja_data:
            profile_data['foto_url'] = pekerja_data[0]
    return profile_data
