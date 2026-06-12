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
    WITH obs_units AS (
        SELECT
            a.observation_id,
            a.track,
            a.frame,
            MAX(CASE WHEN a.product_name = 'RSLC' THEN LOWER(a.product_status) END) AS runw_status,
            MAX(CASE WHEN a.product_name = 'GSLC' THEN LOWER(a.product_status) END) AS gunw_status,
            MAX(CASE WHEN a.product_name = 'GCOV' THEN LOWER(a.product_status) END) AS gcov_status
        FROM analytic_table a
        {where}
        GROUP BY a.observation_id, a.track, a.frame
    )
    SELECT
        COUNT(DISTINCT (a.observation_id, a.track, a.frame))         AS observation_count,
        COUNT(DISTINCT a.SESS_ID)                                     AS session_count,
        COUNT(DISTINCT a.DATATAKE_ID)                                 AS datatake_count,
        COUNT(DISTINCT CASE WHEN a.SSAR_CONFIG_ID IS NOT NULL 
              THEN (a.observation_id, a.track, a.frame, a.SSAR_CONFIG_ID) 
              END)                                                     AS rc_count,
        SUM(CASE WHEN LOWER(a.L0_status) = 'completed'     THEN 1 ELSE 0 END) AS l0_success_count,
        SUM(CASE WHEN LOWER(a.L0_status) = 'not completed' THEN 1 ELSE 0 END) AS l0_failed_count,
        (SELECT COUNT(*) FROM obs_units
         WHERE runw_status = 'completed'
           AND gunw_status = 'completed'
           AND gcov_status = 'completed')                              AS dpgs_success_count,
        (SELECT COUNT(*) FROM obs_units
         WHERE runw_status != 'completed' OR runw_status IS NULL
            OR gunw_status != 'completed' OR gunw_status IS NULL
            OR gcov_status != 'completed' OR gcov_status IS NULL)      AS dpgs_failed_count
    FROM analytic_table a
"""

# ── Analytics chart (filter-independent, time-bucketed) ───────────────────────

ANALYTICS_CHART_PERIOD_EXPR = {
    "till_now": "'All Time'",
    "daily":    "TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY-MM-DD')",
    "weekly":   "TO_CHAR(a.CMD_SSAR_START_DATETIME, 'IYYY-IW')",
    "monthly":  "TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY-MM')",
    "yearly":   "TO_CHAR(a.CMD_SSAR_START_DATETIME, 'YYYY')",
}

ANALYTICS_CHART_TEMPLATE = """
    WITH obs_units AS (
        SELECT
            a.observation_id,
            a.track,
            a.frame,
            __PERIOD_EXPR__ AS period_label,
            MAX(CASE WHEN a.product_name = 'RSLC' THEN LOWER(a.product_status) END) AS runw_status,
            MAX(CASE WHEN a.product_name = 'GSLC' THEN LOWER(a.product_status) END) AS gunw_status,
            MAX(CASE WHEN a.product_name = 'GCOV' THEN LOWER(a.product_status) END) AS gcov_status
        FROM analytic_table a
        WHERE a.CMD_SSAR_START_DATETIME IS NOT NULL
        GROUP BY a.observation_id, a.track, a.frame, __PERIOD_EXPR__
    ),
    dpgs_agg AS (
        SELECT
            period_label,
            SUM(CASE WHEN runw_status = 'completed'
                      AND gunw_status = 'completed'
                      AND gcov_status = 'completed'
                     THEN 1 ELSE 0 END)                       AS dpgs_success_count,
            SUM(CASE WHEN runw_status IS NULL OR gunw_status IS NULL OR gcov_status IS NULL
                      OR runw_status != 'completed'
                      OR gunw_status != 'completed'
                      OR gcov_status != 'completed'
                     THEN 1 ELSE 0 END)                       AS dpgs_failed_count
        FROM obs_units
        GROUP BY period_label
    ),
    base_agg AS (
        SELECT
            __PERIOD_EXPR__ AS period_label,
            COUNT(DISTINCT (a.observation_id, a.track, a.frame))            AS observation_count,
            COUNT(DISTINCT CASE WHEN a.SSAR_CONFIG_ID IS NOT NULL
                  THEN (a.observation_id, a.track, a.frame, a.SSAR_CONFIG_ID)
                  END)                                                       AS rc_count,
            SUM(CASE WHEN LOWER(a.L0_status) = 'completed'     THEN 1 ELSE 0 END) AS l0_success_count,
            SUM(CASE WHEN LOWER(a.L0_status) = 'not completed' THEN 1 ELSE 0 END) AS l0_failed_count
        FROM analytic_table a
        WHERE a.CMD_SSAR_START_DATETIME IS NOT NULL
        GROUP BY __PERIOD_EXPR__
    )
    SELECT
        b.period_label                       AS label,
        b.l0_success_count,
        b.l0_failed_count,
        COALESCE(d.dpgs_success_count, 0)    AS dpgs_success_count,
        COALESCE(d.dpgs_failed_count, 0)     AS dpgs_failed_count,
        b.rc_count,
        b.observation_count
    FROM base_agg b
    LEFT JOIN dpgs_agg d ON b.period_label = d.period_label
    ORDER BY b.period_label ASC
"""


def build_analytics_chart_query(period_type: str) -> str:
    """
    Returns the analytics chart SQL for the given period type.
    Unknown types fall back to 'till_now'.
    """
    expr = ANALYTICS_CHART_PERIOD_EXPR.get(period_type, ANALYTICS_CHART_PERIOD_EXPR["till_now"])
    return ANALYTICS_CHART_TEMPLATE.replace("__PERIOD_EXPR__", expr)

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