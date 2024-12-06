from django.shortcuts import render, get_object_or_404, redirect
from utils.query import get_db_connection
from urllib.parse import unquote
import logging

logger = logging.getLogger(__name__)

# Create your views here.

def show_subcategory(request, subcategory_name):
    # Decode URL-encoded name and convert hyphens back to spaces
    subcategory_name = unquote(subcategory_name).replace('-', ' ')
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
        
        cur.close()
        conn.close()
        
        context = {
            'subcategory': subcategory,
            'category': category
        }
        
        logger.info(f"Rendering template with context: {context}")
        return render(request, 'subcategory.html', context)
        
    except Exception as e:
        logger.error(f"Error in show_subcategory: {str(e)}", exc_info=True)
        return redirect('main:show_home_page')
