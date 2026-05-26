"""
routes/charts.py — GET /api/rc_stats
Bar chart data — monthly/weekly/yearly counts from rc_cache.
Falls back to direct query on analytic_table if rc_cache is empty.
"""
from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from db.queries import RC_STATS_QUERIES

charts_bp = Blueprint("charts", __name__)


@charts_bp.route("/rc_stats")
def rc_stats():
    chart_type = request.args.get("type", "monthly")

    # default to monthly for unknown types
    if chart_type not in RC_STATS_QUERIES:
        chart_type = "monthly"

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        # try rc_cache first — pre-aggregated, fast
        period_map = {"monthly": "monthly", "weekly": "weekly", "yearly": "yearly"}
        cursor.execute("""
            SELECT period_label AS label, SUM(count) AS count
            FROM   public.rc_cache
            WHERE  period_type = %s
            GROUP  BY period_label
            ORDER  BY period_label ASC
        """, (period_map[chart_type],))

        rows = cursor.fetchall()

        # if rc_cache is empty fall back to direct query
        if not rows:
            cursor.execute(RC_STATS_QUERIES[chart_type])
            rows = cursor.fetchall()

        return jsonify([dict(r) for r in rows])

    finally:
        cursor.close()
        conn.close()