import psycopg2
import sys

try:
    conn = psycopg2.connect(
        "postgresql://neondb_owner:npg_iq38KChNyLpO@ep-winter-glitter-ah0foh8z-pooler.c-3.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    print("✅ Database connection successful!")
    
    # Test a simple query
    cursor = conn.cursor()
    cursor.execute("SELECT 1;")
    result = cursor.fetchone()
    print(f"✅ Query test successful: {result}")
    
    conn.close()
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    sys.exit(1)