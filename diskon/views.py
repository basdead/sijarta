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


def show_voucher_form(request, voucher_code):
    """
    View for showing voucher purchase form
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_id = request.session.get('user_id', None)
    user_type = request.session.get('user_type', None)
    
    if not is_authenticated or user_type != 'pelanggan':
        messages.error(request, 'Please log in as a customer to purchase vouchers')
        return redirect('main:login_user')
    
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed')
        messages.error(request, 'Failed to connect to database')
        return redirect('main:show_home_page')
        
    try:
        # Get selected voucher details
        cursor.execute('''
            SELECT v.kode, v.jmlhariberlaku, v.kuotapenggunaan, v.harga, d.potongan, d.mintrpemesanan
            FROM VOUCHER v
            JOIN DISKON d ON v.kode = d.kode
            WHERE v.kode = %s
        ''', [voucher_code])
        voucher_data = cursor.fetchone()
        
        if not voucher_data:
            messages.error(request, 'Voucher not found')
            return redirect('diskon:show_discount_page')
            
        voucher = {
            'kode': voucher_data[0],
            'jmlhariberlaku': voucher_data[1],
            'kuota': voucher_data[2],
            'harga': voucher_data[3],
            'potongan': voucher_data[4],
            'mintrpemesanan': voucher_data[5],
            'nama': f"{voucher_data[0]} - Rp {voucher_data[3]:,.0f}"
        }
        
        # Get user's MyPay balance
        cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', [user_id])
        user_balance = cursor.fetchone()[0]
        
        # Get payment methods
        cursor.execute('''
            SELECT id, nama 
            FROM metode_bayar 
            ORDER BY nama
        ''')
        payment_methods = [
            {'id': row[0], 'nama': row[1]} 
            for row in cursor.fetchall()
        ]
        
        context = {
            'voucher': voucher,
            'user_balance': user_balance,
            'payment_methods': payment_methods,
            'selected_voucher_code': voucher_code
        }
        
        return render(request, 'voucher_form.html', context)
        
    except Exception as e:
        logger.error(f'Error showing voucher form: {str(e)}')
        messages.error(request, 'Failed to load voucher form')
        return redirect('diskon:show_discount_page')
        
    finally:
        cursor.close()
        connection.close()


def voucher_purchase(request, voucher_code):
    """
    View for handling voucher purchase
    """
    # Check authentication
    is_authenticated = request.session.get('is_authenticated', False)
    user_id = request.session.get('user_id', None)
    user_type = request.session.get('user_type', None)
    
    if not is_authenticated or user_type != 'pelanggan':
        messages.error(request, 'Please log in as a customer to purchase vouchers')
        return redirect('main:login_user')
    
    connection, cursor = get_db_connection()
    if connection is None or cursor is None:
        logger.error('Database connection failed')
        messages.error(request, 'Failed to connect to database')
        return redirect('main:show_home_page')
        
    try:
        if request.method == 'GET':
            # Get selected voucher details
            cursor.execute('''
                SELECT v.kode, v.jmlhariberlaku, v.kuotapenggunaan, v.harga, d.potongan, d.mintrpemesanan
                FROM VOUCHER v
                JOIN DISKON d ON v.kode = d.kode
                WHERE v.kode = %s
            ''', [voucher_code])
            voucher_data = cursor.fetchone()
            
            if not voucher_data:
                messages.error(request, 'Voucher not found')
                return redirect('diskon:show_discount_page')
                
            voucher = {
                'kode': voucher_data[0],
                'jmlhariberlaku': voucher_data[1],
                'kuota': voucher_data[2],
                'harga': voucher_data[3],
                'potongan': voucher_data[4],
                'mintrpemesanan': voucher_data[5],
                'nama': f"{voucher_data[0]} - Rp {voucher_data[3]:,.0f}"
            }
            
            # Get user's MyPay balance
            cursor.execute('SELECT saldomypay FROM "USER" WHERE id = %s', [user_id])
            user_balance = cursor.fetchone()[0]
            
            # Get payment methods
            cursor.execute('''
                SELECT id, nama 
                FROM metode_bayar 
                ORDER BY nama
            ''')
            payment_methods = [
                {'id': row[0], 'nama': row[1]} 
                for row in cursor.fetchall()
            ]
            
            context = {
                'voucher': voucher,
                'user_balance': user_balance,
                'payment_methods': payment_methods
            }
            
            return render(request, 'voucher_form.html', context)
            
        elif request.method == 'POST':
            # Get customer ID
            cursor.execute('SELECT id FROM PELANGGAN WHERE id = %s', [user_id])
            customer_id = cursor.fetchone()
            
            if not customer_id:
                messages.error(request, 'Customer not found')
                return redirect('diskon:show_discount_page')
                
            customer_id = customer_id[0]
            
            # Get voucher details
            cursor.execute('''
                SELECT v.jmlhariberlaku, v.kuotapenggunaan, v.harga
                FROM VOUCHER v
                WHERE v.kode = %s
            ''', [voucher_code])
            voucher_data = cursor.fetchone()
            
            if not voucher_data:
                messages.error(request, 'Voucher not found')
                return redirect('diskon:show_discount_page')
                
            validity_days = voucher_data[0]
            usage_quota = voucher_data[1]
            price = voucher_data[2]
            
            # Get payment method
            metode_bayar = request.POST.get('metode_bayar')
            if not metode_bayar:
                messages.error(request, 'Please select a payment method')
                return redirect('diskon:voucher_purchase', voucher_code=voucher_code)
            
            # Calculate validity period
            tgl_awal = date.today()
            tgl_akhir = tgl_awal + timedelta(days=validity_days)
            
            # Get MyPay payment method ID
            cursor.execute('''
                SELECT id 
                FROM metode_bayar 
                WHERE nama = 'MyPay'
            ''')
            mypay_id = cursor.fetchone()
            
            if not mypay_id:
                messages.error(request, 'Payment method not found')
                return redirect('diskon:show_discount_page')
                
            mypay_id = mypay_id[0]
            
            # Insert into TR_PEMBELIAN_VOUCHER
            cursor.execute('''
                INSERT INTO tr_pembelian_voucher 
                (tglawal, tglakhir, telahdigunakan, idpelanggan, idvoucher, idmetodebayar)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', [tgl_awal, tgl_akhir, 0, customer_id, voucher_code, mypay_id])
            
            purchase_id = cursor.fetchone()[0]
            connection.commit()
            
            messages.success(request, f'Successfully purchased voucher {voucher_code}')
            return redirect('diskon:show_discount_page')
            
    except Exception as e:
        logger.error(f'Error in voucher purchase: {str(e)}')
        connection.rollback()
        messages.error(request, 'Failed to purchase voucher')
        return redirect('diskon:show_discount_page')
        
    finally:
        cursor.close()
        connection.close()
