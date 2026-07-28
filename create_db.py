import MySQLdb

def create_database():
    try:
        # Connect to MySQL server running on localhost (XAMPP default: root / no password)
        conn = MySQLdb.connect(host='localhost', port=3306, user='root', passwd='')
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS shopbill_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print("Database 'shopbill_db' created or already exists!")
        conn.close()
        return True
    except Exception as e:
        print(f"Could not connect to MySQL server: {e}")
        return False

if __name__ == '__main__':
    create_database()
