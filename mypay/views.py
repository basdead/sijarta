from django.shortcuts import render, redirect
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
