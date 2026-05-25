"""
etl_service.py — Flask entry point for the ETL container

Endpoints:
  POST /etl/trigger    runs Phase 1 (raw load) + Phase 2 (transform + swap)
  GET  /etl/status     returns last ETL run status for dashboard header
  GET  /health         container health check for Docker healthcheck
"""
import logging
import datetime
import threading
from flask import Flask, jsonify
from core.db import get_pg_conn
from core.phase1_raw_load import run_phase1
from core.phase2_transform import run_phase2
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ── ETL audit helper ──────────────────────────────────────────────────────────

def record_run(status, phase, start_time, rows=None, error=None):
    """
    Writes one row to etl_runs audit table.
    Called after Phase 1 and after Phase 2 complete or fail.
    last_processed_time is set to start_time on SUCCESS — used as
    the watermark for the next ETL run's incremental load.
    """
    try:
        conn   = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO public.etl_runs
                (status, phase, start_time, end_time,
                 last_processed_time, rows_processed, error_message)
            VALUES (%s, %s, %s, NOW(), %s, %s, %s)
        """, (
            status,
            phase,
            start_time,
            start_time if status == "SUCCESS" else None,
            rows,
            error
        ))
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to write etl_runs record: {e}")


# ── Full ETL pipeline ─────────────────────────────────────────────────────────

def run_full_etl():
    """
    Orchestrates the complete ETL in two phases:

    Phase 1 — Raw Load:
      Connects to MySQL and MariaDB, discovers all tables dynamically,
      copies every table into postgres raw schema as-is.
      MySQL tables → raw.{table}_mysql
      MariaDB tables → raw.{table}_mariadb

    Phase 2 — Transform + Optimize:
      Reads from raw schema, runs CTE join + UNION ALL unpivot,
      builds analytic_table_new (partitioned, indexed),
      rebuilds rc_cache, performs blue-green swap,
      refreshes materialized views.

    If Phase 1 fails, Phase 2 does not run.
    Each phase records its own SUCCESS/FAILED row in etl_runs.
    """
    start = datetime.datetime.now()
    logger.info("=" * 60)
    logger.info("FULL ETL TRIGGERED")
    logger.info("=" * 60)

    # ── Phase 1: Raw Load ─────────────────────────────────────────────────
    try:
        logger.info("Starting Phase 1: Raw Load")
        p1 = run_phase1()
        record_run(
            status="SUCCESS",
            phase="RAW_LOAD",
            start_time=start,
            rows=p1["total"]
        )
        logger.info(f"Phase 1 done: mysql={p1['mysql_rows']} mariadb={p1['mariadb_rows']} total={p1['total']}")
    except Exception as e:
        record_run(status="FAILED", phase="RAW_LOAD", start_time=start, error=str(e))
        logger.error(f"Phase 1 FAILED: {e}")
        return False, f"Phase 1 (raw load) failed: {e}"

    # ── Phase 2: Transform ────────────────────────────────────────────────
    try:
        logger.info("Starting Phase 2: Transform + Blue-Green Swap")
        p2 = run_phase2()
        record_run(
            status="SUCCESS",
            phase="COMPLETE",
            start_time=start,
            rows=p2["rows"]
        )
        logger.info(f"Phase 2 done: rows={p2['rows']} duration={p2['duration_sec']}s")
        return True, f"ETL complete — {p2['rows']:,} rows in {p2['duration_sec']}s"
    except Exception as e:
        record_run(status="FAILED", phase="TRANSFORM", start_time=start, error=str(e))
        logger.error(f"Phase 2 FAILED: {e}")
        return False, f"Phase 2 (transform) failed: {e}"


# ── Routes ────────────────────────────────────────────────────────────────────

# @app.route("/etl/trigger", methods=["POST"])
# def trigger_etl():
#     """
#     Manually triggers the full ETL pipeline.
#     Called by:
#       - Dashboard "Run ETL" button (dev)
#       - curl -X POST http://localhost:5001/etl/trigger
#       - APScheduler nightly job (when added)
#     Synchronous — returns when ETL completes.
#     For async, wrap run_full_etl in a thread and return job_id immediately.
#     """
#     success, message = run_full_etl()
#     if success:
#         return jsonify({"status": "success", "message": message}), 200
#     return jsonify({"status": "failed", "error": message}), 500



@app.route("/etl/trigger", methods=["POST"])
def trigger_etl():
    thread = threading.Thread(target=run_full_etl, daemon=True)
    thread.start()
    return jsonify({"status": "started", "message": "ETL running in background — check /etl/status"}), 202

@app.route("/etl/status", methods=["GET"])
def etl_status():
    """
    Returns last ETL run details.
    Consumed by dashboard navbar to show ETL success/failure indicator.
    """
    try:
        conn   = get_pg_conn()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT status, phase, start_time, end_time,
                   rows_processed, error_message
            FROM   public.etl_runs
            ORDER  BY id DESC
            LIMIT  1
        """)
        row = cursor.fetchone()
        cursor.close()
        conn.close()

        if not row:
            return jsonify({"status": "NEVER_RUN", "time": None})

        return jsonify({
            "status":   row[0],
            "phase":    row[1],
            "time":     str(row[2]) if row[2] else None,
            "end_time": str(row[3]) if row[3] else None,
            "rows":     row[4],
            "error":    row[5],
        })
    except Exception as e:
        logger.error(f"ETL status error: {e}")
        return jsonify({"status": "ERROR", "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    """Used by Docker healthcheck and frontend proxy."""
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)