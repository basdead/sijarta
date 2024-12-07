from django.shortcuts import render, get_object_or_404, redirect
from utils.query import get_db_connection
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def show_subcategory(request, subcategory_name):
    # Log the raw input
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
    
    logger.info(f"Looking for subcategory: {subcategory_name}")
    
    try:
        conn, cur = get_db_connection()
        if not conn or not cur:
            logger.error("Could not establish database connection")
            return redirect('main:show_home_page')
        
        # First, let's see what subcategories exist
        cur.execute("SELECT namasubkategori FROM SUBKATEGORI_JASA")
        all_subcats = cur.fetchall()
        logger.info(f"All subcategories in database: {all_subcats}")
        
        # Fetch subcategory details using name
        query = """
            SELECT s.namasubkategori, s.deskripsi, k.namakategori, k.id
            FROM SUBKATEGORI_JASA s
            JOIN KATEGORI_JASA k ON s.kategorijasaid = k.id
            WHERE s.namasubkategori = %s
        """
        logger.info(f"Executing query with name: {subcategory_name!r}")  # !r shows quotes and escapes
        cur.execute(query, [subcategory_name])
        
        result = cur.fetchone()
        logger.info(f"Query result: {result!r}")
        
        if not result:
            logger.warning(f"Subcategory not found: {subcategory_name!r}")
            cur.close()
            conn.close()
            return redirect('main:show_home_page')
        
        subcategory = {
            'nama_subkategori': result[0],
            'deskripsi': result[1]
        }
        
        category = {
            'nama_kategori': result[2],
            'id_kategori': result[3]
        }
        
        # Fetch sesi_layanan for this subcategory
        cur.execute("""
            SELECT sesi, harga 
            FROM SESI_LAYANAN sl
            JOIN SUBKATEGORI_JASA sj ON sl.subkategoriid = sj.id
            WHERE sj.namasubkategori = %s
            ORDER BY sesi
        """, [subcategory_name])
        sessions = [{'sesi': row[0], 'harga': "{:,.0f}".format(row[1]).replace(",", ".")} for row in cur.fetchall()]
        
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
