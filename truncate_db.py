from app import get_db_connection
import mysql.connector

def truncate_tables():
    print("Clearing all data from tables...")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Disable FK checks to allow truncating tables with relationships
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        
        tables = ['approvals', 'donors', 'users', 'daily_stats']
        for table in tables:
            print(f"Truncating table {table}...")
            cursor.execute(f"TRUNCATE TABLE {table}")
            
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        conn.commit()
        print("All tables cleared successfully.")
        
    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    truncate_tables()
