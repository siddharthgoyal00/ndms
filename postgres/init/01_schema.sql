-- ═══════════════════════════════════════════════════════════════════════════
-- 01_schema.sql — auto-runs on first postgres container start
--
-- Creates:
--   raw schema          Phase 1 staging (MySQL + MariaDB copies)
--   public schema       Phase 2 output (read-optimized tables + views)
--   etl_runs            ETL audit table
--   rc_cache            pre-aggregated chart data
--   analytic_table      partitioned, indexed, read-optimized main table
--   3 materialized views  pre-computed dashboard summary counts
-- ═══════════════════════════════════════════════════════════════════════════

-- postgres analytics tuning
ALTER SYSTEM SET work_mem                       = '256MB';
ALTER SYSTEM SET max_parallel_workers_per_gather = 4;
ALTER SYSTEM SET max_parallel_workers            = 4;
ALTER SYSTEM SET enable_partitionwise_join       = on;
ALTER SYSTEM SET enable_partitionwise_aggregate  = on;
SELECT pg_reload_conf();

CREATE SCHEMA IF NOT EXISTS raw;

-- ── ETL audit ─────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.etl_runs (
    id                  SERIAL PRIMARY KEY,
    status              TEXT,
    phase               TEXT,
    start_time          TIMESTAMP,
    end_time            TIMESTAMP,
    last_processed_time TIMESTAMP,
    rows_processed      INTEGER,
    error_message       TEXT
);

-- ── rc_cache ──────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.rc_cache (
    id           SERIAL PRIMARY KEY,
    period_type  TEXT,
    period_label TEXT,
    rc_id        TEXT,
    count        INTEGER,
    updated_at   TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_rc_lookup ON public.rc_cache (period_type, period_label);

-- ── analytic_table (partitioned by year, FILLFACTOR=70) ───────────────────
CREATE TABLE IF NOT EXISTS public.analytic_table (
    observation_id          TEXT,
    obs_key                 TEXT,
    SESS_ID                 TEXT,
    CMD_SSAR_START_DATETIME TIMESTAMP,
    CMD_SSAR_END_DATETIME   TEXT,
    SSAR_CONFIG_ID          TEXT,
    DATATAKE_ID             TEXT,
    L0_status               TEXT,
    DUMP_ORBIT              INTEGER,
    TRACK                   INTEGER,
    FRAME                   INTEGER,
    MASTERWORK_ORDER_ID     TEXT,
    CYCLE_NO                INTEGER,
    scene_no                TEXT,
    crid_id                 TEXT,
    WKT_POLYGON             TEXT,
    product_name            TEXT,
    product_workorder_id    TEXT,
    product_status          TEXT
)
PARTITION BY RANGE (CMD_SSAR_START_DATETIME)
WITH (FILLFACTOR = 70);

-- Yearly partitions — add more as mission continues
CREATE TABLE IF NOT EXISTS public.analytic_2023 PARTITION OF public.analytic_table FOR VALUES FROM ('2023-01-01') TO ('2024-01-01');
CREATE TABLE IF NOT EXISTS public.analytic_2024 PARTITION OF public.analytic_table FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE IF NOT EXISTS public.analytic_2025 PARTITION OF public.analytic_table FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE IF NOT EXISTS public.analytic_2026 PARTITION OF public.analytic_table FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');
CREATE TABLE IF NOT EXISTS public.analytic_2027 PARTITION OF public.analytic_table FOR VALUES FROM ('2027-01-01') TO ('2028-01-01');
CREATE TABLE IF NOT EXISTS public.analytic_default PARTITION OF public.analytic_table DEFAULT;

-- ── Indexes on live table ─────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_at_obs_id      ON public.analytic_table (observation_id);
CREATE INDEX IF NOT EXISTS idx_at_obs_key     ON public.analytic_table (obs_key);
CREATE INDEX IF NOT EXISTS idx_at_time_brin   ON public.analytic_table USING BRIN (CMD_SSAR_START_DATETIME) WITH (pages_per_range = 32);
CREATE INDEX IF NOT EXISTS idx_at_time_btree  ON public.analytic_table (CMD_SSAR_START_DATETIME);
CREATE INDEX IF NOT EXISTS idx_at_cfg_time    ON public.analytic_table (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME);
CREATE INDEX IF NOT EXISTS idx_at_l0          ON public.analytic_table (L0_status);
CREATE INDEX IF NOT EXISTS idx_at_product     ON public.analytic_table (product_name);
CREATE INDEX IF NOT EXISTS idx_at_cycle       ON public.analytic_table (CYCLE_NO);
CREATE INDEX IF NOT EXISTS idx_at_datatake    ON public.analytic_table (DATATAKE_ID);
CREATE INDEX IF NOT EXISTS idx_at_polygon     ON public.analytic_table (observation_id) WHERE WKT_POLYGON IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_at_covering    ON public.analytic_table (CMD_SSAR_START_DATETIME DESC, observation_id, product_name) INCLUDE (SSAR_CONFIG_ID, L0_status, CYCLE_NO, TRACK, FRAME, DATATAKE_ID);

-- ── Materialized views ────────────────────────────────────────────────────
-- Dashboard summary counts — feeds analytic summary table
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_summary_counts AS
SELECT
    COUNT(DISTINCT observation_id)                                AS observation_count,
    COUNT(DISTINCT DATATAKE_ID)                                   AS datatake_count,
    COUNT(DISTINCT SSAR_CONFIG_ID)                                AS rc_count,
    COUNT(DISTINCT SESS_ID)                                       AS session_count,
    COUNT(*) FILTER (WHERE L0_status = 'Completed')              AS l0_success_count,
    COUNT(*) FILTER (WHERE L0_status != 'Completed'
                       AND L0_status IS NOT NULL)                 AS l0_failed_count,
    COUNT(*) FILTER (WHERE product_status = 'Completed')         AS dpgs_success_count,
    COUNT(*) FILTER (WHERE product_status != 'Completed'
                       AND product_status IS NOT NULL)            AS dpgs_failed_count,
    NOW()                                                         AS computed_at
FROM public.analytic_table
WITH DATA;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_summary ON public.mv_summary_counts ((computed_at::TEXT));

-- Product status breakdown
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_product_status AS
SELECT
    product_name,
    product_status,
    COUNT(*)                           AS count,
    COUNT(DISTINCT observation_id)     AS unique_observations
FROM public.analytic_table
WHERE product_name IS NOT NULL
GROUP BY product_name, product_status
WITH DATA;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_product ON public.mv_product_status (product_name, COALESCE(product_status, 'NULL'));

-- Cycle summary
CREATE MATERIALIZED VIEW IF NOT EXISTS public.mv_cycle_summary AS
SELECT
    CYCLE_NO,
    COUNT(DISTINCT observation_id)                           AS observations,
    COUNT(DISTINCT DATATAKE_ID)                              AS datatakes,
    COUNT(*) FILTER (WHERE L0_status = 'Completed')         AS l0_completed,
    MIN(CMD_SSAR_START_DATETIME)                             AS cycle_start,
    MAX(CMD_SSAR_START_DATETIME)                             AS cycle_end
FROM public.analytic_table
WHERE CYCLE_NO IS NOT NULL
GROUP BY CYCLE_NO
WITH DATA;
CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_cycle ON public.mv_cycle_summary (CYCLE_NO);