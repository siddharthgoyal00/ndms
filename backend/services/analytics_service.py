"""
services/analytics_service.py — business logic for analytics counts
"""
from db.connection import get_db_connection
from db.queries import (
    ANALYTICS_QUERY,
    build_where_clause,
    build_analytics_chart_query,
)


def get_analytics_counts(filters: dict) -> dict:
    """
    Returns pre-computed summary counts for the analytic table widget.
    Reads from analytic_table directly with filter support.
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


def get_analytics_chart_data(period_type: str) -> list[dict]:
    """
    Returns time-bucketed analytics for the Analytics Charts widget.
    Independent of user search filters — always reads the full table.

    period_type: till_now | daily | weekly | monthly | yearly
    Each row: { label, l0_success_count, l0_failed_count,
                dpgs_success_count, dpgs_failed_count,
                rc_count, observation_count }
    """
    query = build_analytics_chart_query(period_type)

    conn   = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(r) for r in rows]
    finally:
        cursor.close()
        conn.close()