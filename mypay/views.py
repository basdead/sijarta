from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest
from django.contrib import messages
from utils.query import get_db_connection
from django.utils import timezone
from zoneinfo import ZoneInfo
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_user_date(request):
    # Get timezone from request headers or default to UTC
    user_timezone_str = request.META.get('HTTP_TIMEZONE', 'UTC')
    try:
        # Get current time in UTC
        utc_now = timezone.now()
        # Convert to user's timezone
        user_time = utc_now.astimezone(ZoneInfo(user_timezone_str))
        return user_time.strftime('%d/%m/%Y')
    except Exception:
        # Fallback to UTC if there's any error
        utc_time = timezone.now()
        return utc_time.strftime('%d/%m/%Y')

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
        cursor.execute('SELECT id, nohp, saldomypay FROM "USER" WHERE id = %s', [user_id])
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'User data not found for user_id: {user_id}')
            messages.error(request, 'Data pengguna tidak ditemukan')
            return redirect('main:show_home_page')
            
        logger.info(f'User data found: id={user_data[0]}, phone={user_data[1]}, balance={user_data[2]}')
        
        # First check if there are any transactions at all
        cursor.execute('SELECT COUNT(*) FROM TR_MYPAY WHERE userid = %s', [user_id])
        count = cursor.fetchone()[0]
        logger.info(f'Total transactions found for user {user_id}: {count}')
        
        # Get user's MyPay transactions
        query = '''
            SELECT 
                m.nominal, 
                TO_CHAR(m.tgl AT TIME ZONE 'Asia/Jakarta', 'YYYY-MM-DD HH24:MI:SS') as formatted_date,
                k.nama,
                m.userid,
                m.kategoriid
            FROM TR_MYPAY m
            LEFT JOIN KATEGORI_TR_MYPAY k ON m.kategoriid = k.id
            WHERE m.userid = %s::uuid
            ORDER BY m.tgl AT TIME ZONE 'Asia/Jakarta' DESC
        '''
        logger.info(f'Executing query for user {user_id}: {query}')
        cursor.execute(query, [user_id])
        
        rows = cursor.fetchall()
        logger.info(f'Raw query results: {rows}')
        
        transactions = []
        for row in rows:
            try:
                transactions.append({
                    'nominal': float(row[0]) if row[0] is not None else 0,
                    'tanggal': datetime.strptime(row[1], '%Y-%m-%d %H:%M:%S').date() if row[1] else None,
                    'kategori': row[2],
                    'userid': row[3],
                    'kategoriid': row[4]
                })
            except Exception as e:
                logger.error(f'Error processing row {row}: {str(e)}')
        
        # Debug log to check transactions
        logger.info(f'Found {len(transactions)} transactions for user {user_id}')
        if transactions:
            logger.info(f'First transaction: {transactions[0]}')
        
        context = {
            'phone_number': user_data[1],
            'mypay_balance': user_data[2],
            'transactions': transactions
        }
        
        logger.info(f'Final context: {context}')
        
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
        # Get user's name and MyPay balance
        cursor.execute('SELECT nama, saldomypay FROM "USER" WHERE id = %s', [user_id])
        user_data = cursor.fetchone()
        
        if not user_data:
            logger.error(f'User data not found for user_id: {user_id}')
            messages.error(request, 'Data pengguna tidak ditemukan')
            return redirect('main:show_home_page')
            
        user_name = user_data[0]
        user_balance = user_data[1]

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
                {'id': 'transfer', 'nama': 'Transfer MyPay ke Pengguna Lain', 'disabled': False},
                {'id': 'withdrawal', 'nama': 'Withdrawal MyPay ke Rekening Bank', 'disabled': False}
            ]
            
            # Fetch pending orders for the user
            cursor.execute('''
                WITH LatestStatus AS (
                    SELECT 
                        idtrpemesanan,
                        idstatus,
                        ROW_NUMBER() OVER (PARTITION BY idtrpemesanan ORDER BY tglwaktu DESC) as rn
                    FROM TR_PEMESANAN_STATUS
                )
                SELECT pj.id, sj.namasubkategori, pj.sesi, pj.totalbiaya 
                FROM TR_PEMESANAN_JASA pj
                JOIN SUBKATEGORI_JASA sj ON pj.idkategorijasa = sj.id
                JOIN LatestStatus ls ON pj.id = ls.idtrpemesanan AND ls.rn = 1
                JOIN STATUS_PEMESANAN sp ON ls.idstatus = sp.id
                WHERE pj.idpelanggan = %s 
                AND sp.status = 'Menunggu Pembayaran'
                ORDER BY pj.tglpemesanan DESC
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
                {'id': 'bayar_jasa', 'nama': 'Membayar Transaksi Jasa', 'disabled': True},
                {'id': 'transfer', 'nama': 'Transfer MyPay ke Pengguna Lain', 'disabled': False},
                {'id': 'withdrawal', 'nama': 'Withdrawal MyPay ke Rekening Bank', 'disabled': False}
            ]
        else:
            logger.error(f'User {user_id} not found in either PELANGGAN or PEKERJA table')
            messages.error(request, 'Tipe pengguna tidak valid')
            
        logger.info(f'Final categories: {categories}')
            
        # Fetch payment methods for withdrawal (excluding MyPay)
        cursor.execute('''
            SELECT id, nama 
            FROM METODE_BAYAR 
            WHERE LOWER(nama) != 'mypay'
            ORDER BY nama
        ''')
        payment_methods = [
            {'id': row[0], 'nama': row[1]}
            for row in cursor.fetchall()
        ]
        logger.info(f'Fetched payment methods: {payment_methods}')
            
    except Exception as e:
        logger.error(f'Error fetching user type and categories: {str(e)}')
        messages.error(request, 'Terjadi kesalahan saat mengambil data')
    finally:
        cursor.close()
        connection.close()
    
    context = {
        'categories': categories,
        'user_type': user_type,
        'pending_orders': pending_orders,
        'user_name': user_name,
        'user_balance': user_balance,
        'current_date': get_user_date(request),
        'payment_methods': payment_methods
    }
    logger.info(f'Final context being sent to template: {context}')
    return render(request, 'transactions.html', context)

def update_transaction_form(request):
    logger.info('Received transaction form update request')
    logger.info(f'Request method: {request.method}')
    logger.info(f'POST data: {request.POST}')
    
    if not request.session.get('is_authenticated'):
        logger.warning('User not authenticated')
        messages.error(request, 'Silakan login terlebih dahulu')
        return redirect('main:login_user')
    
    user_id = request.session.get('user_id')
    logger.info(f'User ID: {user_id}')
    
    if not user_id:
        logger.error('No user ID in session')
        messages.error(request, 'Sesi login tidak valid')
        return redirect('main:login_user')
    
    if request.method != 'POST':
        logger.warning('Invalid request method')
        return HttpResponseBadRequest('Method not allowed')
    
    form_type = request.POST.get('form_type')
    logger.info(f'Form type: {form_type}')
    
    if not form_type:
        logger.warning('No form type provided')
        messages.error(request, 'Tipe form tidak valid')
        return redirect('mypay:show_transaction_page')
    
    connection, cursor = get_db_connection()
    if not connection or not cursor:
        logger.error('Database connection failed')
        messages.error(request, 'Gagal terhubung ke database')
        return redirect('mypay:show_transaction_page')
    
    try:
        if form_type == 'topup':
            nominal = request.POST.get('nominal')
            
            # Clean up the nominal string (remove 'Rp ' and '.')
            nominal = nominal.replace('Rp ', '').replace('.', '')
            nominal = int(nominal)

            try:
                # Begin transaction
                cursor.execute('BEGIN')
                
                # Update user's balance
                cursor.execute('''
                    UPDATE "USER" 
                    SET saldomypay = saldomypay + %s 
                    WHERE id = %s
                    RETURNING saldomypay
                ''', (nominal, user_id))
                
                new_balance = cursor.fetchone()[0]

                # Record transaction
                cursor.execute('''
                    INSERT INTO TR_MYPAY (
                        userid, kategoriid, nominal, tgl
                    ) VALUES (
                        %s, 
                        (SELECT id FROM KATEGORI_TR_MYPAY WHERE nama = 'Top Up MyPay'),
                        %s,
                        CURRENT_TIMESTAMP
                    )
                ''', (user_id, nominal))

                cursor.execute('COMMIT')
                messages.success(request, f'Top up berhasil. Saldo MyPay Anda sekarang Rp {new_balance:,.0f}')

            except Exception as e:
                cursor.execute('ROLLBACK')
                logger.error(f"Error in topup: {str(e)}")
                messages.error(request, 'Gagal melakukan top up')

            return redirect('mypay:show_mypay')

        elif form_type == 'bayar_jasa':
            service_id = request.POST.get('service_id')
            nominal = request.POST.get('nominal_value')
            
            # Clean up the nominal string (remove 'Rp ' and '.')
            nominal = nominal.replace('Rp ', '').replace('.', '')
            nominal = int(nominal)

            # Check if user has enough balance
            cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', (user_id,))
            current_balance = cursor.fetchone()[0]
            
            if current_balance < nominal:
                messages.error(request, 'Saldo MyPay tidak mencukupi')
                return redirect('mypay:show_transactions')

            try:
                # Begin transaction
                cursor.execute('BEGIN')

                # Update user's balance
                cursor.execute('''
                    UPDATE "USER" 
                    SET saldomypay = saldomypay - %s 
                    WHERE id = %s
                    RETURNING saldomypay
                ''', (nominal, user_id))
                
                new_balance = cursor.fetchone()[0]

                # Record transaction
                cursor.execute('''
                    INSERT INTO TR_MYPAY (
                        userid, kategoriid, nominal, tgl
                    ) VALUES (
                        %s, 
                        (SELECT id FROM KATEGORI_TR_MYPAY WHERE nama = 'Membayar Transaksi Jasa'),
                        %s,
                        CURRENT_TIMESTAMP
                    )
                ''', (user_id, nominal))

                cursor.execute('COMMIT')
                messages.success(request, f'Pembayaran berhasil. Saldo MyPay Anda sekarang Rp {new_balance:,.0f}')

            except Exception as e:
                cursor.execute('ROLLBACK')
                logger.error(f"Error in payment: {str(e)}")
                messages.error(request, 'Gagal melakukan pembayaran')

            return redirect('mypay:show_mypay')
            
        elif form_type == 'transfer':
            nomor_hp = request.POST.get('nomor-hp')
            nominal = request.POST.get('nominal')
            
            # Clean up the nominal string (remove 'Rp ' and '.')
            nominal = nominal.replace('Rp ', '').replace('.', '')
            nominal = int(nominal)

            # Get the receiver's user ID
            cursor.execute('''
                SELECT u.Id, u.SaldoMyPay
                FROM "USER" u
                WHERE u.nohp = %s
            ''', (nomor_hp,))
            
            receiver = cursor.fetchone()
            if not receiver:
                messages.error(request, 'Nomor HP tidak ditemukan')
                return redirect('mypay:show_transactions')

            receiver_id, receiver_balance = receiver

            # Check if user has enough balance
            cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', (user_id,))
            sender_balance = cursor.fetchone()[0]
            
            if sender_balance < nominal:
                messages.error(request, 'Saldo MyPay tidak mencukupi')
                return redirect('mypay:show_transactions')

            try:
                # Begin transaction
                cursor.execute('BEGIN')

                # Update sender's balance
                cursor.execute('''
                    UPDATE "USER" 
                    SET saldomypay = saldomypay - %s 
                    WHERE id = %s
                ''', (nominal, user_id))

                # Update receiver's balance
                cursor.execute('''
                    UPDATE "USER" 
                    SET saldomypay = saldomypay + %s 
                    WHERE id = %s
                ''', (nominal, receiver_id))

                # Record sender's transaction (transfer out)
                cursor.execute('''
                    INSERT INTO TR_MYPAY (
                        userid, kategoriid, nominal, tgl
                    ) VALUES (
                        %s, 
                        (SELECT id FROM KATEGORI_TR_MYPAY WHERE nama = 'Transfer MyPay ke Pengguna Lain'),
                        %s,
                        CURRENT_TIMESTAMP
                    )
                ''', (user_id, nominal))

                # Record receiver's transaction (transfer in)
                cursor.execute('''
                    INSERT INTO TR_MYPAY (
                        userid, kategoriid, nominal, tgl
                    ) VALUES (
                        %s, 
                        (SELECT id FROM KATEGORI_TR_MYPAY WHERE nama = 'Transfer MyPay ke Pengguna Lain'),
                        %s,
                        CURRENT_TIMESTAMP
                    )
                ''', (receiver_id, nominal))

                # Commit transaction
                cursor.execute('COMMIT')
                messages.success(request, f'Berhasil transfer Rp {nominal:,.0f} ke {nomor_hp}')

            except Exception as e:
                cursor.execute('ROLLBACK')
                logger.error(f"Error in transfer: {str(e)}")
                messages.error(request, 'Gagal melakukan transfer')

            return redirect('mypay:show_transactions')
        
        elif form_type == 'withdraw':
            nominal = request.POST.get('nominal')
            metode_bayar = request.POST.get('metode_bayar')
            account_number = request.POST.get('account-number')
            
            # Clean up the nominal string (remove 'Rp ' and '.')
            nominal = nominal.replace('Rp ', '').replace('.', '')
            nominal = int(nominal)

            # Check if user has enough balance
            cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', (user_id,))
            current_balance = cursor.fetchone()[0]
            
            if current_balance < nominal:
                messages.error(request, 'Saldo MyPay tidak mencukupi')
                return redirect('mypay:show_transactions')

            try:
                # Begin transaction
                cursor.execute('BEGIN')

                # Update user's balance
                cursor.execute('''
                    UPDATE "USER" 
                    SET saldomypay = saldomypay - %s 
                    WHERE id = %s
                    RETURNING saldomypay
                ''', (nominal, user_id))
                
                new_balance = cursor.fetchone()[0]

                # Record transaction
                cursor.execute('''
                    INSERT INTO TR_MYPAY (
                        userid, kategoriid, nominal, tgl
                    ) VALUES (
                        %s, 
                        (SELECT id FROM KATEGORI_TR_MYPAY WHERE nama = 'Withdrawal MyPay ke Rekening Bank'),
                        %s,
                        CURRENT_TIMESTAMP
                    )
                ''', (user_id, nominal))

                cursor.execute('COMMIT')
                messages.success(request, f'Penarikan berhasil. Saldo MyPay Anda sekarang Rp {new_balance:,.0f}. Dana akan ditransfer ke rekening {account_number}.')

            except Exception as e:
                cursor.execute('ROLLBACK')
                logger.error(f"Error in withdrawal: {str(e)}")
                messages.error(request, 'Gagal melakukan penarikan saldo')

            return redirect('mypay:show_mypay')
        
    except Exception as e:
        logger.error(f'Error in update_transaction_form: {str(e)}')
        messages.error(request, 'Terjadi kesalahan saat memproses transaksi')
    finally:
        cursor.close()
        connection.close()
    
    return redirect('mypay:show_transaction_page')
