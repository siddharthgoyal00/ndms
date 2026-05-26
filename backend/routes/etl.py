"""
routes/etl.py — ETL trigger + status
Proxies to the ETL container so the frontend only talks to the backend.
"""
import os
import requests
from flask import Blueprint, jsonify
from db.connection import get_db_connection
from db.queries import ETL_STATUS_QUERY

etl_bp = Blueprint("etl", __name__)

ETL_SERVICE_URL = os.getenv("ETL_SERVICE_URL", "http://pipeline_etl:5001")


@etl_bp.route("/etl/trigger", methods=["POST"])
def trigger_etl():
    """Proxies trigger request to ETL container."""
    try:
        resp = requests.post(f"{ETL_SERVICE_URL}/etl/trigger", timeout=10)
        return jsonify(resp.json()), resp.status_code
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@etl_bp.route("/etl/status")
def etl_status():
    """Reads ETL status directly from postgres etl_runs table."""
    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(ETL_STATUS_QUERY)
        row = cursor.fetchone()

        if not row:
            return jsonify({"status": "NEVER_RUN", "time": None})

        r = dict(row)

        # convert timestamps to IST string for display
        def to_ist(dt):
            if not dt:
                return None
            from datetime import timedelta
            ist = dt + timedelta(hours=5, minutes=30)
            return ist.strftime("%Y-%m-%d %H:%M:%S")

        display_time = r.get("end_time") or r.get("start_time")

        return jsonify({
            "status":         r["status"],
            "phase":          r.get("phase"),
            "time":           to_ist(display_time),
            "rows_processed": r.get("rows_processed"),
            "error":          r.get("error_message"),
        })

    finally:
        cursor.close()
        conn.close()