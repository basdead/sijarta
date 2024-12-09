from django.shortcuts import render, get_object_or_404, redirect
from utils.query import get_db_connection
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def show_subcategory(request, subcategory_name):
    """
    View for showing subcategory details
    """
    logger.info(f"Raw subcategory_name from URL: {subcategory_name!r}")
    
    # Decode URL-encoded name
    subcategory_name = unquote(subcategory_name)
    logger.info(f"After unquote: {subcategory_name!r}")
    
    # First remove any existing spaces
    subcategory_name = subcategory_name.replace(' ', '')
    
    # Add space before 'AC' if it exists and isn't at the start
    if 'AC' in subcategory_name and not subcategory_name.startswith('AC'):
        subcategory_name = subcategory_name.replace('AC', ' AC')
    
    # Add spaces before other capital letters (except first letter and 'AC')
    result = []
    i = 0
    while i < len(subcategory_name):
        # Skip over 'AC' if we find it
        if i < len(subcategory_name) - 1 and subcategory_name[i:i+2] == 'AC':
            result.append(subcategory_name[i:i+2])
            i += 2
            continue
            
        # Add space before capitals (except first letter)
        if i > 0 and subcategory_name[i].isupper():
            result.append(' ')
        result.append(subcategory_name[i])
        i += 1
    
    subcategory_name = ''.join(result)
    logger.info(f"After processing: {subcategory_name!r}")
    
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            logger.error("Could not establish database connection")
            return redirect('main:show_home_page')
        
        # First get the subcategory ID
        cur.execute("""
            SELECT id, namasubkategori, deskripsi, kategorijasaid
            FROM SUBKATEGORI_JASA
            WHERE namasubkategori = %s
        """, [subcategory_name])
        
        subcategory_result = cur.fetchone()
        logger.info(f"Subcategory query result: {subcategory_result!r}")
        
        if not subcategory_result:
            logger.warning(f"Subcategory not found: {subcategory_name!r}")
            cur.close()
            conn.close()
            return redirect('main:show_home_page')

        subcategory_id = subcategory_result[0]
        if subcategory_id is None:
            logger.error("Subcategory ID is None")
            cur.close()
            conn.close()
            return redirect('main:show_home_page')
        
        # Now get the category info
        cur.execute("""
            SELECT namakategori, id
            FROM KATEGORI_JASA
            WHERE id = %s
        """, [subcategory_result[3]])
        
        category_result = cur.fetchone()
        logger.info(f"Category query result: {category_result!r}")
        
        if not category_result:
            logger.error("Category not found")
            cur.close()
            conn.close()
            return redirect('main:show_home_page')
        
        subcategory = {
            'nama_subkategori': subcategory_result[1],
            'deskripsi': subcategory_result[2]
        }
        
        category = {
            'nama_kategori': category_result[0],
            'id_kategori': category_result[1]
        }
        
        # Fetch sesi_layanan using subcategory ID
        cur.execute("""
            SELECT COALESCE(sesi, 0) as sesi, COALESCE(harga, 0.0) as harga
            FROM SESI_LAYANAN
            WHERE subkategoriid = %s
            ORDER BY sesi
        """, [subcategory_id])
        
        raw_sessions = cur.fetchall()
        logger.info(f"Session query result: {raw_sessions!r}")
        
        sessions = []
        for row in raw_sessions:
            try:
                sesi, harga = row
                logger.info(f"Processing session - sesi: {sesi!r}, harga: {harga!r}")
                
                # Convert to appropriate types with defaults
                sesi_val = int(sesi) if sesi is not None else 0
                harga_val = float(harga) if harga is not None else 0.0
                
                sessions.append({
                    'sesi': sesi_val,
                    'harga': harga_val
                })
            except (TypeError, ValueError) as e:
                logger.error(f"Error processing session {row!r}: {str(e)}")
                continue
        
        logger.info(f"Final sessions list: {sessions!r}")
        
        # Fetch enrolled pekerja for this subcategory
        cur.execute("""
            SELECT DISTINCT u.nama, p.linkfoto
            FROM PEKERJA p
            JOIN "USER" u ON p.id = u.id
            JOIN PEKERJA_KATEGORI_JASA pk ON p.id = pk.pekerjaid
            JOIN KATEGORI_JASA k ON pk.kategorijasaid = k.id
            JOIN SUBKATEGORI_JASA s ON s.kategorijasaid = k.id
            WHERE s.namasubkategori = %s
            ORDER BY u.nama
        """, [subcategory_name])
        
        enrolled_workers = [
            {'nama': row[0], 'foto_url': row[1]} 
            for row in cur.fetchall()
        ]
        
        # Fetch testimonials for this subcategory
        cur.execute("""
            SELECT t.tgl, t.teks, t.rating, u.nama
            FROM TESTIMONI t
            JOIN TR_PEMESANAN_JASA tp ON t.idtrpemesanan = tp.id
            JOIN PELANGGAN p ON tp.idpelanggan = p.id
            JOIN "USER" u ON p.id = u.id
            JOIN SUBKATEGORI_JASA sj ON tp.idkategorijasa = sj.id
            WHERE sj.id = %s
            ORDER BY t.tgl DESC
        """, [subcategory_id])
        
        testimonials = []
        for row in cur.fetchall():
            testimonials.append({
                'tanggal': row[0],
                'komentar': row[1],
                'rating': row[2],
                'nama_pelanggan': row[3]
            })
        
        # Calculate star rating (convert 10-point to 5-star)
        for testimoni in testimonials:
            testimoni['star_rating'] = float(testimoni['rating']) / 2
        
        logger.info(f"Testimonials found: {len(testimonials)}")
        
        cur.close()
        conn.close()
        
        # Get logged-in user's data for navbar
        conn, cur = get_db_connection()
        if conn and cur:
            cur.execute('SELECT linkfoto FROM PEKERJA WHERE id = %s', (request.session.get('user_id'),))
            navbar_data = cur.fetchone()
            navbar_attributes = {}
            if request.session.get('user_type') == 'pekerja' and navbar_data:
                navbar_attributes['foto_url'] = navbar_data[0]

            context = {
                'subcategory': subcategory,
                'category': category,
                'sessions': sessions,
                'enrolled_workers': enrolled_workers,
                'testimonials': testimonials,
                'navbar_attributes': navbar_attributes  # Add navbar data to context
            }
            
            # Add profile photo URL and enrollment status for workers
            if request.session.get('user_type') == 'pekerja':
                user_id = request.session.get('user_id')
                
                # Get pekerja photo
                cur.execute('SELECT linkfoto FROM PEKERJA WHERE id = %s', (user_id,))
                pekerja_data = cur.fetchone()
                
                # Check if enrolled in this category
                cur.execute("""
                    SELECT 1 
                    FROM PEKERJA_KATEGORI_JASA pk
                    JOIN SUBKATEGORI_JASA s ON s.kategorijasaid = pk.kategorijasaid
                    WHERE pk.pekerjaid = %s AND s.namasubkategori = %s
                """, (user_id, subcategory_name))
                
                is_enrolled = cur.fetchone() is not None
                
                if pekerja_data:
                    context['additional_attributes'] = {
                        'foto_url': pekerja_data[0],
                        'is_enrolled': is_enrolled
                    }
                cur.close()
                conn.close()
        
        logger.info(f"Rendering template with context: {context}")
        return render(request, 'subcategory.html', context)
        
    except Exception as e:
        logger.error(f"Error in show_subcategory: {str(e)}", exc_info=True)
        return redirect('main:show_home_page')

