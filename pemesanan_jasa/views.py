from django.shortcuts import render, redirect
from utils.query import get_db_connection
from urllib.parse import unquote
from datetime import datetime
from profil.views import get_user_profile_data
import logging
import re
from django.http import Http404
from django.contrib import messages

logger = logging.getLogger(__name__)

def order_jasa(request, subcategory_name):
    """
    View for order form
    """
    # Debug session state
    logger.info("=== Order Form Access ===")
    logger.info("Request method: %s", request.method)
    logger.info("Session data:")
    for key, value in request.session.items():
        logger.info(f"  {key}: {value}")
    
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    logger.info(f"Authentication check:")
    logger.info(f"  is_authenticated: {is_authenticated}")
    logger.info(f"  user_type: {user_type}")
    logger.info(f"  user_id: {user_id}")
    
    if not is_authenticated or not user_type or not user_id:
        logger.warning("Missing session data")
        messages.error(request, 'Please log in to continue')
        return redirect('main:login_user')
    
    if user_type != 'pelanggan':
        logger.warning(f"Invalid user type: {user_type}")
        messages.error(request, 'Only customers can place orders')
        return redirect('main:show_home_page')

    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        messages.error(request, 'Database connection failed')
        return redirect('main:show_home_page')

    try:
        # Get subcategory data
        formatted_subcategory = ' '.join(re.findall('[A-Z][^A-Z]*', subcategory_name))
        if not formatted_subcategory:
            formatted_subcategory = subcategory_name

        logger.info(f"Looking up subcategory: {formatted_subcategory}")
        
        cursor.execute('''
            SELECT sk.id, sk.namasubkategori, sk.deskripsi, k.id, k.namakategori 
            FROM SUBKATEGORI_JASA sk
            JOIN KATEGORI_JASA k ON sk.kategorijasaid = k.id
            WHERE sk.namasubkategori = %s
        ''', (formatted_subcategory,))
        
        subcategory_data = cursor.fetchone()
        if not subcategory_data:
            logger.error(f"Subcategory not found: {formatted_subcategory}")
            raise Http404("Subcategory not found")

        # Get sessions data
        cursor.execute('SELECT sesi, harga FROM SESI_LAYANAN WHERE SubkategoriId = %s', (subcategory_data[0],))
        sessions = [{'sesi': row[0], 'harga': row[1]} for row in cursor.fetchall()]

        # Get payment methods
        cursor.execute('SELECT id, nama FROM METODE_BAYAR')
        payment_methods = [{'id': row[0], 'nama': row[1]} for row in cursor.fetchall()]

        context = {
            'subcategory': {
                'id': subcategory_data[0],
                'nama_subkategori': subcategory_data[1],  # namasubkategori from DB mapped to nama_subkategori for template
                'deskripsi': subcategory_data[2]
            },
            'category': {
                'id': subcategory_data[3],
                'nama_kategori': subcategory_data[4]  # namakategori from DB mapped to nama_kategori for template
            },
            'sessions': sessions,
            'payment_methods': payment_methods,
            'current_date': datetime.now().strftime('%Y-%m-%d')
        }

        return render(request, 'order_form.html', context)

    except Exception as e:
        logger.error(f"Error in order_jasa: {str(e)}")
        messages.error(request, 'An error occurred while processing your request')
        return redirect('main:show_home_page')

    finally:
        cursor.close()
        connection.close()