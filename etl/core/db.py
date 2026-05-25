"""
core/db.py — database connection helpers

All credentials read from environment variables.
Environment variables are set in docker-compose.yml.
Defaults match the compose file values for local dev.
"""
import os
import psycopg2
import pymysql


def get_pg_conn():
    """
    PostgreSQL connection — analytics store.
    Used by Phase 2 transform, rc_cache, materialized views,
    blue-green swap, and etl_runs audit table.
    """
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "postgres_db"),
        dbname=os.getenv("PG_DB", "analytics_db"),
        user=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD", "postgres"),
        port=int(os.getenv("PG_PORT", 5432)),
        connect_timeout=30,
    )


def get_mysql_conn():
    """
    MySQL connection — source database A.
    Used by Phase 1 raw load to discover and copy all MySQL tables.
    DictCursor returns rows as dicts — column names preserved.
    """
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "mysql_db"),
        db=os.getenv("MYSQL_DB", "source_db"),
        user=os.getenv("MYSQL_USER", "root"),
        password=os.getenv("MYSQL_PASSWORD", "root"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
    )


def get_mariadb_conn():
    """
    MariaDB connection — source database B.
    Same driver as MySQL (pymysql), different host.
    """
    return pymysql.connect(
        host=os.getenv("MARIADB_HOST", "mariadb_db"),
        db=os.getenv("MARIADB_DB", "source_db"),
        user=os.getenv("MARIADB_USER", "root"),
        password=os.getenv("MARIADB_PASSWORD", "root"),
        port=int(os.getenv("MARIADB_PORT", 3306)),
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        connect_timeout=30,
    )