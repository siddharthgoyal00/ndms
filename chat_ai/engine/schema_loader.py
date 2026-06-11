"""
engine/schema_loader.py

Fetches column names + types for analytic_table and rc_cache from postgres.
Called once per /ai/query request (no caching — schema may change after ETL).

Uses the same PG_* env vars as the ETL and backend containers.
"""
import os
import logging

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)


def _get_conn():
    return psycopg2.connect(
        host     = os.environ["PG_HOST"],
        dbname   = os.environ["PG_DB"],
        user     = os.environ["PG_USER"],
        password = os.environ["PG_PASSWORD"],
        port     = int(os.environ.get("PG_PORT", 5432)),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def load_schema(tables: list[str] | None = None) -> str:
    """
    Returns a human-readable schema string for the given tables.

    Default tables: analytic_table, rc_cache

    Example output:
        Table: analytic_table
          observation_id   (character varying)
          product_name     (character varying)
          ...
        Table: rc_cache
          ...
    """
    if tables is None:
        tables = ["analytic_table", "rc_cache"]

    conn   = _get_conn()
    cursor = conn.cursor()
    lines  = []

    try:
        for table in tables:
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name   = %s
                ORDER BY ordinal_position
            """, (table,))
            rows = cursor.fetchall()

            if not rows:
                logger.warning(f"schema_loader: no columns found for table '{table}'")
                continue

            lines.append(f"Table: {table}")
            for r in rows:
                lines.append(f"  {r['column_name']}  ({r['data_type']})")

        return "\n".join(lines)

    finally:
        cursor.close()
        conn.close()