import os
import psycopg2
from psycopg2 import sql
import uuid # To generate UUIDs for new listings if not handled by DB automatically

def get_db_connection():
    """Establishes and returns a PostgreSQL database connection."""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    return conn
