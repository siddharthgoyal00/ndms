"""
db/queries.py — raw SQL query strings

Centralised here so routes never contain SQL.
All queries use %s placeholders (psycopg2 style, NOT ? like SQLite).
"""

# ── Filter builder ────────────────────────────────────────────────────────────

def build_where_clause(filters: dict) -> tuple[str, list]:
    """
    Builds a WHERE clause string and params list from the filter dict.
    Called by multiple routes — single source of truth for filter logic.

    Returns:
        where_sql  — SQL string starting with "WHERE 1=1 AND ..."
        params     — list of values matching %s placeholders
    """
    where = "WHERE 1=1"
    params = []

    # datetime range
    if filters.get("cmd_start"):
        where += " AND a.CMD_SSAR_START_DATETIME >= %s"
        params.append(filters["cmd_start"].replace("T", " "))

    if filters.get("cmd_end"):
        where += " AND a.CMD_SSAR_END_DATETIME <= %s"
        params.append(filters["cmd_end"].replace("T", " "))

    # observation id
    if filters.get("Ob_id"):
        val = filters["Ob_id"].strip().replace("*", "%")
        where += " AND a.observation_id LIKE %s"
        params.append(val)

    # session id — auto-prefix ssid_ if missing
    if filters.get("Session_id"):
        val = filters["Session_id"].strip().lower()
        if not val.startswith("ssid_"):
            val = "ssid_" + val
        val = val.replace("*", "%")
        where += " AND a.SESS_ID LIKE %s"
        params.append(val)

    # RC / SSAR config id
    if filters.get("Rc_id"):
        where += " AND a.SSAR_CONFIG_ID = %s"
        params.append(filters["Rc_id"].strip())

    # L0 status
    if filters.get("L0_status"):
        where += " AND LOWER(a.L0_status) = %s"
        params.append(filters["L0_status"].strip().lower())

    # cycle number
    if filters.get("cycle"):
        where += " AND a.CYCLE_NO = %s"
        params.append(filters["cycle"].strip())

    # work order id
    if filters.get("WO_id"):
        val = filters["WO_id"].strip().replace("*", "%")
        where += " AND a.MASTERWORK_ORDER_ID LIKE %s"
        params.append(val)

    return where, params


# ── Observations (paginated table) ────────────────────────────────────────────

OBSERVATIONS_SELECT = """
    SELECT
        a.observation_id   AS "REFOBS_ID",
        a.SSAR_CONFIG_ID,
        a.SESS_ID,
        a.DATATAKE_ID,
        a.CMD_SSAR_START_DATETIME,
        a.CMD_SSAR_END_DATETIME,
        a.DUMP_ORBIT,
        a.TRACK,
        a.FRAME,
        a.L0_status,
        a.MASTERWORK_ORDER_ID,
        a.CYCLE_NO,
        a.scene_no,
        a.crid_id,
        a.WKT_POLYGON,
        a.product_workorder_id,
        a.product_name,
        a.product_status
    FROM analytic_table a
"""

OBSERVATIONS_ORDER = """
    ORDER BY
        a.CMD_SSAR_START_DATETIME DESC,
        a.observation_id,
        a.product_name
    LIMIT %s OFFSET %s
"""

COUNT_QUERY = "SELECT COUNT(*) AS total FROM analytic_table a "


# ── Analytics summary counts ──────────────────────────────────────────────────

ANALYTICS_QUERY = """
    SELECT
        COUNT(DISTINCT a.obs_key)       AS observation_count,
        COUNT(DISTINCT a.SESS_ID)       AS session_count,
        COUNT(DISTINCT a.DATATAKE_ID)   AS datatake_count,
        COUNT(DISTINCT a.SSAR_CONFIG_ID) AS rc_count,
        SUM(CASE WHEN LOWER(a.L0_status) = 'completed'     THEN 1 ELSE 0 END) AS l0_success_count,
        SUM(CASE WHEN LOWER(a.L0_status) = 'not completed' THEN 1 ELSE 0 END) AS l0_failed_count,
        SUM(CASE WHEN LOWER(a.product_status) = 'completed'     THEN 1 ELSE 0 END) AS dpgs_success_count,
        SUM(CASE WHEN LOWER(a.product_status) = 'not completed' THEN 1 ELSE 0 END) AS dpgs_failed_count
    FROM analytic_table a
"""


# ── Map polygons ──────────────────────────────────────────────────────────────

MAP_POLYGONS_SELECT = """
    SELECT DISTINCT ON (a.observation_id)
        a.observation_id,
        a.WKT_POLYGON
    FROM analytic_table a
    WHERE a.WKT_POLYGON IS NOT NULL
"""

MAP_POLYGONS_ORDER = " ORDER BY a.observation_id"


# ── RC stats (bar chart) ──────────────────────────────────────────────────────
# PostgreSQL uses TO_CHAR() instead of SQLite's strftime()

RC_STATS_QUERIES = {
    "monthly": """
        SELECT
            TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY-MM') AS label,
            COUNT(*)                                        AS count
        FROM analytic_table a
        WHERE a.CMD_SSAR_START_DATETIME IS NOT NULL
        GROUP BY TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY-MM')
        ORDER BY label ASC
    """,
    "weekly": """
        SELECT
            TO_CHAR(a.CMD_SSAR_START_DATETIME, 'IYYY-IW') AS label,
            COUNT(*)                                        AS count
        FROM analytic_table a
        WHERE a.CMD_SSAR_START_DATETIME IS NOT NULL
        GROUP BY TO_CHAR(a.CMD_SSAR_START_DATETIME, 'IYYY-IW')
        ORDER BY label ASC
    """,
    "yearly": """
        SELECT
            TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY') AS label,
            COUNT(*)                                     AS count
        FROM analytic_table a
        WHERE a.CMD_SSAR_START_DATETIME IS NOT NULL
        GROUP BY TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY')
        ORDER BY label ASC
    """,
}


# ── ETL status ────────────────────────────────────────────────────────────────

ETL_STATUS_QUERY = """
    SELECT
        status,
        phase,
        start_time,
        end_time,
        rows_processed,
        error_message
    FROM public.etl_runs
    ORDER BY id DESC
    LIMIT 1
"""