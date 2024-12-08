from django.shortcuts import render, redirect
from django.contrib import messages
from utils.query import get_db_connection
import logging

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
