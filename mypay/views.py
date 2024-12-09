from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.contrib import messages
from utils.query import get_db_connection
import logging

logger = logging.getLogger(__name__)

def show_mypay(request):
    # Check if user is authenticated
    if not request.session.get('is_authenticated'):
        logger.warning('Unauthenticated user tried to access MyPay')
        messages.error(request, 'Silakan login terlebih dahulu untuk mengakses MyPay')
        return redirect('main:login_user')
    
    user_id = request.session.get('user_id')
    if not user_id:
        logger.error('No user_id in session for authenticated user')
        messages.error(request, 'Sesi login tidak valid. Silakan login kembali')
        return redirect('main:login_user')
    
    # Get user data from database
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed')
        messages.error(request, 'Gagal terhubung ke database')
        return redirect('main:show_home_page')
    
    try:
        # Get user's phone number and MyPay balance
        cursor.execute('SELECT nohp, saldomypay FROM "USER" WHERE id = %s', [user_id])
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'User data not found for user_id: {user_id}')
            messages.error(request, 'Data pengguna tidak ditemukan')
            return redirect('main:show_home_page')
        
        # Get user's MyPay transactions
        cursor.execute('''
            SELECT m.nominal, m.tgl, k.nama 
            FROM TR_MYPAY m
            JOIN KATEGORI_TR_MYPAY k ON m.kategoriid = k.id
            WHERE m.userid = %s
            ORDER BY m.tgl DESC, m.id DESC
        ''', [user_id])
        
        transactions = [
            {
                'nominal': row[0],
                'tanggal': row[1],
                'kategori': row[2]
            }
            for row in cursor.fetchall()
        ]
        
        context = {
            'phone_number': user_data[0],
            'mypay_balance': user_data[1],
            'transactions': transactions
        }
        
        return render(request, "mypay.html", context)
        
    except Exception as e:
        logger.error(f'Error in show_mypay: {str(e)}')
        messages.error(request, 'Terjadi kesalahan saat memuat data MyPay')
        return redirect('main:show_home_page')
        
    finally:
        cursor.close()
        connection.close()

def show_transaction_page(request):
    # Debug: Print session info
    logger.info(f"Session data: {request.session.items()}")
    
    if not request.session.get('is_authenticated'):
        logger.warning('Unauthenticated user tried to access transactions page')
        messages.error(request, 'Silakan login terlebih dahulu untuk mengakses halaman transaksi')
        return redirect('main:login_user')
    
    user_id = request.session.get('user_id')
    logger.info(f"User ID from session: {user_id}")
    
    if not user_id:
        logger.error('No user_id in session for authenticated user')
        messages.error(request, 'Sesi login tidak valid. Silakan login kembali')
        return redirect('main:login_user')
    
    # Initialize default values
    categories = []
    user_type = None
    pending_orders = []
    
    # Get user type from database
    connection, cursor = get_db_connection()
    if not connection or not cursor:
        logger.error('Failed to connect to database')
        messages.error(request, 'Gagal terhubung ke database')
        return render(request, 'transactions.html', {'categories': categories, 'user_type': user_type})
    
    try:
        # Check if user is in PELANGGAN table
        cursor.execute('SELECT 1 FROM PELANGGAN WHERE id = %s', (user_id,))
        is_pelanggan = cursor.fetchone() is not None
        
        # Check if user is in PEKERJA table
        cursor.execute('SELECT 1 FROM PEKERJA WHERE id = %s', (user_id,))
        is_pekerja = cursor.fetchone() is not None
        
        if is_pelanggan:
            user_type = 'Pengguna'
            logger.info('User identified as Pengguna')
            categories = [
                {'id': 'topup', 'nama': 'Top Up MyPay', 'disabled': False},
                {'id': 'bayar_jasa', 'nama': 'Membayar Transaksi Jasa', 'disabled': False},
                {'id': 'withdrawal', 'nama': 'Withdrawal MyPay ke Rekening Bank', 'disabled': False},
                {'id': 'transfer', 'nama': 'Transfer MyPay ke Pengguna Lain', 'disabled': False}
            ]
            
            # Fetch pending orders for the user
            cursor.execute('''
                SELECT pj.id, sj.namasubkategori, pj.sesi, pj.totalbiaya 
                FROM TR_PEMESANAN_JASA pj
                JOIN SUBKATEGORI_JASA sj ON pj.idkategorijasa = sj.id
                JOIN TR_PEMESANAN_STATUS tps ON pj.id = tps.idtrpemesanan
                JOIN STATUS_PEMESANAN sp ON tps.idstatus = sp.id
                WHERE pj.idpelanggan = %s 
                AND sp.status = 'Menunggu Pembayaran'
                AND tps.tglwaktu = (
                    SELECT MAX(tglwaktu)
                    FROM TR_PEMESANAN_STATUS
                    WHERE idtrpemesanan = pj.id
                )
                ORDER BY pj.id DESC
            ''', [user_id])
            
            pending_orders = [
                {
                    'id': row[0],
                    'subkategori': row[1],
                    'sesi': f'Sesi {row[2]}',
                    'totalharga': row[3]
                }
                for row in cursor.fetchall()
            ]
            logger.info(f'Fetched pending orders: {pending_orders}')
            
        elif is_pekerja:
            user_type = 'Pekerja'
            logger.info('User identified as Pekerja')
            categories = [
                {'id': 'topup', 'nama': 'Top Up MyPay', 'disabled': False},
                {'id': 'withdrawal', 'nama': 'Withdrawal MyPay ke Rekening Bank', 'disabled': False},
                {'id': 'transfer', 'nama': 'Transfer MyPay ke Pengguna Lain', 'disabled': False},
                {'id': 'terima_honor', 'nama': 'Menerima Honor Transaksi Jasa', 'disabled': True}
            ]
        else:
            logger.error(f'User {user_id} not found in either PELANGGAN or PEKERJA table')
            messages.error(request, 'Tipe pengguna tidak valid')
            
        logger.info(f'Final categories: {categories}')
            
    except Exception as e:
        logger.error(f'Error fetching user type and categories: {str(e)}')
        messages.error(request, 'Terjadi kesalahan saat mengambil data')
    finally:
        cursor.close()
        connection.close()
    
    context = {
        'categories': categories,
        'user_type': user_type,
        'pending_orders': pending_orders
    }
    logger.info(f'Final context being sent to template: {context}')
    return render(request, 'transactions.html', context)

def update_transaction_form(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        context = {'selected_category': category}
        return render(request, 'transaction_form_partial.html', context)
    return HttpResponseBadRequest()
