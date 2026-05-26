"""
db/connection.py — PostgreSQL connection helper

All credentials read from environment variables set in docker-compose.yml.
Each request gets its own connection — simple and safe for current scale (30 users).
For higher scale, swap get_db_connection() with a connection pool (psycopg2.pool).
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor


def get_db_connection():
  
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "postgres_db"),
        dbname=os.getenv("PG_DB", "analytics_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        port=int(os.getenv("PG_PORT", 5432)),
        cursor_factory=RealDictCursor,
        connect_timeout=10,
    )
    return conn