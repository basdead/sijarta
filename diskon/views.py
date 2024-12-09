from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from utils.query import get_db_connection
import logging
from datetime import date, timedelta

logger = logging.getLogger(__name__)

def show_discount_page(request):
    """
    View for showing available discounts
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    
    if not is_authenticated or user_type != 'pelanggan':
        messages.error(request, 'Please log in as a customer to view discounts')
        return redirect('main:login_user')
    
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed')
        messages.error(request, 'Failed to connect to database')
        return redirect('main:show_home_page')
        
    try:
        # Fetch vouchers with their discount details
        voucher_query = '''
            SELECT v.Kode, v.JmlHariBerlaku, v.KuotaPenggunaan, v.Harga, d.Potongan, d.MinTrPemesanan
            FROM VOUCHER v
            JOIN DISKON d ON v.Kode = d.Kode
        '''
        cursor.execute(voucher_query)
        vouchers = []
        for row in cursor.fetchall():
            vouchers.append({
                'kode': row[0],
                'jmlhariberlaku': row[1],
                'kuota': row[2],
                'harga': row[3],
                'potongan': row[4],
                'mintrpemesanan': row[5],
                'description': f"Berlaku {row[1]} hari, min. transaksi Rp {row[5]:,.0f}"
            })
            
        # Fetch promos with their discount details
        promo_query = '''
            SELECT p.Kode, p.TglAkhirBerlaku, d.Potongan, d.MinTrPemesanan
            FROM PROMO p
            JOIN DISKON d ON p.Kode = d.Kode
            WHERE p.TglAkhirBerlaku >= CURRENT_DATE
        '''
        cursor.execute(promo_query)
        promos = []
        for row in cursor.fetchall():
            promos.append({
                'kode': row[0],
                'tglakhirberlaku': row[1],
                'potongan': row[2],
                'mintrpemesanan': row[3],
                'description': f"Berlaku sampai {row[1]}, min. transaksi Rp {row[3]:,.0f}"
            })
            
        # Split items into rows of 3
        voucher_rows = [vouchers[i:i+3] for i in range(0, len(vouchers), 3)]
        promo_rows = [promos[i:i+3] for i in range(0, len(promos), 3)]
        
        context = {
            'voucher_rows': voucher_rows,
            'promo_rows': promo_rows,
        }
        
        return render(request, 'diskon.html', context)
        
    except Exception as error:
        logger.error(f'Error fetching discounts: {str(error)}')
        messages.error(request, 'Failed to load discounts')
        return redirect('main:show_home_page')
    finally:
        cursor.close()
        connection.close()


def voucher_purchase(request, voucher_code):
    """
    View for handling voucher purchase
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_type = request.session.get('user_type', None)
    user_id = request.session.get('user_id', None)
    
    if not is_authenticated or user_type != 'pelanggan':
        messages.error(request, 'Please log in as a customer to purchase vouchers')
        return redirect('main:login_user')
    
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed')
        messages.error(request, 'Failed to connect to database')
        return redirect('main:show_home_page')
        
    try:
        if request.method == 'POST':
            voucher_id = request.POST.get('voucher_id')
            metode_bayar = request.POST.get('metode_bayar')
            
            if not all([voucher_id, metode_bayar]):
                messages.error(request, 'Please fill in all fields')
                return redirect('diskon:voucher_purchase', voucher_code=voucher_code)
            
            # Get voucher details
            cursor.execute("""
                SELECT v.Kode, v.Harga, v.KuotaPenggunaan, v.JmlHariBerlaku, d.Potongan
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE v.Kode = %s
            """, [voucher_id])
            voucher = cursor.fetchone()
            
            if not voucher:
                messages.error(request, 'Invalid voucher')
                return redirect('diskon:voucher_purchase', voucher_code=voucher_code)
            
            # For MyPay, check balance
            if metode_bayar == 'mypay':
                cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', [user_id])
                user_balance = cursor.fetchone()[0]
                
                if user_balance < voucher[1]:  # voucher[1] is the price
                    messages.error(request, 'Maaf, saldo Anda tidak cukup untuk membeli voucher ini.')
                    return redirect('diskon:voucher_purchase', voucher_code=voucher_code)
            
            # Begin transaction
            cursor.execute('BEGIN')
            try:
                if metode_bayar == 'mypay':
                    # Deduct balance from user's MyPay
                    cursor.execute("""
                        UPDATE "USER"
                        SET saldomypay = saldomypay - %s
                        WHERE id = %s
                    """, [voucher[1], user_id])
                
                # Store voucher in session
                if 'purchased_vouchers' not in request.session:
                    request.session['purchased_vouchers'] = []
                
                purchased_voucher = {
                    'kode': voucher[0],
                    'tgl_beli': date.today().strftime('%Y-%m-%d'),
                    'jml_pemakaian': 0
                }
                request.session['purchased_vouchers'].append(purchased_voucher)
                request.session.modified = True
                
                cursor.execute('COMMIT')
                
                # Calculate expiry date
                expiry_date = (date.today() + timedelta(days=voucher[3])).strftime('%d/%m/%Y')
                
                messages.success(request, f'Selamat! Anda berhasil membeli voucher kode {voucher[0]}. Voucher ini akan berlaku hingga tanggal {expiry_date} dengan kuota penggunaan sebanyak {voucher[2]} kali.')
                return redirect('diskon:show_discount_page')
                
            except Exception as e:
                cursor.execute('ROLLBACK')
                logger.error(f'Error during voucher purchase transaction: {str(e)}')
                messages.error(request, 'Failed to process purchase')
                return redirect('diskon:voucher_purchase', voucher_code=voucher_code)
        
        else:  # GET request - show purchase form
            # Get selected voucher details
            cursor.execute("""
                SELECT v.Kode, v.JmlHariBerlaku, v.KuotaPenggunaan, v.Harga, d.Potongan, d.MinTrPemesanan
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
                WHERE v.Kode = %s
            """, [voucher_code])
            selected_voucher = cursor.fetchone()
            
            if not selected_voucher:
                messages.error(request, 'Invalid voucher code')
                return redirect('diskon:show_discount_page')
            
            # Get all vouchers for dropdown
            cursor.execute("""
                SELECT v.Kode, v.JmlHariBerlaku, v.KuotaPenggunaan, v.Harga, d.Potongan, d.MinTrPemesanan
                FROM VOUCHER v
                JOIN DISKON d ON v.Kode = d.Kode
            """)
            vouchers = []
            for row in cursor.fetchall():
                vouchers.append({
                    'id': row[0],
                    'nama': f"{row[0]} - Rp {row[3]:,.0f}".replace(',', '.'),
                    'harga': row[3],
                    'potongan': row[4],
                    'min_pemesanan': row[5]
                })
            
            # Get user's MyPay balance
            cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', [user_id])
            user_balance = cursor.fetchone()[0]
            
            # Get all payment methods
            cursor.execute("""
                SELECT id, nama
                FROM METODE_BAYAR
                ORDER BY nama
            """)
            payment_methods = [
                {'id': row[0], 'nama': row[1]} 
                for row in cursor.fetchall()
            ]
            
            context = {
                'vouchers': vouchers,
                'selected_voucher_code': voucher_code,
                'user_balance': user_balance,
                'payment_methods': payment_methods
            }
            
            return render(request, 'voucher_form.html', context)
            
    except Exception as error:
        logger.error(f'Error in voucher purchase: {str(error)}')
        messages.error(request, 'An error occurred')
        return redirect('diskon:show_discount_page')
    finally:
        cursor.close()
        connection.close()
