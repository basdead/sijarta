from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
import json
from utils.query import get_db_connection
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Create your views here.

def show_my_works(request):
    logger.info("Accessing show_my_works view")
    if 'user_id' not in request.session:
        logger.warning("User not logged in, redirecting to login page")
        return redirect('login:show_login')
    
    try:
        connection, cursor = get_db_connection()
        if connection is None or cursor is None:
            logger.error("Database connection failed in show_my_works")
            messages.error(request, 'Koneksi database gagal')
            return redirect('main:show_home_page')

        with connection.cursor() as cursor:
            # Get worker photo
            logger.info(f"Fetching worker photo for user_id: {request.session.get('user_id')}")
            cursor.execute("""
                SELECT LinkFoto
                FROM PEKERJA p
                JOIN "USER" u ON p.Id = u.Id
                WHERE p.Id = %s
            """, [request.session.get('user_id')])
            
            worker_data = cursor.fetchone()
            if worker_data:
                request.session['foto_url'] = worker_data[0]
                logger.info("Worker photo found and set in session")
            else:
                logger.warning("No worker photo found")
            
            # Get categories and subcategories the pekerja is enrolled in
            logger.info(f"Fetching enrolled categories for pekerja {request.session.get('user_id')}")
            cursor.execute("""
                SELECT DISTINCT
                    kj.Id as category_id,
                    kj.NamaKategori as category_name,
                    skj.Id as subcategory_id,
                    skj.NamaSubkategori as subcategory_name
                FROM KATEGORI_JASA kj
                JOIN PEKERJA_KATEGORI_JASA pkj ON kj.Id = pkj.KategoriJasaId
                JOIN SUBKATEGORI_JASA skj ON skj.KategoriJasaId = kj.Id
                WHERE pkj.PekerjaId = %s
                ORDER BY kj.NamaKategori, skj.NamaSubkategori
            """, [request.session.get('user_id')])
            
            enrolled_categories_data = cursor.fetchall()
            logger.info("Raw enrolled categories data: %s", enrolled_categories_data)
            
            # Process the data into a nested structure
            enrolled_categories = []
            current_category = None
            
            for row in enrolled_categories_data:
                if not current_category or current_category['id'] != row[0]:
                    current_category = {
                        'id': row[0],
                        'nama_kategori': row[1],
                        'subcategories': []
                    }
                    enrolled_categories.append(current_category)
                
                current_category['subcategories'].append({
                    'id': row[2],
                    'nama_subkategori': row[3]
                })

            logger.info("Processed categories structure: %s", enrolled_categories)

            # Fetch pending orders
            logger.info("Fetching pending orders...")
            cursor.execute("""
                WITH LatestStatus AS (
                    SELECT 
                        IdTrPemesanan,
                        IdStatus,
                        TglWaktu,
                        ROW_NUMBER() OVER (PARTITION BY IdTrPemesanan ORDER BY TglWaktu DESC) as rn
                    FROM TR_PEMESANAN_STATUS
                )
                SELECT DISTINCT
                    pj.Id,
                    skj.NamaSubkategori,
                    sl.Sesi as namasesi,
                    pj.TglPemesanan,
                    u.Nama as nama_lengkap,
                    pj.TotalBiaya,
                    kj.Id as category_id,
                    pj.IdKategoriJasa as subcategory_id,
                    kj.NamaKategori,
                    sp.Status,
                    pj.IdPekerja
                FROM TR_PEMESANAN_JASA pj
                JOIN SUBKATEGORI_JASA skj ON pj.IdKategoriJasa = skj.Id
                JOIN KATEGORI_JASA kj ON skj.KategoriJasaId = kj.Id
                JOIN SESI_LAYANAN sl ON sl.SubkategoriId = skj.Id AND sl.Sesi = pj.Sesi
                JOIN "USER" u ON pj.IdPelanggan = u.Id
                JOIN PEKERJA_KATEGORI_JASA pkj ON kj.Id = pkj.KategoriJasaId
                JOIN LatestStatus ls ON pj.Id = ls.IdTrPemesanan AND ls.rn = 1
                JOIN STATUS_PEMESANAN sp ON ls.IdStatus = sp.Id
                WHERE pkj.PekerjaId = %s
                AND sp.Status = 'Mencari Pekerja Terdekat'
                AND pj.IdPekerja IS NULL
                ORDER BY pj.TglPemesanan ASC
            """, [request.session.get('user_id')])
            
            orders_data = cursor.fetchall()
            logger.info("Raw orders data: %s", orders_data)

            orders = []
            for order in orders_data:
                order_dict = {
                    'id': order[0],
                    'subcategory': order[1],
                    'session': order[2],
                    'date': order[3].strftime('%d/%m/%Y') if order[3] else '',  # TglPemesanan
                    'customer_name': order[4],
                    'price': order[5],
                    'category_id': str(order[6]),
                    'subcategory_id': str(order[7]),
                    'category_name': order[8],
                    'status': order[9],
                    'worker_id': order[10]
                }
                orders.append(order_dict)
                logger.info("Processed order: %s", order_dict)

            # Fetch all available statuses
            cursor.execute("""
                SELECT Id, Status
                FROM STATUS_PEMESANAN
                ORDER BY Status
            """)
            
            all_statuses = [{'id': status[0], 'status': status[1]} for status in cursor.fetchall()]
            
            context = {
                'orders': orders,
                'categories': enrolled_categories,
                'all_statuses': all_statuses,
            }
            logger.info("Final context: %s", context)

            navbar_attributes = {
                'foto_url': request.session.get('foto_url', ''),
                'user_name': request.session.get('user_name', ''),
                'user_type': request.session.get('user_type', ''),
                'is_authenticated': request.session.get('is_authenticated', False),
            }

            context['navbar_attributes'] = navbar_attributes
            
            return render(request, 'my_works.html', context)
    
    except Exception as e:
        logger.error(f"Error in show_my_works: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('main:show_home_page')
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            logger.info("Database connection closed")

def accept_work(request):
    logger.info("Accessing accept_work view")
    
    if 'user_id' not in request.session:
        logger.warning("User not logged in")
        return JsonResponse({'status': 'error', 'message': 'User not logged in'})
    
    if request.method != 'POST':
        logger.warning("Invalid request method for accept_work: %s", request.method)
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        waktu_pekerjaan = data.get('waktu_pekerjaan')  # Format: "17.11"
        tanggal_pekerjaan = data.get('tanggal_pekerjaan')  # Format: "09/12/2024"
        
        logger.info("Received work acceptance request - Order ID: %s, Time: %s, Date: %s", 
                   order_id, waktu_pekerjaan, tanggal_pekerjaan)
        
        if not all([order_id, waktu_pekerjaan, tanggal_pekerjaan]):
            logger.error("Missing required fields - Order ID: %s, Time: %s, Date: %s", 
                        order_id, waktu_pekerjaan, tanggal_pekerjaan)
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
            
        connection, cursor = get_db_connection()
        if connection is None or cursor is None:
            logger.error("Database connection failed in accept_work")
            return JsonResponse({'status': 'error', 'message': 'Database connection failed'})
        
        with connection.cursor() as cursor:
            # Check if order exists and is available
            logger.info("Checking order availability - Order ID: %s, Worker ID: %s", 
                       order_id, request.session.get('user_id'))
            cursor.execute("""
                SELECT pj.Id 
                FROM TR_PEMESANAN_JASA pj
                JOIN SESI_LAYANAN sl ON pj.Sesi = sl.Sesi
                JOIN SUBKATEGORI_JASA skj ON sl.SubkategoriId = skj.Id
                JOIN KATEGORI_JASA kj ON skj.KategoriJasaId = kj.Id
                JOIN "USER" u ON pj.IdPelanggan = u.Id
                JOIN PEKERJA_KATEGORI_JASA pkj ON kj.Id = pkj.KategoriJasaId
                JOIN TR_PEMESANAN_STATUS tps ON pj.Id = tps.IdTrPemesanan
                JOIN STATUS_PEMESANAN sp ON tps.IdStatus = sp.Id
                WHERE pj.Id = %s 
                AND sp.Status = 'Mencari Pekerja Terdekat'
                AND pkj.PekerjaId = %s
            """, [order_id, request.session.get('user_id')])
            
            if not cursor.fetchone():
                logger.warning("Order not found or not available - Order ID: %s", order_id)
                return JsonResponse({
                    'status': 'error',
                    'message': 'Order not found or not available'
                })
            
            # Update order status to "Menunggu Pekerja Berangkat" and assign worker
            logger.info("Updating order status and assigning worker - Order ID: %s, Worker ID: %s", 
                       order_id, request.session.get('user_id'))
            try:
                # First check available statuses
                cursor.execute("SELECT Id, Status FROM STATUS_PEMESANAN")
                available_statuses = cursor.fetchall()
                logger.info("Available statuses: %s", available_statuses)
                
                # Get the status ID
                cursor.execute("""
                    SELECT Id FROM STATUS_PEMESANAN 
                    WHERE Status = 'Menunggu Pekerja Berangkat'
                """)
                status_result = cursor.fetchone()
                if not status_result:
                    logger.error("Status 'Menunggu Pekerja Berangkat' not found in STATUS_PEMESANAN")
                    return JsonResponse({
                        'status': 'error',
                        'message': 'Required status not found in database'
                    })
                
                new_status_id = status_result[0]
                logger.info("Found status ID: %s", new_status_id)
                
                # Insert new status record with timestamp
                cursor.execute("""
                    INSERT INTO TR_PEMESANAN_STATUS (IdTrPemesanan, IdStatus, TglWaktu)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                """, [order_id, new_status_id])
                
                # Update the worker assignment
                cursor.execute("""
                    UPDATE TR_PEMESANAN_JASA 
                    SET IdPekerja = %s,
                        WaktuPekerjaan = (CURRENT_DATE + %s::TIME),
                        TglPekerjaan = TO_DATE(%s, 'DD/MM/YYYY')
                    WHERE Id = %s
                """, [request.session.get('user_id'), waktu_pekerjaan, tanggal_pekerjaan, order_id])
                
                connection.commit()
                logger.info("Successfully updated order - Order ID: %s", order_id)
            except Exception as e:
                logger.error("Error updating order - Order ID: %s, Error: %s", order_id, str(e))
                connection.rollback()
                raise
            
        return JsonResponse({
            'status': 'success',
            'message': 'Work accepted successfully'
        })
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON data received in accept_work")
        return JsonResponse({
            'status': 'error',
            'message': 'Invalid JSON data'
        })
    except Exception as e:
        logger.error("Unexpected error in accept_work: %s", str(e))
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            logger.info("Database connection closed")

def show_work_status(request):
    logger.info("Accessing show_work_status view")
    if 'user_id' not in request.session:
        logger.warning("User not logged in, redirecting to login page")
        return redirect('login:show_login')
    
    try:
        connection, cursor = get_db_connection()
        if connection is None or cursor is None:
            logger.error("Database connection failed in show_work_status")
            messages.error(request, 'Koneksi database gagal')
            return redirect('main:show_home_page')

        with connection.cursor() as cursor:
            # Get worker photo
            logger.info(f"Fetching worker photo for user_id: {request.session.get('user_id')}")
            cursor.execute("""
                SELECT LinkFoto
                FROM PEKERJA p
                JOIN "USER" u ON p.Id = u.Id
                WHERE p.Id = %s
            """, [request.session.get('user_id')])
            
            worker_data = cursor.fetchone()
            if worker_data:
                request.session['foto_url'] = worker_data[0]
                logger.info("Worker photo found and set in session")
            else:
                logger.warning("No worker photo found")
            
            # Get categories and subcategories the pekerja is enrolled in
            logger.info(f"Fetching enrolled categories for pekerja {request.session.get('user_id')}")
            cursor.execute("""
                SELECT DISTINCT
                    kj.Id as category_id,
                    kj.NamaKategori as category_name,
                    skj.Id as subcategory_id,
                    skj.NamaSubkategori as subcategory_name
                FROM KATEGORI_JASA kj
                JOIN PEKERJA_KATEGORI_JASA pkj ON kj.Id = pkj.KategoriJasaId
                JOIN SUBKATEGORI_JASA skj ON skj.KategoriJasaId = kj.Id
                WHERE pkj.PekerjaId = %s
                ORDER BY kj.NamaKategori, skj.NamaSubkategori
            """, [request.session.get('user_id')])
            
            enrolled_categories_data = cursor.fetchall()
            
            # Process the data into a nested structure
            enrolled_categories = []
            current_category = None
            
            for row in enrolled_categories_data:
                if not current_category or current_category['id'] != row[0]:
                    current_category = {
                        'id': row[0],
                        'nama_kategori': row[1],
                        'subcategories': []
                    }
                    enrolled_categories.append(current_category)
                
                current_category['subcategories'].append({
                    'id': row[2],
                    'nama_subkategori': row[3]
                })

            logger.info("Processed categories structure: %s", enrolled_categories)

            # Fetch orders with their status
            logger.info("Fetching orders with status...")
            cursor.execute("""
                WITH LatestStatus AS (
                    SELECT 
                        IdTrPemesanan,
                        MAX(TglWaktu) as LastUpdate
                    FROM TR_PEMESANAN_STATUS
                    GROUP BY IdTrPemesanan
                )
                SELECT DISTINCT
                    pj.Id,
                    skj.NamaSubkategori,
                    sl.Sesi as namasesi,
                    pj.TglPekerjaan,
                    pj.WaktuPekerjaan,
                    u.Nama as nama_lengkap,
                    pj.TotalBiaya,
                    kj.Id as category_id,
                    pj.IdKategoriJasa as subcategory_id,
                    kj.NamaKategori,
                    sp.Status,
                    pj.IdPekerja
                FROM TR_PEMESANAN_JASA pj
                JOIN SUBKATEGORI_JASA skj ON pj.IdKategoriJasa = skj.Id
                JOIN KATEGORI_JASA kj ON skj.KategoriJasaId = kj.Id
                JOIN SESI_LAYANAN sl ON sl.SubkategoriId = skj.Id AND sl.Sesi = pj.Sesi
                JOIN "USER" u ON pj.IdPelanggan = u.Id
                JOIN TR_PEMESANAN_STATUS tps ON pj.Id = tps.IdTrPemesanan
                JOIN LatestStatus ls ON tps.IdTrPemesanan = ls.IdTrPemesanan AND tps.TglWaktu = ls.LastUpdate
                JOIN STATUS_PEMESANAN sp ON tps.IdStatus = sp.Id
                WHERE pj.IdPekerja = %s
                ORDER BY pj.TglPekerjaan ASC
            """, [request.session.get('user_id')])
            
            orders_data = cursor.fetchall()
            logger.info("Raw orders data: %s", orders_data)

            orders = []
            for order in orders_data:
                # Calculate end date by adding session days to TglPekerjaan
                work_date = order[3]  # TglPekerjaan
                session_days = order[2]  # namasesi (number of days)
                if work_date:
                    # Add session days to work date
                    end_date = work_date + timedelta(days=session_days)
                    date_display = f"{work_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"
                else:
                    date_display = ''

                order_dict = {
                    'id': order[0],
                    'subcategory': order[1],
                    'session': order[2],
                    'date': date_display,  # Show date range
                    'customer_name': order[5],
                    'price': order[6],
                    'category_id': str(order[7]),
                    'subcategory_id': str(order[8]),
                    'category_name': order[9],
                    'status': order[10],
                    'worker_id': order[11]
                }
                orders.append(order_dict)
                logger.info("Processed order: %s", order_dict)

            # Fetch all available statuses
            cursor.execute("""
                SELECT Id, Status
                FROM STATUS_PEMESANAN
                ORDER BY Status
            """)
            
            all_statuses = [{'id': status[0], 'status': status[1]} for status in cursor.fetchall()]
            
            context = {
                'orders': orders,
                'categories': enrolled_categories,
                'all_statuses': all_statuses,
            }
            logger.info("Final context: %s", context)

            navbar_attributes = {
                'foto_url': request.session.get('foto_url', ''),
                'user_name': request.session.get('user_name', ''),
                'user_type': request.session.get('user_type', ''),
                'is_authenticated': request.session.get('is_authenticated', False),
            }

            context['navbar_attributes'] = navbar_attributes
            
            return render(request, 'work_status.html', context)
    
    except Exception as e:
        logger.error(f"Error in show_work_status: {str(e)}")
        messages.error(request, f'Terjadi kesalahan: {str(e)}')
        return redirect('main:show_home_page')
    finally:
        if 'connection' in locals() and connection:
            connection.close()
            logger.info("Database connection closed")

@require_http_methods(["POST"])
def update_status(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('order_id')
        new_status = data.get('new_status')

        if not all([order_id, new_status]):
            return JsonResponse({'status': 'error', 'message': 'Missing required fields'})

        connection, cursor = get_db_connection()
        if connection is None or cursor is None:
            return JsonResponse({'status': 'error', 'message': 'Database connection failed'})

        try:
            # Get the status ID for the new status
            cursor.execute("""
                SELECT Id FROM STATUS_PEMESANAN WHERE Status = %s
            """, [new_status])
            status_result = cursor.fetchone()
            
            if not status_result:
                return JsonResponse({'status': 'error', 'message': 'Invalid status'})
            
            new_status_id = status_result[0]
            
            # Insert the new status
            cursor.execute("""
                INSERT INTO TR_PEMESANAN_STATUS (IdTrPemesanan, IdStatus, TglWaktu)
                VALUES (%s, %s, CURRENT_TIMESTAMP)
            """, [order_id, new_status_id])

            # If status is "Pesanan selesai", increment the worker's completed orders count
            if new_status == 'Pesanan selesai':
                cursor.execute("""
                    UPDATE PEKERJA p
                    SET jmlpesananselesai = COALESCE(jmlpesananselesai, 0) + 1
                    FROM TR_PEMESANAN_JASA pj
                    WHERE p.Id = pj.IdPekerja AND pj.Id = %s
                """, [order_id])
            
            connection.commit()
            return JsonResponse({'status': 'success'})
            
        finally:
            cursor.close()
            connection.close()
            
    except Exception as e:
        logger.error(f"Error updating status: {str(e)}")
        return JsonResponse({'status': 'error', 'message': str(e)})
