import os
import psycopg2
from psycopg2 import sql
import uuid # To generate UUIDs for new listings if not handled by DB automatically

def get_db_connection():
    """Establishes and returns a PostgreSQL database connection."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn

def init_db():
    """Initializes the database schema. This is usually run by init.sql in Docker."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # This part is mostly for local dev if not using init.sql or for re-init
        cur.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                item_name VARCHAR(255) NOT NULL,
                price NUMERIC(10, 2) NOT NULL,
                description TEXT,
                status VARCHAR(50) NOT NULL DEFAULT 'active',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("Database initialized successfully (if tables didn't exist).")
    except Exception as e:
        print(f"Error initializing database: {e}")

# In a real application, you might call init_db() once at startup if needed,
# but for Docker, init.sql handles initial schema creation.
