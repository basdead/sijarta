from django.shortcuts import render, redirect
from utils.query import get_db_connection
from urllib.parse import unquote
from datetime import datetime
from django.utils import timezone
from zoneinfo import ZoneInfo
import logging
import re
from django.http import Http404
from django.contrib import messages

logger = logging.getLogger(__name__)

def get_user_date(request):
    # Get timezone from request headers or default to UTC
    user_timezone_str = request.META.get('HTTP_TIMEZONE', 'UTC')
    try:
        # Get current time in UTC
        utc_now = timezone.now()
        # Convert to user's timezone
        user_time = utc_now.astimezone(ZoneInfo(user_timezone_str))
        return user_time.strftime('%Y-%m-%d')
    except Exception:
        # Fallback to UTC if there's any error
        utc_time = timezone.now()
        return utc_time.strftime('%Y-%m-%d')

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
        # Get subcategory details
        cursor.execute('''
            SELECT s.id, s.namasubkategori, s.deskripsi, k.namakategori
            FROM SUBKATEGORI_JASA s
            JOIN KATEGORI_JASA k ON s.kategorijasaid = k.id
            WHERE REPLACE(s.namasubkategori, ' ', '') = %s
        ''', (subcategory_name,))
        
        subcategory_data = cursor.fetchone()
        if not subcategory_data:
            messages.error(request, 'Subcategory not found')
            return redirect('main:show_home_page')
            
        # Get available sessions
        cursor.execute('''
            SELECT sesi, harga 
            FROM SESI_LAYANAN 
            WHERE subkategoriid = %s
            ORDER BY sesi
        ''', (subcategory_data[0],))
        
        sessions = [
            {
                'sesi': row[0], 
                'harga': float(row[1]) if row[1] is not None else 0  # Raw price as float
            }
            for row in cursor.fetchall()
        ]

        # Get pre-selected session from URL parameter
        selected_session = request.GET.get('selected_session')
        logger.info(f"Selected session from URL: {selected_session}")
        logger.info(f"Session type: {type(selected_session)}")
        logger.info(f"Available sessions: {sessions}")

        if selected_session:
            try:
                selected_session = int(selected_session)
                logger.info(f"Converted selected_session to int: {selected_session}")
                # Verify selected session exists
                session_exists = any(session.get('sesi') == selected_session for session in sessions)
                logger.info(f"Session exists in available sessions: {session_exists}")
                if not session_exists:
                    logger.warning(f"Selected session {selected_session} not found in available sessions")
                    selected_session = None
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting selected_session: {e}")
                selected_session = None

        # Handle form submission
        if request.method == 'POST':
            tgl_pemesanan = request.POST.get('tgl_pemesanan')
            sesi = request.POST.get('sesi')
            kode_diskon = request.POST.get('kode_diskon') or None
            metode_bayar = request.POST.get('metode_bayar')

            # Get status based on payment method
            cursor.execute('SELECT nama FROM METODE_BAYAR WHERE id = %s', (metode_bayar,))
            payment_method = cursor.fetchone()
            
            if payment_method and payment_method[0] == 'MyPay':
                status = 'Menunggu Pembayaran'
            else:
                status = 'Mencari Pekerja Terdekat'

            # Get session price
            cursor.execute('SELECT harga FROM SESI_LAYANAN WHERE SubkategoriId = %s AND sesi = %s', 
                         (subcategory_data[0], sesi))
            session_price = cursor.fetchone()[0]

            # Insert new order
            cursor.execute('''
                INSERT INTO TR_PEMESANAN_JASA (
                    TglPemesanan, TglPekerjaan, WaktuPekerjaan,
                    TotalBiaya, IdPelanggan, IdKategoriJasa,
                    Sesi, IdDiskon, IdMetodeBayar
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING Id
            ''', (
                tgl_pemesanan,
                tgl_pemesanan,  # TglPekerjaan same as TglPemesanan for now
                datetime.now(),  # WaktuPekerjaan as current timestamp
                session_price,  # Use session price as total cost
                user_id,
                subcategory_data[0],  # SubkategoriId
                sesi,
                kode_diskon,
                metode_bayar
            ))
            
            # Get the newly created order ID
            new_order_id = cursor.fetchone()[0]

            # Get status ID based on payment method
            cursor.execute('SELECT nama FROM METODE_BAYAR WHERE id = %s', (metode_bayar,))
            payment_method = cursor.fetchone()
            
            if payment_method and payment_method[0] == 'MyPay':
                status_name = 'Menunggu Pembayaran'
            else:
                status_name = 'Mencari Pekerja Terdekat'

            # Get status ID
            cursor.execute('SELECT id FROM STATUS_PEMESANAN WHERE status = %s', (status_name,))
            status_id = cursor.fetchone()[0]

            # Insert into TR_PEMESANAN_STATUS
            cursor.execute('''
                INSERT INTO TR_PEMESANAN_STATUS (
                    IdTrPemesanan, IdStatus, TglWaktu
                ) VALUES (
                    %s, %s, %s
                )
            ''', (
                new_order_id,
                status_id,
                datetime.now()
            ))
            
            connection.commit()
            messages.success(request, 'Order berhasil dibuat!')
            return redirect('pemesanan_jasa:show_my_orders')

        # Get payment methods
        cursor.execute('SELECT id, nama FROM METODE_BAYAR')
        payment_methods = [{'id': row[0], 'nama': row[1]} for row in cursor.fetchall()]

        context = {
            'subcategory': {
                'id': subcategory_data[0],
                'nama_subkategori': subcategory_data[1],
                'deskripsi': subcategory_data[2]
            },
            'category': {
                'nama_kategori': subcategory_data[3]
            },
            'sessions': sessions,
            'selected_session': selected_session,
            'payment_methods': payment_methods,
            'current_date': get_user_date(request)
        }

        return render(request, 'order_form.html', context)

    except Exception as e:
        logger.error(f"Error in order_jasa: {str(e)}")
        messages.error(request, 'An error occurred while processing your request')
        return redirect('main:show_home_page')

    finally:
        cursor.close()
        connection.close()