def enroll_subcategory(request, subcategory_name):
    if request.session.get('user_type') != 'pekerja':
        return redirect('main:show_home_page')
    
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            logger.error("Could not establish database connection")
            return redirect('main:show_home_page')
        
        user_id = request.session.get('user_id')
        
        # Get category ID for the subcategory
        cur.execute("""
            SELECT k.id
            FROM SUBKATEGORI_JASA s
            JOIN KATEGORI_JASA k ON s.kategorijasaid = k.id
            WHERE s.namasubkategori = %s
        """, [subcategory_name])
        result = cur.fetchone()
        
        if not result:
            logger.error(f"Subcategory not found: {subcategory_name}")
            return redirect('main:show_home_page')
        
        category_id = result[0]
        
        # Check if already enrolled
        cur.execute("""
            SELECT 1 FROM PEKERJA_KATEGORI_JASA 
            WHERE pekerjaid = %s AND kategorijasaid = %s
        """, [user_id, category_id])
        
        if not cur.fetchone():
            # Enroll in category if not already enrolled
            cur.execute("""
                INSERT INTO PEKERJA_KATEGORI_JASA (pekerjaid, kategorijasaid)
                VALUES (%s, %s)
            """, [user_id, category_id])
            conn.commit()
        
        cur.close()
        conn.close()
        
        return redirect('subkategori:show_subcategory', subcategory_name=subcategory_name)
        
    except Exception as e:
        logger.error(f"Error in enroll_subcategory: {str(e)}", exc_info=True)
        return redirect('main:show_home_page')
