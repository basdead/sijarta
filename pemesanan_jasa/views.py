from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, Http404
from utils.query import get_db_connection
from urllib.parse import unquote
from datetime import datetime
from django.utils import timezone
from zoneinfo import ZoneInfo
import logging
import re
from django.contrib import messages
from datetime import timedelta
from django.views.decorators.http import require_http_methods
import uuid

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
                'harga': float(row[1]) if row[1] is not None else 0
            }
            for row in cursor.fetchall()
        ]

        # Get pre-selected session from URL parameter
        selected_session = request.GET.get('selected_session')
        if selected_session:
            try:
                selected_session = int(selected_session)
                session_exists = any(session.get('sesi') == selected_session for session in sessions)
                if not session_exists:
                    selected_session = None
            except (ValueError, TypeError):
                selected_session = None

        # Handle form submission
        if request.method == 'POST':
            tgl_pemesanan = request.POST.get('tgl_pemesanan')
            sesi = request.POST.get('sesi')
            kode_diskon = request.POST.get('kode_diskon')
            metode_bayar = request.POST.get('metode_bayar')
            total_pembayaran = request.POST.get('total_pembayaran')  # Get the actual total after discount

            # Get status based on payment method
            cursor.execute('SELECT nama FROM METODE_BAYAR WHERE id = %s', (metode_bayar,))
            payment_method = cursor.fetchone()
            
            if payment_method and payment_method[0] == 'MyPay':
                status = 'Menunggu Pembayaran'
            else:
                status = 'Mencari Pekerja Terdekat'

            # Get session price (original price)
            cursor.execute('SELECT harga FROM SESI_LAYANAN WHERE SubkategoriId = %s AND sesi = %s', 
                         (subcategory_data[0], sesi))
            session_price = cursor.fetchone()[0]

            # Initialize is_promo
            is_promo = False

            # If discount code is provided, validate it
            if kode_diskon:
                # First check if it exists in DISKON table
                cursor.execute('''
                    SELECT 1 FROM DISKON WHERE Kode = %s
                ''', (kode_diskon,))
                
                if not cursor.fetchone():
                    messages.error(request, 'Invalid discount code')
                    return render(request, 'order_form.html', {
                        'subcategory': {
                            'id': subcategory_data[0],
                            'nama_subkategori': subcategory_data[1],
                            'deskripsi': subcategory_data[2]
                        },
                        'category': {'nama_kategori': subcategory_data[3]},
                        'sessions': sessions,
                        'selected_session': selected_session,
                        'payment_methods': [{'id': row[0], 'nama': row[1]} for row in cursor.fetchall()],
                        'current_date': get_user_date(request)
                    })

                # Then check if it's a PROMO
                cursor.execute('''
                    SELECT TglAkhirBerlaku
                    FROM PROMO
                    WHERE Kode = %s
                ''', (kode_diskon,))
                
                promo = cursor.fetchone()
                if promo:
                    # It's a PROMO, check if it's expired
                    if promo[0] < datetime.now().date():
                        messages.error(request, 'This promo has expired')
                        return render(request, 'order_form.html', {
                            'subcategory': {
                                'id': subcategory_data[0],
                                'nama_subkategori': subcategory_data[1],
                                'deskripsi': subcategory_data[2]
                            },
                            'category': {'nama_kategori': subcategory_data[3]},
                            'sessions': sessions,
                            'selected_session': selected_session,
                            'payment_methods': [{'id': row[0], 'nama': row[1]} for row in cursor.fetchall()],
                            'current_date': get_user_date(request)
                        })
                else:
                    # Not a PROMO, check if it's a VOUCHER
                    cursor.execute('''
                        SELECT 1
                        FROM VOUCHER v
                        JOIN TR_PEMBELIAN_VOUCHER tr ON v.Kode = tr.IdVoucher
                        WHERE v.Kode = %s AND tr.IdPelanggan = %s
                    ''', (kode_diskon, user_id))
                    
                    if not cursor.fetchone():
                        messages.error(request, 'Invalid voucher or voucher not purchased by this user')
                        return render(request, 'order_form.html', {
                            'subcategory': {
                                'id': subcategory_data[0],
                                'nama_subkategori': subcategory_data[1],
                                'deskripsi': subcategory_data[2]
                            },
                            'category': {'nama_kategori': subcategory_data[3]},
                            'sessions': sessions,
                            'selected_session': selected_session,
                            'payment_methods': [{'id': row[0], 'nama': row[1]} for row in cursor.fetchall()],
                            'current_date': get_user_date(request)
                        })

            # Insert new order with the actual total_pembayaran
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
                total_pembayaran,  # Use the actual total after discount
                user_id,
                subcategory_data[0],  # SubkategoriId
                sesi,
                kode_diskon if (kode_diskon and not is_promo) else None,  # Set IdDiskon to NULL if no code or if it's a PROMO
                metode_bayar
            ))
            
            # Get the newly created order ID
            new_order_id = cursor.fetchone()[0]

            # Get status ID based on payment method
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
        messages.error(request, 'An error occurred while processing your order')
        return redirect('main:show_home_page')
        
    finally:
        cursor.close()
        connection.close()


