import psycopg2, os
from psycopg2 import Error

def get_db_connection():
    try:
        connection = psycopg2.connect(
            user = 'postgres.zdpwcrvbgfcydcvrfese',
            password = 'HOlJuL6NucqWnOkw',
            host = 'aws-0-ap-southeast-1.pooler.supabase.com',
            port = '5432',
            database = 'postgres'
        )
        cursor = connection.cursor()
        cursor.execute('SET search_path TO SIJARTA;')
        return connection, cursor
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
        return None, None