def show_my_orders(request):
    """
    View for showing user's orders
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    if not is_authenticated or not user_type or not user_id:
        messages.error(request, 'Please log in to continue')
        return redirect('main:login_user')
    
    if user_type != 'pelanggan':
        messages.error(request, 'Only customers can view their orders')
        return redirect('main:show_home_page')

    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        messages.error(request, 'Database connection failed')
        return redirect('main:show_home_page')

    try:
        # Get subcategories grouped by categories
        cursor.execute('''
            SELECT k.id as kategori_id, 
                   k.namakategori,
                   s.id as subkategori_id,
                   s.namasubkategori
            FROM KATEGORI_JASA k
            JOIN SUBKATEGORI_JASA s ON k.id = s.kategorijasaid
            ORDER BY k.namakategori, s.namasubkategori
        ''')
        
        # Organize subcategories by category
        categories = {}
        for row in cursor.fetchall():
            cat_id, cat_name, subcat_id, subcat_name = row
            if cat_id not in categories:
                categories[cat_id] = {
                    'id': cat_id,
                    'nama_kategori': cat_name,
                    'subcategories': []
                }
            categories[cat_id]['subcategories'].append({
                'id': subcat_id,
                'nama_subkategori': subcat_name
            })

        # Get order statuses
        cursor.execute('SELECT id, status FROM STATUS_PEMESANAN ORDER BY status')
        order_statuses = [
            {'id': row[0], 'status': row[1]}
            for row in cursor.fetchall()
        ]

        # Get user's orders with all required information
        cursor.execute('''
            SELECT 
                p.id, 
                p.tglpemesanan, 
                p.tglpekerjaan, 
                p.waktupekerjaan, 
                p.totalbiaya, 
                p.sesi, 
                sk.namasubkategori as nama,
                sk.id as subkategori_id,
                u.nama as nama_pekerja,
                s.status,
                sl.harga
            FROM TR_PEMESANAN_JASA p
            JOIN SUBKATEGORI_JASA sk ON p.idkategorijasa = sk.id
            LEFT JOIN TR_PEMESANAN_STATUS ps ON p.id = ps.idtrpemesanan
            LEFT JOIN STATUS_PEMESANAN s ON ps.idstatus = s.id
            LEFT JOIN PEKERJA w ON p.idpekerja = w.id
            LEFT JOIN "USER" u ON w.id = u.id
            LEFT JOIN SESI_LAYANAN sl ON (sk.id = sl.subkategoriid AND p.sesi = sl.sesi)
            WHERE p.idpelanggan = %s
            ORDER BY p.tglpemesanan DESC
        ''', (user_id,))
        
        orders = []
        for row in cursor.fetchall():
            orders.append({
                'id': row[0],
                'tanggal_pemesanan': row[1],
                'tanggal_pekerjaan': row[2],
                'waktu_pekerjaan': row[3],
                'harga': row[4],  # Pass raw number
                'sesi_layanan': row[5],
                'subkategori_jasa': {'nama': row[6], 'id': row[7]},
                'pekerja': {'nama': row[8]},
                'status': row[9] or 'Menunggu Konfirmasi'  # Default status if none found
            })

        context = {
            'orders': orders,
            'categories': list(categories.values()),
            'order_statuses': order_statuses
        }

        return render(request, 'my_orders.html', context)

    except Exception as e:
        logger.error(f"Error in show_my_orders: {str(e)}")
        messages.error(request, 'An error occurred while retrieving your orders')
        return redirect('main:show_home_page')

    finally:
        cursor.close()
        connection.close()