@require_http_methods(["POST"])
def validate_discount(request):
    """
    Validates a discount code and returns the discount amount if valid
    """
    kode_diskon = request.POST.get('kode_diskon')
    total_amount = float(request.POST.get('total_amount', 0))
    
    if not kode_diskon:
        return JsonResponse({'error': 'No discount code provided'}, status=400)
        
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        return JsonResponse({'error': 'Database connection failed'}, status=500)
        
    try:
        # First check if code exists in DISKON table
        cursor.execute('''
            SELECT d.Kode, d.Potongan, d.MinTrPemesanan
            FROM DISKON d
            WHERE d.Kode = %s
        ''', (kode_diskon,))
        
        diskon = cursor.fetchone()
        if not diskon:
            return JsonResponse({'error': 'Invalid discount code'}, status=400)
            
        kode, potongan, min_transaksi = diskon
        
        # Check minimum transaction amount
        if total_amount < min_transaksi:
            return JsonResponse({
                'success': False,
                'error': f'Minimum transaction amount is Rp {min_transaksi:,.0f}',
                'min_transaksi': min_transaksi
            }, status=400)
            
        # Check if it's a PROMO
        cursor.execute('''
            SELECT TglAkhirBerlaku
            FROM PROMO
            WHERE Kode = %s
        ''', (kode_diskon,))
        
        promo = cursor.fetchone()
        if promo:
            tgl_akhir = promo[0]
            if tgl_akhir < datetime.now().date():
                return JsonResponse({'error': 'Promo has expired'}, status=400)
        else:
            # If not PROMO, check if it's a VOUCHER
            cursor.execute('''
                SELECT v.JmlHariBerlaku, v.TglPembelian, v.KuotaPenggunaan,
                       COUNT(t.IdDiskon) as used_count
                FROM VOUCHER v
                LEFT JOIN TR_PEMESANAN_JASA t ON v.Kode = t.IdDiskon
                WHERE v.Kode = %s
                GROUP BY v.Kode, v.JmlHariBerlaku, v.TglPembelian, v.KuotaPenggunaan
            ''', (kode_diskon,))
            
            voucher = cursor.fetchone()
            if not voucher:
                return JsonResponse({'error': 'Invalid voucher'}, status=400)
                
            jml_hari, tgl_pembelian, kuota, used_count = voucher
            
            # Check if voucher has expired
            expiry_date = tgl_pembelian + timedelta(days=jml_hari)
            if expiry_date < datetime.now().date():
                return JsonResponse({'error': 'Voucher has expired'}, status=400)
            
            # Check usage quota
            if used_count >= kuota:
                return JsonResponse({'error': 'Voucher usage limit reached'}, status=400)
        
        # If we get here, the discount is valid
        return JsonResponse({
            'success': True,
            'potongan': float(potongan),
            'min_transaksi': float(min_transaksi),
            'message': 'Discount applied successfully'
        })
        
    except Exception as e:
        logger.error(f"Error validating discount: {str(e)}")
        return JsonResponse({'error': 'Error validating discount'}, status=500)
        
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
                sl.harga as original_harga
            FROM TR_PEMESANAN_JASA p
            JOIN SUBKATEGORI_JASA sk ON p.idkategorijasa = sk.id
            LEFT JOIN TR_PEMESANAN_STATUS ps ON p.id = ps.idtrpemesanan
            LEFT JOIN STATUS_PEMESANAN s ON ps.idstatus = s.id
            LEFT JOIN PEKERJA w ON p.idpekerja = w.id
            LEFT JOIN "USER" u ON w.id = u.id
            LEFT JOIN SESI_LAYANAN sl ON (sk.id = sl.subkategoriid AND p.sesi = sl.sesi)
            WHERE p.idpelanggan = %s
            ORDER BY p.tglpemesanan ASC
        ''', (user_id,))
        
        orders = []
        for row in cursor.fetchall():
            total_biaya = float(row[4]) if row[4] is not None else 0
            original_harga = float(row[10]) if row[10] is not None else total_biaya
            
            # If total_biaya is less than original_harga, it means there's a discount
            is_discounted = total_biaya < original_harga
            
            orders.append({
                'id': row[0],
                'tanggal_pemesanan': row[1],
                'tanggal_pekerjaan': row[2],
                'waktu_pekerjaan': row[3],
                'harga': original_harga if is_discounted else total_biaya,  # Show original price only if discounted
                'total_pembayaran': total_biaya,  # Always show total_biaya
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


@require_http_methods(["POST"])
def cancel_order(request, order_id):
    """
    View for canceling an order
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    if not is_authenticated or not user_type or not user_id:
        messages.error(request, 'Please log in to continue')
        return redirect('main:login_user')
    
    if user_type != 'pelanggan':
        messages.error(request, 'Only customers can cancel orders')
        return redirect('main:show_home_page')

    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        messages.error(request, 'Database connection failed')
        return redirect('main:show_home_page')

    try:
        # Convert order_id to string for PostgreSQL UUID comparison
        order_id_str = str(order_id)
        
        # First verify that this order belongs to the current user
        cursor.execute('''
            SELECT id FROM TR_PEMESANAN_JASA 
            WHERE id::text = %s AND idpelanggan = %s
        ''', (order_id_str, user_id))
        
        if not cursor.fetchone():
            messages.error(request, 'Order not found or unauthorized')
            return redirect('pemesanan_jasa:show_my_orders')

        # Update the status in TR_PEMESANAN_STATUS
        current_time = timezone.now()
        
        # First, get the ID of the "Pesanan Dibatalkan" status
        cursor.execute('''
            SELECT Id FROM STATUS_PEMESANAN 
            WHERE Status = 'Pesanan Dibatalkan'
        ''')
        status_id = cursor.fetchone()
        
        if not status_id:
            # If status doesn't exist, create it
            cursor.execute('''
                INSERT INTO STATUS_PEMESANAN (Status)
                VALUES ('Pesanan Dibatalkan')
                RETURNING Id
            ''')
            status_id = cursor.fetchone()

        # Delete any existing status for this order
        cursor.execute('''
            DELETE FROM TR_PEMESANAN_STATUS
            WHERE IdTrPemesanan = %s
        ''', (order_id,))
        
        # Insert the new cancelled status
        cursor.execute('''
            INSERT INTO TR_PEMESANAN_STATUS (IdTrPemesanan, IdStatus, TglWaktu)
            VALUES (%s, %s, %s)
        ''', (order_id, status_id[0], current_time))
        
        connection.commit()
        messages.success(request, 'Order cancelled successfully')

    except Exception as e:
        logger.error(f"Error in cancel_order: {str(e)}")
        connection.rollback()
        messages.error(request, 'An error occurred while canceling your order')
    
    finally:
        cursor.close()
        connection.close()
    
    return redirect('pemesanan_jasa:show_my_orders')