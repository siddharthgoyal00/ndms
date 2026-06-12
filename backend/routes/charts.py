"""
routes/charts.py
  GET /api/rc_stats          — legacy RC bar chart (rc_cache based)
  GET /api/analytics_chart    — NEW: filter-independent summary chart
"""
from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from db.queries import RC_STATS_QUERIES
from services.analytics_service import get_analytics_chart_data

charts_bp = Blueprint("charts", __name__)


@charts_bp.route("/rc_stats")
def rc_stats():
    chart_type = request.args.get("type", "monthly")

    if chart_type not in RC_STATS_QUERIES:
        chart_type = "monthly"

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        period_map = {"monthly": "monthly", "weekly": "weekly", "yearly": "yearly"}
        cursor.execute("""
            SELECT period_label AS label, SUM(count) AS count
            FROM   public.rc_cache
            WHERE  period_type = %s
            GROUP  BY period_label
            ORDER  BY period_label ASC
        """, (period_map[chart_type],))

        rows = cursor.fetchall()

        if not rows:
            cursor.execute(RC_STATS_QUERIES[chart_type])
            rows = cursor.fetchall()

        return jsonify([dict(r) for r in rows])

    finally:
        cursor.close()
        conn.close()


@charts_bp.route("/analytics_chart")
def analytics_chart():
    """
    Filter-independent summary chart.
    ?type = till_now | daily | weekly | monthly | yearly  (default: till_now)
    """
    period_type = request.args.get("type", "till_now")

    valid_types = {"till_now", "daily", "weekly", "monthly", "yearly"}
    if period_type not in valid_types:
        period_type = "till_now"

    data = get_analytics_chart_data(period_type)
    return jsonify(data)