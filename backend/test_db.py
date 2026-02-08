import mysql.connector

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="msais_db",
        port=3306
    )

    print("✅ Connected to MySQL successfully!")
    conn.close()

except Exception as e:
    print("❌ Connection failed!")
    print("Error:", e)
