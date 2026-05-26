"""
services/analytics_service.py — business logic for analytics counts
"""
from db.connection import get_db_connection
from db.queries import ANALYTICS_QUERY, build_where_clause


def get_analytics_counts(filters: dict) -> dict:
    """
    Returns pre-computed summary counts for the analytic table widget.
    Reads from analytic_table directly with filter support.
    When materialized views are available, switch to mv_summary_counts for speed.
    """
    where, params = build_where_clause(filters)
    query = ANALYTICS_QUERY + where

    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else {}
    finally:
        cursor.close()
        conn.close()