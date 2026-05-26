# NISAR Data Management System (NDMS) — Complete Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [System Architecture](#system-architecture)
3. [Complete Project Structure](#complete-project-structure)
4. [Database Schema & Tables](#database-schema--tables)
5. [Backend APIs & Routes](#backend-apis--routes)
6. [ETL Pipeline Flow](#etl-pipeline-flow)
7. [Filter & Search Flow](#filter--search-flow)
8. [High-Level Design (HLD)](#high-level-design-hld)
9. [Low-Level Design (LLD)](#low-level-design-lld)
10. [Flow Diagrams](#flow-diagrams)

---

## Project Overview

The NISAR Data Management System (NDMS) is a satellite observation analytics platform designed to ingest, transform, and visualize satellite imaging and reconnaissance data. It provides:

- **Real-time Dashboard**: Interactive map, charts, and data tables
- **Advanced Filtering**: Multi-criteria search across observations, RC configurations, sessions
- **ETL Pipeline**: Two-phase data ingestion (raw load → transform)
- **AI Chat Interface**: Natural language SQL queries
- **Performance Optimization**: Partitioned tables, materialized views, pre-aggregated caches

**Tech Stack:**
- **Backend**: Python Flask (5000), separate ETL service (5001)
- **Frontend**: Vanilla JavaScript, Leaflet.js, Chart.js
- **Databases**: PostgreSQL (analytics), MySQL + MariaDB (source)
- **Containers**: Docker Compose (5 services)

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (8080)                             │
│  - Leaflet Map    - Data Tables    - Charts    - AI Chat Widget    │
│  - Filter Panel   - CSV Export     - Pagination                    │
└──────────────────┬──────────────────────────────────────────────────┘
                   │ CORS-enabled HTTPS/HTTP
                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    BACKEND (5000) — Flask                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ /api/search          → Paginated observation table         │    │
│  │ /api/analytics       → Summary counts                       │    │
│  │ /api/rc_stats        → Pre-aggregated chart data            │    │
│  │ /api/map_polygons    → WKT geometries for map             │    │
│  │ /api/ai/query        → Text-to-SQL AI assistant           │    │
│  │ /api/etl/trigger     → Proxy to ETL service               │    │
│  │ /api/etl/status      → Read from etl_runs table            │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────┬──────────────────────────────────────────────────┘
                   │ psycopg2 / TCP 5432
                   ↓
┌──────────────────────────────────────────────────────────────────────┐
│              ETL SERVICE (5001) — Flask + Threading                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ POST /etl/trigger  → Runs Phase 1 + Phase 2 in background  │    │
│  │ GET  /etl/status   → Returns last run status               │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────┬────────────────────────┬─────────────────────────────┘
               │                        │
        ┌──────┴──────┐          ┌──────┴──────┐
        ↓             ↓          ↓             ↓
    ┌────────┐   ┌────────┐  ┌─────────┐  ┌──────────┐
    │ MySQL  │   │MariaDB │  │PostgreSQL│  │ PostgreSQL│
    │ (3308) │   │ (3307) │  │ (5432)  │  │ (5432)   │
    │        │   │        │  │ RAW     │  │ PUBLIC   │
    └────────┘   └────────┘  │ SCHEMA  │  │ANALYTIC  │
                             └─────────┘  │ TABLES   │
                                         └──────────┘
```

---

## Complete Project Structure

```
/workspaces/ndms/
│
├── README.md                          ← This file
├── schema.sql                         ← Source DB schemas (MySQL/MariaDB)
├── docker-compose.yml                 ← 5-container orchestration
│
├── frontend/
│   └── src/
│       ├── index.html                 ← Single page app entry
│       ├── css/
│       │   └── styles.css             ← Dashboard UI styles
│       └── js/
│           ├── api.js                 ← Centralized API client (fetch calls)
│           ├── main.js                ← App initialization & DOMContentLoaded
│           ├── components/
│           │   ├── filters.js         ← Filter UI state & collectFilters()
│           │   ├── map.js             ← Leaflet map, drawPolygons(), WKT parsing
│           │   ├── chart.js           ← Bar chart rendering (Chart.js)
│           │   ├── analytics_table.js ← Summary counts widget
│           │   ├── data_table.js      ← Paginated observations table
│           │   ├── ai_chat.js         ← AI chat UI, message history
│           │   └── etl_trigger.js     ← DEV ONLY: manual ETL trigger button
│           └── utils/
│               ├── pagination.js      ← Pagination UI logic
│               └── csv_export.js      ← Download analytics as CSV
│
├── backend/
│   ├── app.py                         ← Flask app entry, blueprint registration
│   ├── Dockerfile                     ← Python 3.10-slim, gunicorn
│   ├── requirements.txt               ← Dependencies (Flask, psycopg2, etc)
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── connection.py              ← get_db_connection() → psycopg2 pool
│   │   └── queries.py                 ← Centralized SQL queries, build_where_clause()
│   │
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── observations.py            ← GET /api/search (paginated table)
│   │   ├── analytics.py               ← GET /api/analytics (summary counts)
│   │   ├── charts.py                  ← GET /api/rc_stats (chart data)
│   │   ├── map.py                     ← GET /api/map_polygons (WKT geometries)
│   │   ├── etl.py                     ← GET /api/etl/status (audit table)
│   │   └── ai.py                      ← POST /api/ai/query (text-to-SQL)
│   │
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py              ← answer_query() → LLM integration stub
│       ├── analytics_service.py       ← get_analytics_counts() → mv_summary_counts
│       └── pagination_service.py      ← get_page_params(), calc_total_pages()
│
├── etl/
│   ├── Dockerfile                     ← Python 3.10-slim, gunicorn 1 worker
│   ├── etl_service.py                 ← Flask app: /etl/trigger, /etl/status, /health
│   ├── requirements.txt               ← Dependencies (Flask, psycopg2, PyMySQL)
│   │
│   └── core/
│       ├── __init__.py
│       ├── db.py                      ← Connection factories for MySQL/MariaDB/PG
│       ├── phase1_raw_load.py         ← Dynamic discovery, batch copy (MySQL/MariaDB → PG raw schema)
│       └── phase2_transform.py        ← CTE pipeline, UNION unpivot, blue-green swap
│
└── postgres/
    └── init/
        └── 01_schema.sql              ← Auto-run on first postgres start
                                        Creates: raw schema, etl_runs, analytic_table (partitioned),
                                        rc_cache, 11 indexes, 3 materialized views
```

---

## Database Schema & Tables

### PostgreSQL Schemas

#### **1. `public` Schema — Live Analytics Tables**

The `public` schema contains tables and views that the dashboard and API read from during operation.

##### **A. analytic_table (Partitioned, Read-Optimized)**

```sql
CREATE TABLE public.analytic_table (
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
```

**Partitions (auto-created):**
- `analytic_2023` → 2023-01-01 to 2024-01-01
- `analytic_2024` → 2024-01-01 to 2025-01-01
- `analytic_2025` → 2025-01-01 to 2026-01-01
- `analytic_2026` → 2026-01-01 to 2027-01-01
- `analytic_2027` → 2027-01-01 to 2028-01-01
- `analytic_default` → Catch-all for dates outside ranges

**Why Partitioning?**
- Query "show 2024 data only" → PostgreSQL automatically excludes 2025-2027 partitions
- Partition pruning happens at plan time — no index needed
- VACUUM and ANALYZE run faster per partition
- Index bloat is isolated to individual partitions

**FILLFACTOR = 70:**
- Reserves 30% free space on each page
- When a row is updated (e.g., product_status changes), PostgreSQL can write the new version on the same page
- Avoids index updates (called Heap Only Tuple - HOT update)
- Reduces table bloat for frequently-updated columns

##### **B. Indexes on analytic_table**

```sql
-- Identity lookup
CREATE INDEX idx_at_obs_id       ON public.analytic_table (observation_id);
CREATE INDEX idx_at_obs_key      ON public.analytic_table (obs_key);

-- Time-range queries (dashboard filter: date range)
CREATE INDEX idx_at_time_brin    ON public.analytic_table USING BRIN (CMD_SSAR_START_DATETIME)
    WITH (pages_per_range = 32);  -- 32 pages = ~1MB ranges
CREATE INDEX idx_at_time_btree   ON public.analytic_table (CMD_SSAR_START_DATETIME);

-- Composite: (RC ID + time) for joined lookups
CREATE INDEX idx_at_cfg_time     ON public.analytic_table (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME);

-- Filter widget: L0 status, product type, cycle
CREATE INDEX idx_at_l0           ON public.analytic_table (L0_status);
CREATE INDEX idx_at_product      ON public.analytic_table (product_name);
CREATE INDEX idx_at_cycle        ON public.analytic_table (CYCLE_NO);
CREATE INDEX idx_at_datatake     ON public.analytic_table (DATATAKE_ID);

-- Covering index for WKT polygon lookup
CREATE INDEX idx_at_polygon      ON public.analytic_table (observation_id) 
    WHERE WKT_POLYGON IS NOT NULL;  -- Partial index: only rows with geometry

-- Covering index for common queries (includes additional columns to avoid heap lookups)
CREATE INDEX idx_at_covering     ON public.analytic_table (
    CMD_SSAR_START_DATETIME DESC, 
    observation_id, 
    product_name
) INCLUDE (SSAR_CONFIG_ID, L0_status, CYCLE_NO, TRACK, FRAME, DATATAKE_ID);
```

**Index Types:**
- **B-tree** (standard): Fast for equality and range queries (>, <, BETWEEN)
- **BRIN** (Block Range Index): Very compact for sorted columns; scans fewer blocks
- **Partial**: Only indexes rows where WKT_POLYGON IS NOT NULL (saves space)
- **Covering**: Includes additional columns; query can be answered without heap lookup

##### **C. rc_cache — Pre-aggregated Chart Data**

```sql
CREATE TABLE public.rc_cache (
    id           SERIAL PRIMARY KEY,
    period_type  TEXT,              -- 'monthly' | 'weekly' | 'yearly'
    period_label TEXT,              -- '2024-01' | '2024-W01' | '2024'
    rc_id        TEXT,              -- SSAR_CONFIG_ID
    count        INTEGER,           -- observation count
    updated_at   TIMESTAMP
);
CREATE INDEX idx_rc_lookup ON public.rc_cache (period_type, period_label);
```

**Purpose:** Chart loading is instant (no aggregation at query time).

##### **D. etl_runs — ETL Audit Table**

```sql
CREATE TABLE public.etl_runs (
    id                  SERIAL PRIMARY KEY,
    status              TEXT,                -- 'SUCCESS' | 'FAILED'
    phase               TEXT,                -- 'RAW_LOAD' | 'TRANSFORM'
    start_time          TIMESTAMP,           -- When ETL started
    end_time            TIMESTAMP,           -- When ETL ended
    last_processed_time TIMESTAMP,           -- Watermark for next incremental run
    rows_processed      INTEGER,             -- Row count
    error_message       TEXT                 -- Failure reason
);
```

**Used By:**
- `/api/etl/status` endpoint → shows last run in dashboard header
- ETL service → watermark filter for incremental loads

##### **E. Materialized Views**

**mv_summary_counts** (refreshed after Phase 2)

```sql
CREATE MATERIALIZED VIEW public.mv_summary_counts AS
SELECT
    COUNT(DISTINCT observation_id)  AS observation_count,
    COUNT(DISTINCT DATATAKE_ID)     AS datatake_count,
    COUNT(DISTINCT SSAR_CONFIG_ID)  AS rc_count,
    COUNT(DISTINCT SESS_ID)         AS session_count,
    COUNT(*) FILTER (WHERE L0_status = 'Completed') AS l0_success_count,
    COUNT(*) FILTER (WHERE product_status = 'Ready') AS product_ready_count;
```

**Used By:** `/api/analytics` → Analytics Summary widget

**Why Materialized Views?**
- Dashboard loads instantly (pre-computed)
- Refreshed CONCURRENTLY → doesn't lock the table during refresh
- Run manually after ETL Phase 2 completes

#### **2. `raw` Schema — ETL Staging Area**

Created by Phase 1, temporary tables that hold MySQL/MariaDB data as-is (no transformation).

```sql
CREATE SCHEMA raw;

-- Phase 1 copies MySQL tables to raw schema with _mysql suffix
raw.cop_observation_mysql
raw.scene_mysql
raw.nisar_product_info_mysql
-- ... (all other MySQL tables)

-- Phase 1 copies MariaDB tables with _mariadb suffix
raw.cop_observation_mariadb
raw.scene_mariadb
raw.nisar_product_info_mariadb
-- ... (all other MariaDB tables)
```

**Note:** Raw tables are NOT blue-green swapped; they're always recreated from scratch each ETL run.

### Source Databases (MySQL & MariaDB)

**Not read by dashboard.** Only used by ETL Phase 1 to copy data into PostgreSQL.

#### **MySQL Tables** (3308)
- cop_observation
- scene
- nisar_product_info
- nisar_imaging_data
- nisar_replica_data
- session_observation
- observation
- CRID_NISAR_INFO
- ERRORCODES
- MW01_LOCAL_WO
- NISAR_WO_TIMEOUT
- PRODUCTINFONISAR
- ... (and others defined in schema.sql)

#### **MariaDB Tables** (3307)
Same structure as MySQL (typically replicated source system).

---

## Backend APIs & Routes

All routes return JSON and use PostgreSQL `public` schema.

### **1. GET /api/search** — Paginated Observation Table

**File:** [backend/routes/observations.py](backend/routes/observations.py)

**Query String Parameters:**
```
?page=1&limit=25&cmd_start=2024-01-01&cmd_end=2024-12-31
  &Session_id=ssid_001&Ob_id=OBS%&Rc_id=RC001&L0_status=Completed
  &cycle=5&WO_id=WO%
```

**Filter Logic:** [backend/db/queries.py](backend/db/queries.py) → `build_where_clause()`

```python
def build_where_clause(filters: dict) -> tuple[str, list]:
    """
    Filters:
    - cmd_start, cmd_end     → CMD_SSAR_START_DATETIME / END_DATETIME range
    - Ob_id                  → LIKE observation_id (wildcards: *)
    - Session_id             → LIKE SESS_ID (auto-prefix ssid_ if missing)
    - Rc_id                  → exact SSAR_CONFIG_ID match
    - L0_status              → case-insensitive match (Completed/Processing/etc)
    - cycle                  → exact CYCLE_NO match
    - WO_id                  → LIKE MASTERWORK_ORDER_ID (wildcards: *)
    
    Returns: (WHERE_clause_sql, param_list)
    """
```

**Response:**
```json
{
  "observations": [
    {
      "REFOBS_ID": "OBS_20240115_001",
      "SSAR_CONFIG_ID": "RC001",
      "SESS_ID": "ssid_20240115",
      "DATATAKE_ID": "DT_20240115_A",
      "CMD_SSAR_START_DATETIME": "2024-01-15T10:30:45",
      "CMD_SSAR_END_DATETIME": "2024-01-15T11:00:45",
      "L0_status": "Completed",
      "CYCLE_NO": 5,
      "TRACK": 12,
      "FRAME": 8,
      ...
    }
  ],
  "page": 1,
  "total_pages": 42,
  "total_rows": 1050
}
```

**Database Query:**
```sql
SELECT observation_id, SSAR_CONFIG_ID, SESS_ID, ... FROM public.analytic_table
WHERE 1=1
  AND CMD_SSAR_START_DATETIME >= %s  -- if cmd_start provided
  AND SSAR_CONFIG_ID = %s            -- if Rc_id provided
  AND LOWER(L0_status) = %s          -- if L0_status provided
  ...
ORDER BY CMD_SSAR_START_DATETIME DESC
LIMIT %s OFFSET %s;
```

---

### **2. GET /api/analytics** — Summary Counts

**File:** [backend/routes/analytics.py](backend/routes/analytics.py)
**Service:** [backend/services/analytics_service.py](backend/services/analytics_service.py)

**Query String Parameters:**
```
?cmd_start=2024-01-01&cmd_end=2024-12-31&Rc_id=RC001
```

**Response:**
```json
{
  "observation_count": 1050,
  "datatake_count": 234,
  "rc_count": 42,
  "session_count": 89,
  "l0_success_count": 950,
  "product_ready_count": 1005
}
```

**Database Query:**
```sql
SELECT
    COUNT(DISTINCT observation_id) as observation_count,
    COUNT(DISTINCT DATATAKE_ID) as datatake_count,
    ...
FROM public.analytic_table
WHERE 1=1 AND CMD_SSAR_START_DATETIME >= %s ...;
```

---

### **3. GET /api/rc_stats** — Chart Data (Pre-aggregated)

**File:** [backend/routes/charts.py](backend/routes/charts.py)

**Query String Parameters:**
```
?type=monthly   -- 'monthly' | 'weekly' | 'yearly'
```

**Response:**
```json
[
  { "label": "2024-01", "count": 85 },
  { "label": "2024-02", "count": 92 },
  { "label": "2024-03", "count": 78 },
  ...
]
```

**Query Strategy:**
1. Try `rc_cache` table first (pre-aggregated, instant)
2. Fallback to direct query on `analytic_table` if cache is empty

**Database Queries:**
```sql
-- Primary (fast cache hit)
SELECT period_label AS label, SUM(count) AS count
FROM public.rc_cache
WHERE period_type = 'monthly'
GROUP BY period_label
ORDER BY period_label ASC;

-- Fallback (direct aggregation)
SELECT TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') as label, COUNT(*) as count
FROM public.analytic_table
WHERE CMD_SSAR_START_DATETIME IS NOT NULL
GROUP BY label
ORDER BY label;
```

---

### **4. GET /api/map_polygons** — WKT Geometries for Leaflet

**File:** [backend/routes/map.py](backend/routes/map.py)

**Query String Parameters:**
```
?cmd_start=2024-01-01&cmd_end=2024-12-31&SSAR_CONFIG_ID=RC001
```

**Response:**
```json
{
  "polygons": [
    {
      "observation_id": "OBS_20240115_001",
      "wkt_polygon": "POLYGON((35.5 51.2, 35.8 51.2, 35.8 51.5, 35.5 51.5, 35.5 51.2))"
    },
    ...
  ]
}
```

**Database Query:**
```sql
SELECT DISTINCT ON (observation_id) observation_id, WKT_POLYGON
FROM public.analytic_table
WHERE WKT_POLYGON IS NOT NULL
  AND CMD_SSAR_START_DATETIME >= %s
  ...
ORDER BY observation_id DESC;
```

**Frontend Processing:**
- WKT parser converts `POLYGON(...)` to Leaflet `L.polygon()` objects
- Each polygon is drawn on the map with click handlers

---

### **5. POST /api/ai/query** — Text-to-SQL Assistant

**File:** [backend/routes/ai.py](backend/routes/ai.py)
**Service:** [backend/services/ai_service.py](backend/services/ai_service.py)

**Request:**
```json
{
  "query": "How many observations are completed?"
}
```

**Response:**
```json
{
  "question": "How many observations are completed?",
  "generated_sql": "SELECT COUNT(DISTINCT observation_id) FROM analytic_table WHERE L0_status = 'Completed';",
  "result": [
    { "count": 950 }
  ]
}
```

**Flow:**
1. Load `analytic_table` schema from postgres information_schema
2. Build prompt with schema + few-shot examples + user question
3. Call LLM (stub: can be Ollama/OpenAI/Gemini)
4. Extract generated SQL from LLM response
5. Validate SQL (no INSERT/UPDATE/DELETE, only allowed tables)
6. Execute read-only query on postgres
7. Return results as JSON

**Security Checks:**
- Blocked keywords: INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, GRANT, REVOKE
- Allowed tables: analytic_table, rc_cache only
- Query must start with SELECT
- Result capped to 100 rows

---

### **6. GET /api/etl/status** — Last ETL Run Status

**File:** [backend/routes/etl.py](backend/routes/etl.py)

**Response:**
```json
{
  "status": "SUCCESS",
  "phase": "TRANSFORM",
  "time": "2024-01-15 14:32:10",  -- IST
  "rows_processed": 52400,
  "error": null
}
```

**Query:**
```sql
SELECT status, phase, start_time, end_time, rows_processed, error_message
FROM public.etl_runs
ORDER BY id DESC
LIMIT 1;
```

**In Dashboard:** Shows ETL health in header (green ✓ if SUCCESS, red ✗ if FAILED)

---

### **7. POST /api/etl/trigger** — Start ETL Pipeline

**File:** [backend/routes/etl.py](backend/routes/etl.py)

**Request:** No body required

**Response:**
```json
{
  "status": "triggered",
  "message": "ETL pipeline started in background"
}
```

**Behavior:**
- Proxies request to ETL service (`http://pipeline_etl:5001/etl/trigger`)
- ETL runs in background thread (doesn't block response)
- Frontend polls `/api/etl/status` to monitor progress

---

## ETL Pipeline Flow

### **Phase 1: Raw Load** (`core/phase1_raw_load.py`)

**Objective:** Copy all tables from MySQL & MariaDB into PostgreSQL `raw` schema as-is.

```
MySQL (3308)                    PostgreSQL (5432)
┌──────────────────┐           ┌──────────────────────┐
│ cop_observation  │──copy────→│ raw.cop_observation_mysql
│ scene            │           │ raw.scene_mysql
│ nisar_product... │           │ raw.nisar_product_info_mysql
│ (25+ tables)     │           │ ...
└──────────────────┘           └──────────────────────┘

MariaDB (3307)
┌──────────────────┐           ┌──────────────────────┐
│ cop_observation  │──copy────→│ raw.cop_observation_mariadb
│ scene            │           │ raw.scene_mariadb
│ nisar_product... │           │ raw.nisar_product_info_mariadb
│ (25+ tables)     │           │ ...
└──────────────────┘           └──────────────────────┘
```

**Process:**

1. **Dynamic Table Discovery:**
   ```python
   for source_db in [mysql_conn, mariadb_conn]:
       table_names = get_table_names(source_db)  # SHOW TABLES
       for table_name in table_names:
           columns = get_columns(source_db, table_name)  # DESCRIBE
   ```

2. **Type Mapping (MySQL → PostgreSQL):**
   ```python
   MYSQL_TO_PG = {
       "varchar": "TEXT",
       "int": "INTEGER",
       "datetime": "TIMESTAMP",
       "blob": "BYTEA",
       ...
   }
   ```

3. **Batch Copy (500 rows at a time):**
   ```python
   for i in range(0, total_rows, BATCH_SIZE=500):
       rows = SELECT * FROM mysql_table LIMIT 500 OFFSET i
       INSERT INTO raw.{table}_mysql VALUES (rows)
   ```

4. **Record in etl_runs:**
   ```sql
   INSERT INTO etl_runs (status, phase, rows_processed, ...)
   VALUES ('SUCCESS', 'RAW_LOAD', 123456, ...)
   ```

**Watermark (Incremental Load):**
- First run: loads ALL rows
- Subsequent runs: `WHERE source_modified_time > last_processed_time - 5min` (5-min overlap buffer)
- Prevents duplicate loads if records are updated between ETL runs

---

### **Phase 2: Transform & Optimize** (`core/phase2_transform.py`)

**Objective:** Build `analytic_table_new` (partitioned, indexed) from raw data, then atomically swap with live `analytic_table`.

```
raw schema (Phase 1 output)          public schema (Phase 2 output)
┌────────────────────────────────┐   ┌───────────────────────────────┐
│ raw.cop_observation_mysql      │   │
│ raw.cop_observation_mariadb    │───→ TRANSFORM PIPELINE:
│ raw.scene_mysql                │   │ 1. CTE pipeline (cop_clean)
│ raw.scene_mariadb              │   │ 2. Cross-DB join
│ raw.nisar_product_info_*       │   │ 3. UNION ALL unpivot (8 products)
│ ... (25+ raw tables)           │   │ 4. Denormalization
└────────────────────────────────┘   │
                                      │
                                      ↓
                                    ┌───────────────────────┐
                                    │ analytic_table_new    │
                                    │ (shadow, invisible)   │
                                    │ - Partitioned (yearly)│
                                    │ - 11 indexes          │
                                    │ - FILLFACTOR=70       │
                                    └───────────────────────┘
                                    
                                    BLUE-GREEN SWAP:
                                    analytic_table     (live)
                                    ↓
                                    analytic_old       (step 1: rename)
                                    ↓
                                    analytic_table_new (step 2: rename to _table)
                                    ↓
                                    DROP analytic_old  (step 3: cleanup)
```

**Detailed Transform Process:**

```sql
-- Step 1: Get watermark for incremental load
SELECT last_processed_time FROM etl_runs WHERE status='SUCCESS' ORDER BY id DESC LIMIT 1;
-- Returns: 2024-01-10 09:00:00 (so load records from 2024-01-10 08:55:00 onwards)

-- Step 2: Create shadow table (partitioned, FILLFACTOR=70)
DROP TABLE IF EXISTS public.analytic_table_new CASCADE;
CREATE TABLE public.analytic_table_new (
    observation_id          TEXT,
    obs_key                 TEXT,
    SESS_ID                 TEXT,
    CMD_SSAR_START_DATETIME TIMESTAMP,
    ...
)
PARTITION BY RANGE (CMD_SSAR_START_DATETIME)
WITH (FILLFACTOR = 70);

-- Create partitions for shadow table
CREATE TABLE analytic_2024 PARTITION OF analytic_table_new
    FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
CREATE TABLE analytic_2025 PARTITION OF analytic_table_new
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
-- ... (more partitions)

-- Step 3: CTE Pipeline - Extract & Join
WITH cop_clean AS (
    SELECT
        COALESCE(m.REFOBS_ID, d.REFOBS_ID) as observation_id,
        m.SSAR_CONFIG_ID,
        m.CMD_SSAR_START_DATETIME,
        ...
    FROM raw.cop_observation_mysql m
    LEFT JOIN raw.scene_mysql s ON m.REFOBS_ID = s.observation_ref
    WHERE m.CMD_SSAR_START_DATETIME >= '2024-01-10 08:55:00'
)
base AS (
    -- Same from MariaDB
    SELECT ... FROM raw.cop_observation_mariadb d
    LEFT JOIN raw.scene_mariadb ...
    WHERE ...
),
unpivoted AS (
    -- UNION ALL: 8 SAR product types
    SELECT
        observation_id, SSAR_CONFIG_ID, ..., 'RIFG' as product_name, ... FROM cop_clean
    UNION ALL
    SELECT
        ..., 'RIFF' as product_name, ... FROM base
    UNION ALL
    -- ... (6 more product types)
)
INSERT INTO public.analytic_table_new
SELECT * FROM unpivoted;

-- Step 4: Create Indexes on shadow table
CREATE INDEX idx_at_obs_id ON public.analytic_table_new (observation_id);
CREATE INDEX idx_at_time_btree ON public.analytic_table_new (CMD_SSAR_START_DATETIME);
CREATE INDEX idx_at_covering ON public.analytic_table_new (...) INCLUDE (...);
-- ... (8 more indexes)

-- Step 5: Build RC Cache (pre-aggregated chart data)
DELETE FROM public.rc_cache WHERE period_type IN ('monthly', 'weekly', 'yearly');
INSERT INTO public.rc_cache (period_type, period_label, rc_id, count, updated_at)
SELECT
    'monthly' as period_type,
    TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') as period_label,
    SSAR_CONFIG_ID as rc_id,
    COUNT(*) as count,
    NOW()
FROM public.analytic_table_new
GROUP BY period_type, period_label, rc_id;
-- Similar for weekly and yearly

-- Step 6: Refresh Materialized Views
REFRESH MATERIALIZED VIEW CONCURRENTLY public.mv_summary_counts;

-- Step 7: Blue-Green Swap (all in one transaction)
BEGIN;
  ALTER TABLE IF EXISTS public.analytic_table RENAME TO analytic_old;
  ALTER TABLE public.analytic_table_new RENAME TO analytic_table;
  DROP TABLE IF EXISTS public.analytic_old CASCADE;
COMMIT;

-- Step 8: Vacuum & Analyze (outside transaction)
VACUUM ANALYZE public.analytic_table;

-- Step 9: Record success
INSERT INTO etl_runs (status, phase, last_processed_time, rows_processed)
VALUES ('SUCCESS', 'TRANSFORM', NOW(), row_count);
```

**Why Blue-Green Swap?**
- Dashboard never sees missing `analytic_table`
- All three rename operations are atomic (one COMMIT makes all three land together)
- If crash occurs, rollback restores everything automatically
- Zero downtime swap

**Why FILLFACTOR=70?**
- Reserves 30% free page space
- When product_status changes (frequently), PostgreSQL writes new version on same page (HOT update)
- Avoids updating all indexes
- Reduces table bloat

---

## Filter & Search Flow

### **User Interaction Flow**

```
Frontend UI
┌─────────────────────────────────────────────────┐
│ User Input: Date Range, RC ID, L0 Status, etc  │
│ ↓                                               │
│ filters.js: collectFilters() returns object:   │
│ {                                               │
│   cmd_start: "2024-01-01",                      │
│   cmd_end: "2024-12-31",                        │
│   Rc_id: "RC001",                               │
│   L0_status: "Completed",                       │
│   Session_id: "001"  (auto-prefixed → ssid_)   │
│   Ob_id: "OBS*"      (wildcard)                │
│ }                                               │
│                                                 │
│ ↓                                               │
│ api.js: API.search(filters, page) calls        │
│ fetch("http://localhost:5001/search?..." + URLSearchParams)
│                                                 │
└─────────────────────────────────────────────────┘
        ↓
    Backend API
┌─────────────────────────────────────────────────┐
│ GET /api/search?cmd_start=...&Rc_id=...&...    │
│                                                 │
│ observations.py: search()                       │
│ ├─ get_page_params(filters) → page, limit, offset
│ ├─ build_where_clause(filters)                 │
│ │  └─ Returns: (WHERE_sql, params_list)        │
│ ├─ SELECT COUNT(*) FROM analytic_table         │
│ │  WHERE 1=1 AND ... (for total_rows)         │
│ ├─ SELECT * FROM analytic_table                │
│ │  WHERE 1=1 AND ... LIMIT 25 OFFSET 0        │
│ └─ Return JSON with observations, pagination   │
│                                                 │
└─────────────────────────────────────────────────┘
        ↓
    Database
┌─────────────────────────────────────────────────┐
│ PostgreSQL (5432) — analytic_table              │
│                                                 │
│ Query Execution:                                │
│ 1. Partition Pruning:                           │
│    Only 2024 partition selected (based on date) │
│                                                 │
│ 2. Index Selection (Query Planner):             │
│    If Rc_id + date range → idx_at_cfg_time     │
│    If only date range    → idx_at_time_btree   │
│    If L0_status filter   → idx_at_l0           │
│                                                 │
│ 3. Bitmap Index Scan / Seq Scan                 │
│    Merge with remaining WHERE conditions       │
│                                                 │
│ 4. Sort by CMD_SSAR_START_DATETIME DESC        │
│ 5. LIMIT 25 OFFSET 0                           │
│                                                 │
│ Returns: 25 rows + total count (separate query)│
└─────────────────────────────────────────────────┘
        ↓
    Frontend UI
┌─────────────────────────────────────────────────┐
│ data_table.js: renderObservationTable()         │
│ ├─ Render 25 rows in HTML table                 │
│ ├─ Render pagination (page 1 of 42)            │
│ ├─ Enable "Next", "Previous" buttons           │
│ └─ Update status: "Showing 1-25 of 1050"      │
└─────────────────────────────────────────────────┘
```

### **Filter Function Mapping**

| Filter Widget | Query Parameter | Database Column | Operation |
|---|---|---|---|
| Date Range (From/To) | cmd_start, cmd_end | CMD_SSAR_START_DATETIME | Range query (>=, <=) |
| Observation ID | Ob_id | observation_id | LIKE with wildcard (*) |
| Session ID | Session_id | SESS_ID | LIKE, auto-prefix "ssid_" |
| RC/SSAR Config | Rc_id | SSAR_CONFIG_ID | Exact match (=) |
| L0 Status | L0_status | L0_status | Case-insensitive LIKE |
| Cycle Number | cycle | CYCLE_NO | Exact match (=) |
| Work Order ID | WO_id | MASTERWORK_ORDER_ID | LIKE with wildcard (*) |

### **Filter Implementation** (`build_where_clause()`)

```python
def build_where_clause(filters: dict) -> tuple[str, list]:
    where = "WHERE 1=1"
    params = []
    
    # Date range
    if filters.get("cmd_start"):
        where += " AND a.CMD_SSAR_START_DATETIME >= %s"
        params.append(filters["cmd_start"].replace("T", " "))
    
    if filters.get("cmd_end"):
        where += " AND a.CMD_SSAR_END_DATETIME <= %s"
        params.append(filters["cmd_end"].replace("T", " "))
    
    # Observation ID (wildcard)
    if filters.get("Ob_id"):
        val = filters["Ob_id"].strip().replace("*", "%")
        where += " AND a.observation_id LIKE %s"
        params.append(val)
    
    # Session ID (auto-prefix ssid_, wildcard)
    if filters.get("Session_id"):
        val = filters["Session_id"].strip().lower()
        if not val.startswith("ssid_"):
            val = "ssid_" + val
        val = val.replace("*", "%")
        where += " AND a.SESS_ID LIKE %s"
        params.append(val)
    
    # RC ID (exact)
    if filters.get("Rc_id"):
        where += " AND a.SSAR_CONFIG_ID = %s"
        params.append(filters["Rc_id"].strip())
    
    # L0 Status (case-insensitive)
    if filters.get("L0_status"):
        where += " AND LOWER(a.L0_status) = %s"
        params.append(filters["L0_status"].strip().lower())
    
    # ... (more filters)
    
    return where, params
```

---

## High-Level Design (HLD)

### **System Components**

```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                       │
│  Frontend (Vue.js)      Dashboard (Leaflet Map + Tables)   │
└──────────────────────────┬──────────────────────────────────┘
                           │ RESTful API (JSON)
┌──────────────────────────┴──────────────────────────────────┐
│                    APPLICATION LAYER                        │
│  Backend (Flask)        7 REST endpoints                    │
│  - /api/search          - /api/analytics                    │
│  - /api/rc_stats        - /api/map_polygons                 │
│  - /api/ai/query        - /api/etl/status                   │
│  ETL Service (Flask)    2 ETL endpoints                     │
│  - POST /etl/trigger    - GET /etl/status                   │
└──────────────────────────┬──────────────────────────────────┘
                    │
        ┌───────────┼────────────┐
        ↓           ↓            ↓
┌─────────────┐ ┌──────────┐ ┌──────────┐
│   DATA LAYER│ │  SOURCE  │ │ ANALYTICS│
│  PostgreSQL │ │   DBS    │ │   DB     │
│  Port 5432  │ │          │ │          │
│             │ │  MySQL   │ │PostgreSQL│
│ - raw       │ │ (3308)   │ │(5432)    │
│ - public    │ │          │ │          │
│             │ │ MariaDB  │ │- raw sch.│
│Schemas:     │ │ (3307)   │ │- public  │
│- raw        │ │          │ │ schema   │
│- public     │ │(source)  │ │(analytics│
│             │ │          │ │)         │
└─────────────┘ └──────────┘ └──────────┘
```

### **Data Flow Architecture**

```
┌─────────────────────────────────────────────────────────────────┐
│                    ETL ORCHESTRATION (Phase 1+2)               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Phase 1: Raw Load                                              │
│  ─────────────────────────────────────────────────────────────  │
│  MySQL ──[Discovery + Copy]──→  raw.{table}_mysql              │
│  MariaDB ──[Discovery + Copy]─→  raw.{table}_mariadb           │
│  (Type mapping, batch processing, watermark filter)            │
│                                                                 │
│  Phase 2: Transform & Optimize                                  │
│  ─────────────────────────────────────────────────────────────  │
│  raw schema ──[CTE + JOIN + UNION]──→ analytic_table_new        │
│  (Denormalize, index, partition, rc_cache, mv refresh)         │
│  ──[Blue-Green Swap]──→ analytic_table (LIVE)                  │
│                                                                 │
│  ETL Audit                                                       │
│  ─────────────────────────────────────────────────────────────  │
│  etl_runs (status, phase, rows, watermark)                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │   QUERY OPTIMIZATION      │
        ├───────────────────────────┤
        │ Indexes (11 types)        │
        │ Partitioning (yearly)     │
        │ Materialized Views        │
        │ RC Cache (pre-agg)        │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  LIVE ANALYTICS DATABASE  │
        ├───────────────────────────┤
        │ analytic_table            │
        │ rc_cache                  │
        │ mv_summary_counts         │
        │ etl_runs                  │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  QUERY LAYER (Backend)    │
        ├───────────────────────────┤
        │ /api/search               │
        │ /api/analytics            │
        │ /api/rc_stats             │
        │ /api/map_polygons         │
        │ /api/ai/query             │
        └───────────────────────────┘
                    ↓
        ┌───────────────────────────┐
        │  DASHBOARD (Frontend)     │
        ├───────────────────────────┤
        │ Data Table (filtered)     │
        │ Leaflet Map               │
        │ Bar Charts                │
        │ Analytics Summary         │
        │ AI Chat Widget            │
        └───────────────────────────┘
```

---

## Low-Level Design (LLD)

### **1. Filter Search (Detailed Flow)**

```
User clicks "Apply Filters"
    ↓
collectFilters() → {cmd_start, cmd_end, Rc_id, L0_status, ...}
    ↓
API.search(filters, page=1)
    ↓
fetch("GET /api/search?cmd_start=...&cmd_end=...&Rc_id=...")
    ↓
Backend: observations.py → search()
    │
    ├─ get_page_params(filters)
    │  └─ page = filters.get("page", 1)
    │  └─ limit = 25
    │  └─ offset = (page - 1) * limit
    │
    ├─ build_where_clause(filters)
    │  └─ For each filter:
    │     - cmd_start: WHERE ... >= %s
    │     - Rc_id:     WHERE ... = %s (exact)
    │     - L0_status: WHERE LOWER(...) = %s (case-insensitive)
    │     - Ob_id:     WHERE ... LIKE %s (wildcard)
    │     - Session_id: WHERE ... LIKE %s (with ssid_ prefix)
    │  └─ Returns: (where_sql, params=[v1, v2, ...])
    │
    ├─ Execute COUNT query:
    │  SELECT COUNT(*) FROM analytic_table
    │  WHERE 1=1 AND cmd_start >= v1 AND Rc_id = v2 ...
    │  └─ Returns: total_rows = 1050
    │  └─ total_pages = ceil(1050 / 25) = 42
    │
    ├─ Execute data query:
    │  SELECT observation_id, SSAR_CONFIG_ID, ... 
    │  FROM analytic_table
    │  WHERE 1=1 AND cmd_start >= v1 AND Rc_id = v2 ...
    │  ORDER BY CMD_SSAR_START_DATETIME DESC
    │  LIMIT 25 OFFSET 0
    │  └─ Returns: 25 rows
    │
    ├─ Query Execution (PostgreSQL):
    │  1. Parse filter conditions
    │  2. Partition pruning: only 2024 partition (based on date range)
    │  3. Index selection:
    │     - If Rc_id + date: use idx_at_cfg_time (composite index)
    │     - If date only:    use idx_at_time_btree (BRIN faster for range)
    │     - If L0_status:    use idx_at_l0 (partial index)
    │  4. Bitmap Scan / Sequential Scan on filtered rows
    │  5. Filter remaining conditions (wildcard LIKE)
    │  6. Sort DESC by date
    │  7. Apply LIMIT 25 OFFSET 0
    │
    └─ Return JSON:
       {
         "observations": [
           {
             "observation_id": "OBS_20240115_001",
             "SSAR_CONFIG_ID": "RC001",
             ...
           }
         ],
         "page": 1,
         "total_pages": 42,
         "total_rows": 1050
       }

↓

Frontend: data_table.js → renderObservationTable()
    ├─ Render HTML table with 25 rows
    ├─ Render pagination buttons (Previous, Next)
    ├─ Show "Showing 1-25 of 1,050 observations"
    └─ Attach click handlers for sorting, row details

↓

User sees filtered results on dashboard
```

### **2. ETL Trigger (Detailed Flow)**

```
User clicks "Run ETL" button (frontend)
    ↓
etl_trigger.js → API.triggerEtl()
    ↓
fetch("POST http://localhost:5001/etl/trigger")
    ↓
Backend (app.py): POST /api/etl/trigger
    ├─ Proxy to ETL service: requests.post("http://pipeline_etl:5001/etl/trigger")
    └─ Return immediately (don't wait for ETL to finish)
    
↓

ETL Service (etl_service.py): run_full_etl()
    │
    ├─ Start threading.Thread(target=run_full_etl, daemon=True)
    │  (Runs in background, doesn't block HTTP response)
    │
    ├─ ═════════ PHASE 1: RAW LOAD ═════════
    │  │
    │  ├─ Call run_phase1():
    │  │  │
    │  │  ├─ MySQL Connection: get_mysql_conn()
    │  │  │  ├─ SHOW TABLES → [cop_observation, scene, ...]
    │  │  │  └─ For each table:
    │  │  │     ├─ DESCRIBE table → get columns + types
    │  │  │     ├─ Map MySQL types → PostgreSQL types
    │  │  │     ├─ CREATE TABLE raw.{table}_mysql (cols)
    │  │  │     └─ SELECT * in batches (500 rows):
    │  │  │        ├─ OFFSET 0: rows 1-500 → INSERT into postgres
    │  │  │        ├─ OFFSET 500: rows 501-1000 → INSERT
    │  │  │        └─ ... (repeat until last batch < 500)
    │  │  │
    │  │  ├─ MariaDB Connection: get_mariadb_conn()
    │  │  │  (Same process, creates raw.{table}_mariadb tables)
    │  │  │
    │  │  └─ Returns: {mysql_rows: 123456, mariadb_rows: 234567, total: 358023}
    │  │
    │  ├─ Record Phase 1 in etl_runs:
    │  │  INSERT INTO etl_runs
    │  │  (status, phase, start_time, rows_processed)
    │  │  VALUES ('SUCCESS', 'RAW_LOAD', '2024-01-15 10:00:00', 358023)
    │  │
    │  └─ If Phase 1 FAILS:
    │     ├─ Log error
    │     ├─ Record FAILED status in etl_runs
    │     └─ Return (Phase 2 does not run)
    │
    ├─ ═════════ PHASE 2: TRANSFORM & OPTIMIZE ═════════
    │  │
    │  ├─ Call run_phase2():
    │  │  │
    │  │  ├─ Get watermark (last successful etl_runs.last_processed_time):
    │  │  │  SELECT last_processed_time FROM etl_runs
    │  │  │  WHERE status='SUCCESS' ORDER BY id DESC LIMIT 1
    │  │  │  └─ Returns: 2024-01-10 09:00:00 (subtract 5min buffer → 08:55:00)
    │  │  │
    │  │  ├─ Create shadow table: analytic_table_new
    │  │  │  ├─ Drop if exists: DROP TABLE analytic_table_new
    │  │  │  ├─ Create partitioned table:
    │  │  │  │  CREATE TABLE analytic_table_new (...) 
    │  │  │  │  PARTITION BY RANGE (CMD_SSAR_START_DATETIME)
    │  │  │  │  WITH (FILLFACTOR=70)
    │  │  │  └─ Create partitions: analytic_2024, analytic_2025, ...
    │  │  │
    │  │  ├─ CTE Pipeline → INSERT into shadow table:
    │  │  │  │
    │  │  │  ├─ Extract from MySQL raw tables:
    │  │  │  │  WITH cop_clean AS (
    │  │  │  │      SELECT observation_id, SSAR_CONFIG_ID, ...
    │  │  │  │      FROM raw.cop_observation_mysql m
    │  │  │  │      LEFT JOIN raw.scene_mysql s ON m.REFOBS_ID = s.observation_ref
    │  │  │  │      WHERE CMD_SSAR_START_DATETIME >= '2024-01-10 08:55:00'
    │  │  │  │  )
    │  │  │  │
    │  │  │  ├─ Extract from MariaDB raw tables:
    │  │  │  │  base AS (
    │  │  │  │      SELECT ... FROM raw.cop_observation_mariadb d
    │  │  │  │      LEFT JOIN raw.scene_mariadb ...
    │  │  │  │      WHERE ...
    │  │  │  │  )
    │  │  │  │
    │  │  │  ├─ UNION ALL (combine both DBs):
    │  │  │  │  unpivoted AS (
    │  │  │  │      SELECT ..., 'RIFG' as product_name FROM cop_clean
    │  │  │  │      UNION ALL
    │  │  │  │      SELECT ..., 'RIFF' as product_name FROM base
    │  │  │  │      UNION ALL
    │  │  │  │      ... (8 product types total)
    │  │  │  │  )
    │  │  │  │
    │  │  │  └─ INSERT into analytic_table_new:
    │  │  │     INSERT INTO analytic_table_new
    │  │  │     SELECT * FROM unpivoted
    │  │  │     └─ Returns: 123456 rows inserted
    │  │  │
    │  │  ├─ Create indexes on shadow table:
    │  │  │  CREATE INDEX idx_at_obs_id ON analytic_table_new (observation_id)
    │  │  │  CREATE INDEX idx_at_time_btree ON analytic_table_new (CMD_SSAR_START_DATETIME)
    │  │  │  CREATE INDEX idx_at_cfg_time ON analytic_table_new (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME)
    │  │  │  CREATE INDEX idx_at_covering ON analytic_table_new (...) INCLUDE (...)
    │  │  │  ... (11 indexes total)
    │  │  │
    │  │  ├─ Build RC Cache (pre-aggregated chart data):
    │  │  │  DELETE FROM rc_cache
    │  │  │  INSERT INTO rc_cache (period_type, period_label, rc_id, count)
    │  │  │  SELECT
    │  │  │      'monthly' as period_type,
    │  │  │      TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') as period_label,
    │  │  │      SSAR_CONFIG_ID as rc_id,
    │  │  │      COUNT(*) as count
    │  │  │  FROM analytic_table_new
    │  │  │  GROUP BY period_type, period_label, rc_id
    │  │  │  ... (similar for weekly, yearly)
    │  │  │
    │  │  ├─ Refresh Materialized Views:
    │  │  │  REFRESH MATERIALIZED VIEW CONCURRENTLY mv_summary_counts
    │  │  │  (Doesn't lock analytic_table during refresh)
    │  │  │
    │  │  ├─ BLUE-GREEN SWAP (atomic, zero downtime):
    │  │  │  BEGIN TRANSACTION;
    │  │  │    ALTER TABLE analytic_table RENAME TO analytic_old;
    │  │  │    ALTER TABLE analytic_table_new RENAME TO analytic_table;
    │  │  │    DROP TABLE analytic_old CASCADE;
    │  │  │  COMMIT;
    │  │  │  
    │  │  │  (All three RENAME/DROP happen atomically at COMMIT)
    │  │  │  (Dashboard continues reading analytic_table without interruption)
    │  │  │
    │  │  ├─ VACUUM & ANALYZE (outside transaction):
    │  │  │  VACUUM ANALYZE analytic_table;
    │  │  │  (Cleans up dead rows, updates table statistics for query planner)
    │  │  │
    │  │  └─ Record Phase 2 success in etl_runs:
    │  │     INSERT INTO etl_runs
    │  │     (status, phase, last_processed_time, rows_processed)
    │  │     VALUES ('SUCCESS', 'TRANSFORM', NOW(), 123456)
    │  │
    │  └─ If Phase 2 FAILS:
    │     ├─ Rollback transaction (analytic_table unchanged)
    │     ├─ Log error
    │     └─ Record FAILED status in etl_runs
    │
    └─ Thread exits
    
↓

Frontend: api.js → API.etlStatus() (polling every 5 seconds)
    │
    └─ GET /api/etl/status
       └─ Backend reads: SELECT * FROM etl_runs ORDER BY id DESC LIMIT 1
          ├─ If status='SUCCESS': show green ✓ "ETL completed at 10:45:30"
          ├─ If status='FAILED': show red ✗ "ETL failed: {error_message}"
          └─ If status='IN_PROGRESS': show loading spinner

↓

User sees ETL completion status in dashboard header
Dashboard data automatically refreshes with new analytic_table
```

---

## Flow Diagrams

### **Diagram 1: User Filter Search Flow**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER INTERACTION                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│    Input Filter Values:                                                     │
│    ┌──────────────────────────────────┐                                     │
│    │ Date From:  2024-01-01           │                                     │
│    │ Date To:    2024-12-31           │                                     │
│    │ RC ID:      RC001                │                                     │
│    │ L0 Status:  Completed            │                                     │
│    │ Session ID: 001                  │                                     │
│    │ [Apply Filters] button           │                                     │
│    └──────────────────────────────────┘                                     │
│                    ↓                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                     │ collectFilters() returns object
                     ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND PROCESSING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  filters.js:                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │ function collectFilters() {                                      │       │
│  │   return {                                                       │       │
│  │     cmd_start: "2024-01-01",                                    │       │
│  │     cmd_end: "2024-12-31",                                      │       │
│  │     Rc_id: "RC001",                                             │       │
│  │     L0_status: "Completed",                                     │       │
│  │     Session_id: "001"  // auto-prefixed to "ssid_001" by backend│       │
│  │   }                                                              │       │
│  │ }                                                                │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                    ↓                                                         │
│  api.js:                                                                    │
│  ┌──────────────────────────────────────────────────────────────────┐       │
│  │ API.search(filters, page=1)                                      │       │
│  │ fetch(BASE + "/search?" + new URLSearchParams(filters))          │       │
│  │ .then(r => r.json())                                             │       │
│  └──────────────────────────────────────────────────────────────────┘       │
│                    ↓                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
         │ HTTP GET /api/search?cmd_start=2024-01-01&cmd_end=...&Rc_id=...
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BACKEND PROCESSING                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  app.py: Flask receives GET request                                         │
│    ↓                                                                         │
│  observations.py: search()                                                  │
│  ┌────────────────────────────────────────────────────────────────┐         │
│  │ 1. Extract query params: page, limit, offset                  │         │
│  │                                                                │         │
│  │ 2. Call build_where_clause(filters) from queries.py           │         │
│  │    Result:                                                    │         │
│  │    where_sql = """WHERE 1=1                                  │         │
│  │        AND CMD_SSAR_START_DATETIME >= %s                     │         │
│  │        AND CMD_SSAR_END_DATETIME <= %s                       │         │
│  │        AND SSAR_CONFIG_ID = %s                               │         │
│  │        AND LOWER(L0_status) = %s                             │         │
│  │        AND SESS_ID LIKE %s"""                                │         │
│  │    params = [                                                │         │
│  │      "2024-01-01 00:00:00",                                  │         │
│  │      "2024-12-31 23:59:59",                                  │         │
│  │      "RC001",                                                │         │
│  │      "completed",                                            │         │
│  │      "ssid_001"                                              │         │
│  │    ]                                                          │         │
│  │                                                                │         │
│  │ 3. Execute COUNT query:                                       │         │
│  │    SELECT COUNT(*) as total                                  │         │
│  │    FROM public.analytic_table a                              │         │
│  │    WHERE 1=1 AND ... (all conditions)                        │         │
│  │    Result: total_rows = 1050                                 │         │
│  │            total_pages = 42                                  │         │
│  │                                                                │         │
│  │ 4. Execute DATA query:                                        │         │
│  │    SELECT observation_id, SSAR_CONFIG_ID, SESS_ID, ...       │         │
│  │    FROM public.analytic_table a                              │         │
│  │    WHERE 1=1 AND ... (all conditions)                        │         │
│  │    ORDER BY CMD_SSAR_START_DATETIME DESC                     │         │
│  │    LIMIT 25 OFFSET 0                                         │         │
│  │    Result: [row1, row2, ..., row25]                          │         │
│  │                                                                │         │
│  │ 5. Convert timestamps to ISO format                           │         │
│  │                                                                │         │
│  │ 6. Return JSON response                                       │         │
│  └────────────────────────────────────────────────────────────────┘         │
│                    ↓                                                         │
└─────────────────────────────────────────────────────────────────────────────┘
         │ JSON response
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      DATABASE QUERY EXECUTION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  PostgreSQL Query Optimizer:                                                │
│  1. Parse WHERE conditions                                                  │
│  2. PARTITION PRUNING:                                                      │
│     - Date range: 2024-01-01 to 2024-12-31                                 │
│     - Only scan: analytic_2024 partition                                    │
│     - Skip: analytic_2023, 2025, 2026, 2027, default                       │
│                                                                             │
│  3. INDEX SELECTION (Cost-based planner):                                   │
│     Option A: idx_at_cfg_time (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME)    │
│               (best for combined RC_ID + date range filter)                 │
│     Option B: idx_at_time_btree (CMD_SSAR_START_DATETIME)                  │
│               (good for date-only, but need to filter L0_status)           │
│     Option C: Bitmap Index Scan                                             │
│               (combine multiple indexes via bitmap merge)                    │
│     Planner chooses: Option A (idx_at_cfg_time)                            │
│                                                                             │
│  4. SCAN PLAN:                                                              │
│     Index Scan on analytic_2024 using idx_at_cfg_time                      │
│     ├─ Filter: SSAR_CONFIG_ID = 'RC001'                                    │
│     ├─ Filter: CMD_SSAR_START_DATETIME >= '2024-01-01'                     │
│     └─ Filter: CMD_SSAR_START_DATETIME <= '2024-12-31'                     │
│                                                                             │
│  5. POST-INDEX FILTERS:                                                     │
│     ├─ LOWER(L0_status) = 'completed'  (can't use index, apply here)       │
│     └─ SESS_ID LIKE 'ssid_001'         (can't use index, apply here)       │
│                                                                             │
│  6. SORT: ORDER BY CMD_SSAR_START_DATETIME DESC                             │
│                                                                             │
│  7. LIMIT: Return first 25 rows                                             │
│                                                                             │
│  Result: 25 rows matched all conditions                                     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
         │ Result set returned to backend
         ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND DISPLAY                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Response JSON received by api.js:                                          │
│  {                                                                          │
│    "observations": [                                                        │
│      {                                                                      │
│        "REFOBS_ID": "OBS_20240115_001",                                    │
│        "SSAR_CONFIG_ID": "RC001",                                          │
│        "SESS_ID": "ssid_20240115",                                         │
│        "CMD_SSAR_START_DATETIME": "2024-01-15T10:30:45",                   │
│        "L0_status": "Completed",                                           │
│        ...                                                                  │
│      },                                                                     │
│      ... (24 more rows)                                                     │
│    ],                                                                       │
│    "page": 1,                                                               │
│    "total_pages": 42,                                                       │
│    "total_rows": 1050                                                       │
│  }                                                                          │
│          ↓                                                                  │
│  data_table.js: renderObservationTable(data)                               │
│  ├─ Render HTML table with 25 rows                                         │
│  ├─ Show pagination info: "Showing 1-25 of 1,050 observations"             │
│  ├─ Render pagination buttons:                                             │
│  │  [First]  [< Previous]  [1] [2] [3] ... [42]  [Next >]  [Last]          │
│  ├─ Attach click handlers to pagination                                    │
│  └─ Render analytics summary updated                                       │
│                                                                             │
│  USER SEES:                                                                 │
│  ┌─────────────────────────────────────┐                                   │
│  │ Filtered Data Table (25 rows shown) │                                   │
│  ├────────────────────────────────────+┤                                   │
│  │ ID   │ RC  │ Session │ Status   │ ...                                   │
│  ├──────┼─────┼─────────┼──────────┤                                       │
│  │ OBS01│RC001│ssid_... │Completed │ ...                                   │
│  │ OBS02│RC001│ssid_... │Completed │ ...                                   │
│  │ ...  │ ... │  ...    │   ...    │                                       │
│  ├─────────────────────────────────────┤                                   │
│  │ Showing 1-25 of 1,050 observations  │                                   │
│  │ [First] [< Prev] [1][2][3]...[Next] │                                   │
│  └─────────────────────────────────────┘                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### **Diagram 2: ETL Pipeline Complete Flow**

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        ETL TRIGGER INITIATION                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Frontend: User clicks "Run ETL" button                                     │
│    ↓                                                                         │
│  etl_trigger.js: API.triggerEtl()                                           │
│    ↓                                                                         │
│  api.js: fetch("POST /api/etl/trigger", {method: "POST"})                   │
│    ↓                                                                         │
│  Backend (app.py): POST /api/etl/trigger                                    │
│    ├─ Proxy to: requests.post("http://pipeline_etl:5001/etl/trigger")       │
│    └─ Return immediately (don't wait)                                       │
│                                                                             │
│  Response to Frontend:                                                      │
│  {"status": "triggered", "message": "ETL pipeline started in background"}   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                       ETL SERVICE (Backend)                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  etl_service.py: POST /etl/trigger                                          │
│    ├─ Start background thread: threading.Thread(target=run_full_etl())      │
│    └─ Return HTTP 202 Accepted immediately                                  │
│                                                                             │
│  Background Thread: run_full_etl()                                          │
│    ↓                                                                         │
│    ═════════════════════════════════════════════════════════════════        │
│    PHASE 1: RAW LOAD (MySQL + MariaDB → PostgreSQL raw schema)              │
│    ═════════════════════════════════════════════════════════════════        │
│                                                                             │
│    ┌─────────────────────────────────┐                                      │
│    │  MySQL Connection (3308)        │                                      │
│    │  ├─ SHOW TABLES                 │                                      │
│    │  │  Result: [cop_observation, scene, nisar_product_info, ...]         │
│    │  │                              │                                      │
│    │  └─ For each table:             │                                      │
│    │     ├─ DESCRIBE table           │                                      │
│    │     │  Result: columns + types  │                                      │
│    │     │                           │                                      │
│    │     ├─ Map types:               │                                      │
│    │     │  varchar → TEXT           │                                      │
│    │     │  int → INTEGER            │                                      │
│    │     │  datetime → TIMESTAMP     │                                      │
│    │     │                           │                                      │
│    │     ├─ CREATE TABLE in postgres │                                      │
│    │     │  CREATE TABLE raw.cop_observation_mysql (  │                     │
│    │     │    col1 TEXT, col2 INTEGER, ...            │                     │
│    │     │  );                                        │                     │
│    │     │                           │                                      │
│    │     └─ Copy rows in batches:    │                                      │
│    │        Batch 1 (rows 1-500):   │                                      │
│    │        SELECT * FROM cop_observation LIMIT 500 OFFSET 0               │
│    │        INSERT INTO raw.cop_observation_mysql ...                      │
│    │        ↓                        │                                      │
│    │        Batch 2 (rows 501-1000):│                                      │
│    │        SELECT * FROM cop_observation LIMIT 500 OFFSET 500             │
│    │        INSERT INTO raw.cop_observation_mysql ...                      │
│    │        ↓                        │                                      │
│    │        ... (repeat until < 500) │                                      │
│    │                              │                                      │
│    │  Result: 123,456 rows copied  │                                      │
│    └─────────────────────────────────┘                                      │
│              ↓                                                               │
│    ┌─────────────────────────────────┐                                      │
│    │ MariaDB Connection (3307)       │                                      │
│    │ (Same process as MySQL)         │                                      │
│    │  Result: 234,567 rows copied    │                                      │
│    └─────────────────────────────────┘                                      │
│              ↓                                                               │
│    Record Phase 1 in etl_runs:                                              │
│    INSERT INTO public.etl_runs (status, phase, start_time, rows_processed) │
│    VALUES ('SUCCESS', 'RAW_LOAD', '2024-01-15 10:00:00', 358023);          │
│                                                                             │
│    ═════════════════════════════════════════════════════════════════        │
│    PHASE 2: TRANSFORM + OPTIMIZE                                            │
│    ═════════════════════════════════════════════════════════════════        │
│                                                                             │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 1: Get Watermark (for incremental load)        │                 │
│    │                                                      │                 │
│    │ SELECT last_processed_time FROM etl_runs            │                 │
│    │ WHERE status = 'SUCCESS'                            │                 │
│    │ ORDER BY id DESC LIMIT 1;                           │                 │
│    │                                                      │                 │
│    │ Result: 2024-01-10 09:00:00                         │                 │
│    │ Watermark = 2024-01-10 08:55:00 (subtract 5 min)    │                 │
│    │                                                      │                 │
│    │ Only load/update records modified after watermark:  │                 │
│    │ WHERE CMD_SSAR_START_DATETIME >= '2024-01-10 08:55' │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 2: Create Shadow Table (analytic_table_new)    │                 │
│    │                                                      │                 │
│    │ DROP TABLE IF EXISTS public.analytic_table_new      │                 │
│    │                                                      │                 │
│    │ CREATE TABLE public.analytic_table_new (            │                 │
│    │   observation_id TEXT,                              │                 │
│    │   SESS_ID TEXT,                                     │                 │
│    │   CMD_SSAR_START_DATETIME TIMESTAMP,                │                 │
│    │   ...                                               │                 │
│    │ )                                                   │                 │
│    │ PARTITION BY RANGE (CMD_SSAR_START_DATETIME)        │                 │
│    │ WITH (FILLFACTOR = 70);                             │                 │
│    │                                                      │                 │
│    │ CREATE TABLE analytic_2024 PARTITION OF ...         │                 │
│    │   FOR VALUES FROM ('2024-01-01') TO ('2025-01-01')  │                 │
│    │ ... (more partitions for 2025, 2026, etc)           │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 3: CTE Pipeline → INSERT (Transform data)      │                 │
│    │                                                      │                 │
│    │ WITH cop_clean AS (                                 │                 │
│    │   SELECT col1, col2, ...                            │                 │
│    │   FROM raw.cop_observation_mysql m                  │                 │
│    │   LEFT JOIN raw.scene_mysql s                       │                 │
│    │     ON m.REFOBS_ID = s.observation_ref              │                 │
│    │   WHERE CMD_SSAR_START_DATETIME >= '2024-01-10 ...' │                 │
│    │ ),                                                  │                 │
│    │ base AS (                                           │                 │
│    │   SELECT col1, col2, ...                            │                 │
│    │   FROM raw.cop_observation_mariadb d                │                 │
│    │   LEFT JOIN raw.scene_mariadb s                     │                 │
│    │   WHERE ...                                         │                 │
│    │ ),                                                  │                 │
│    │ unpivoted AS (                                      │                 │
│    │   SELECT ..., 'RIFG' as product_name FROM cop_clean │                 │
│    │   UNION ALL                                         │                 │
│    │   SELECT ..., 'RIFF' as product_name FROM base      │                 │
│    │   UNION ALL                                         │                 │
│    │   ... (8 product types: RIFG, RIFF, ...)            │                 │
│    │ )                                                   │                 │
│    │ INSERT INTO public.analytic_table_new               │                 │
│    │ SELECT * FROM unpivoted;                            │                 │
│    │                                                      │                 │
│    │ Result: 123,456 rows inserted into shadow table     │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 4: Create Indexes (11 total)                   │                 │
│    │                                                      │                 │
│    │ CREATE INDEX idx_at_obs_id ON analytic_table_new    │                 │
│    │   (observation_id);                                 │                 │
│    │                                                      │                 │
│    │ CREATE INDEX idx_at_time_btree ON analytic_table_new │                 │
│    │   (CMD_SSAR_START_DATETIME);                        │                 │
│    │                                                      │                 │
│    │ CREATE INDEX idx_at_cfg_time ON analytic_table_new  │                 │
│    │   (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME);        │                 │
│    │                                                      │                 │
│    │ ... (8 more indexes)                                │                 │
│    │                                                      │                 │
│    │ Status: All indexes built, shadow table ready       │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 5: Build RC Cache (pre-agg chart data)         │                 │
│    │                                                      │                 │
│    │ DELETE FROM public.rc_cache;                        │                 │
│    │                                                      │                 │
│    │ INSERT INTO public.rc_cache                         │                 │
│    │ (period_type, period_label, rc_id, count)           │                 │
│    │ SELECT                                              │                 │
│    │   'monthly' as period_type,                         │                 │
│    │   TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM'),      │                 │
│    │   SSAR_CONFIG_ID as rc_id,                          │                 │
│    │   COUNT(*) as count                                 │                 │
│    │ FROM public.analytic_table_new                      │                 │
│    │ GROUP BY period_type, period_label, rc_id;          │                 │
│    │                                                      │                 │
│    │ (Similar for weekly and yearly)                     │                 │
│    │                                                      │                 │
│    │ Status: rc_cache populated, charts now instant      │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 6: Refresh Materialized Views                  │                 │
│    │                                                      │                 │
│    │ REFRESH MATERIALIZED VIEW CONCURRENTLY              │                 │
│    │   public.mv_summary_counts;                         │                 │
│    │                                                      │                 │
│    │ (CONCURRENTLY = doesn't block reads during refresh)  │                 │
│    │                                                      │                 │
│    │ Status: mv_summary_counts updated                   │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 7: BLUE-GREEN SWAP (Atomic, Zero Downtime)     │                 │
│    │                                                      │                 │
│    │ BEGIN TRANSACTION;                                  │                 │
│    │   ALTER TABLE analytic_table                        │                 │
│    │     RENAME TO analytic_old;         (step 1)        │                 │
│    │                                                      │                 │
│    │   ALTER TABLE analytic_table_new                    │                 │
│    │     RENAME TO analytic_table;       (step 2)        │                 │
│    │                                                      │                 │
│    │   DROP TABLE analytic_old CASCADE;  (step 3)        │                 │
│    │ COMMIT;                                             │                 │
│    │                                                      │                 │
│    │ Timeline:                                           │                 │
│    │ T0 (before):  analytic_table (LIVE)                │                 │
│    │                analytic_table_new (shadow)          │                 │
│    │                                                      │                 │
│    │ T1 (renaming): analytic_table → analytic_old        │                 │
│    │                analytic_table_new → analytic_table  │                 │
│    │                (all in one atomic COMMIT)           │                 │
│    │                                                      │                 │
│    │ T2 (after):   analytic_table (LIVE, new data)       │                 │
│    │                analytic_old → dropped               │                 │
│    │                                                      │                 │
│    │ Status: Dashboard now reads new data, zero downtime │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    ┌──────────────────────────────────────────────────────┐                 │
│    │ Step 8: VACUUM & ANALYZE (outside transaction)      │                 │
│    │                                                      │                 │
│    │ VACUUM ANALYZE public.analytic_table;               │                 │
│    │                                                      │                 │
│    │ (Cleans dead rows, updates table statistics)        │                 │
│    │                                                      │                 │
│    │ Status: Table optimized for future queries          │                 │
│    └──────────────────────────────────────────────────────┘                 │
│                       ↓                                                      │
│    Record Phase 2 success in etl_runs:                                      │
│    INSERT INTO public.etl_runs                                              │
│    (status, phase, start_time, end_time, last_processed_time, rows_...)    │
│    VALUES ('SUCCESS', 'TRANSFORM', '2024-01-15 10:15:00', '2024-01-15 ...  │
│                                                                             │
│  Background Thread completes                                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    DASHBOARD STATUS UPDATE                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Frontend: api.js polls API.etlStatus() every 5 seconds                     │
│            GET /api/etl/status                                              │
│              ↓                                                              │
│  Backend: routes/etl.py → etl_status()                                      │
│            SELECT * FROM etl_runs ORDER BY id DESC LIMIT 1                  │
│              ↓                                                              │
│  Response:  {                                                               │
│              "status": "SUCCESS",                                           │
│              "phase": "TRANSFORM",                                          │
│              "time": "2024-01-15 15:45:30",  (IST)                         │
│              "rows_processed": 123456,                                      │
│              "error": null                                                  │
│            }                                                                │
│              ↓                                                              │
│  Frontend: etl_trigger.js updates header                                    │
│            Show green ✓ "ETL completed: 2024-01-15 15:45:30"               │
│            Auto-refresh all dashboard data                                  │
│              ↓                                                              │
│  USER SEES:                                                                 │
│  ┌────────────────────────────────────────┐                                │
│  │ ETL Status: ✓ SUCCESS (15:45:30)      │                                │
│  │ Rows: 123,456                         │                                │
│  │                                        │                                │
│  │ Dashboard data automatically updated: │                                │
│  │ - Observations table: 1,050 rows      │                                │
│  │ - Analytics: 42 RC configs            │                                │
│  │ - Charts: May 2024 data loaded        │                                │
│  │ - Map: 850 polygons rendered          │                                │
│  └────────────────────────────────────────┘                                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Database Concepts Explained

### **Partitioning (analytic_table)**

```
Full Table:  analytic_table (1.5 GB total)
├─ 2023 data: 150,000 rows (partition: analytic_2023)
├─ 2024 data: 300,000 rows (partition: analytic_2024) ← Current year
├─ 2025 data: 250,000 rows (partition: analytic_2025)
├─ 2026 data: 200,000 rows (partition: analytic_2026)
└─ 2027+ data: 100,000 rows (partition: analytic_default)

Query: SELECT * FROM analytic_table WHERE CMD_SSAR_START_DATETIME BETWEEN '2024-01-01' AND '2024-12-31'

PostgreSQL automatically excludes:
- analytic_2023 (dates before 2024)
- analytic_2025 (dates after 2024)
- analytic_2026, analytic_2027, default (dates outside range)

Result: Only scans analytic_2024 partition (~300,000 rows)
Speedup: ~5x faster than full table scan
```

### **Index Types & Use Cases**

| Index | Use Case | Example |
|---|---|---|
| **B-tree** | Exact match, range, sorting | `WHERE observation_id = 'OBS001'` or `WHERE date > '2024-01-01'` |
| **BRIN** | Large sorted columns (compact) | `WHERE CMD_SSAR_START_DATETIME BETWEEN ...` (minimal memory) |
| **Partial** | Subset of rows (sparse) | `WHERE WKT_POLYGON IS NOT NULL` (only ~20% of rows) |
| **Composite** | Multiple columns together | `WHERE SSAR_CONFIG_ID = 'RC001' AND CMD_SSAR_START_DATETIME ...` |
| **Covering** | Includes extra columns | Avoids heap lookup (index has all needed columns) |

### **Blue-Green Swap Benefits**

```
Before ETL:
- analytic_table (live)
  ├─ 100,000 rows
  ├─ Query response: 200ms

During ETL:
- analytic_table (live, unchanged)
  ├─ 100,000 rows
  ├─ Query response: 200ms (unaffected)
- analytic_table_new (building, invisible)

After ETL Completes (swap happens in < 1 second):
- analytic_table (live, new)
  ├─ 123,456 rows (new data)
  ├─ Query response: 150ms (better performance)
- analytic_old (dropped immediately)

Key Benefit: Dashboard never goes dark; queries run continuously
```

---

## Performance Optimization Strategies

### **1. Partition Pruning**

```sql
-- Query: "Show 2024 data only"
SELECT * FROM analytic_table 
WHERE CMD_SSAR_START_DATETIME BETWEEN '2024-01-01' AND '2024-12-31'

-- PostgreSQL automatically prunes:
-- ✓ Only scans: analytic_2024
-- ✗ Skips: analytic_2023, 2025, 2026, 2027, default
-- Result: ~70% reduction in data scanned
```

### **2. Index Selection**

```sql
-- Query with multiple filters
SELECT * FROM analytic_table
WHERE SSAR_CONFIG_ID = 'RC001'
  AND CMD_SSAR_START_DATETIME >= '2024-01-01'
  AND L0_status = 'Completed'

-- Index: idx_at_cfg_time (SSAR_CONFIG_ID, CMD_SSAR_START_DATETIME)
-- Usage: 
--   - Quick index scan on (RC001, date >= 2024-01-01)
--   - Then filter remaining rows where L0_status = 'Completed'
-- Result: 50-100x faster than full table scan
```

### **3. Materialized Views (Pre-aggregation)**

```sql
-- Without materialization: every request runs aggregation
SELECT COUNT(DISTINCT observation_id), COUNT(DISTINCT DATATAKE_ID), ...
FROM analytic_table  -- scans entire table each time

-- With materialization (pre-computed)
SELECT * FROM mv_summary_counts  -- instant lookup, no aggregation
```

### **4. RC Cache (Time-series Pre-aggregation)**

```sql
-- Without cache: every chart request aggregates
SELECT TO_CHAR(CMD_SSAR_START_DATETIME, 'YYYY-MM') as month, COUNT(*)
FROM analytic_table
GROUP BY month
-- Result: 2-5 seconds for chart load

-- With rc_cache: instant chart load
SELECT * FROM rc_cache WHERE period_type = 'monthly'
-- Result: < 100ms for chart load
```

---

## File Responsibilities Summary

### **Frontend Files**

| File | Responsibility |
|---|---|
| `index.html` | Single-page app entry, container divs |
| `styles.css` | Dashboard UI styling |
| `main.js` | App initialization, DOMContentLoaded, wires components |
| `api.js` | Centralized fetch() calls, all backend communication |
| `filters.js` | Filter UI toggles, collectFilters() function |
| `data_table.js` | Paginated observations table rendering |
| `map.js` | Leaflet map init, WKT polygon parsing, drawPolygons() |
| `chart.js` | Bar chart (Chart.js) rendering with rc_cache data |
| `analytics_table.js` | Summary counts widget from mv_summary_counts |
| `ai_chat.js` | Chat UI, message history, LLM integration |
| `pagination.js` | Page navigation logic |
| `csv_export.js` | Download analytics table as CSV |

### **Backend Files**

| File | Responsibility |
|---|---|
| `app.py` | Flask entry point, blueprint registration, CORS |
| `db/connection.py` | psycopg2 pool, get_db_connection() |
| `db/queries.py` | Centralized SQL strings, build_where_clause() |
| `routes/observations.py` | GET /api/search (paginated table) |
| `routes/analytics.py` | GET /api/analytics (summary counts) |
| `routes/charts.py` | GET /api/rc_stats (chart data) |
| `routes/map.py` | GET /api/map_polygons (WKT geometries) |
| `routes/ai.py` | POST /api/ai/query (text-to-SQL) |
| `routes/etl.py` | GET /api/etl/status, POST /api/etl/trigger |
| `services/ai_service.py` | answer_query(), LLM integration stub |
| `services/analytics_service.py` | get_analytics_counts() → mv query |
| `services/pagination_service.py` | get_page_params(), calc_total_pages() |

### **ETL Files**

| File | Responsibility |
|---|---|
| `etl_service.py` | Flask entry, /etl/trigger, /etl/status, threading |
| `core/db.py` | Connection factories for MySQL/MariaDB/PostgreSQL |
| `core/phase1_raw_load.py` | Dynamic table discovery, batch copy (500 rows) |
| `core/phase2_transform.py` | CTE pipeline, blue-green swap, index building |

### **Database Files**

| File | Responsibility |
|---|---|
| `postgres/init/01_schema.sql` | Auto-run on container start: raw schema, analytic_table, 11 indexes, 3 MVs |
| `schema.sql` | MySQL/MariaDB source table definitions |

---

## Deployment Checklist

- [ ] All 5 containers (mysql, mariadb, postgres, etl, backend, frontend) healthy
- [ ] MySQL dump loaded: `dumps/mysql/mysql_dump.sql`
- [ ] MariaDB dump loaded: `dumps/mariadb/mariadb_dump.sql`
- [ ] PostgreSQL `01_schema.sql` auto-executed
- [ ] ETL triggered: `POST /etl/trigger`
  - [ ] Phase 1 raw load complete (check `etl_runs` table)
  - [ ] Phase 2 transform complete
  - [ ] Blue-green swap successful
  - [ ] Dashboard data visible
- [ ] Filter search working: try date range + RC ID filter
- [ ] Map rendering: check WKT polygons load
- [ ] Charts displaying: monthly/weekly/yearly counts
- [ ] AI chat responding: test natural language query
- [ ] ETL status displayed in dashboard header

---

## Troubleshooting

### **ETL Phase 1 Fails**

```
Check: MySQL/MariaDB connections available?
  docker ps → verify mysql_db and mariadb_db containers running
  
Check: Dump files loaded?
  docker exec mysql_db mysql -uroot -proot -e "SHOW DATABASES;"
  docker exec mariadb_db mysql -uroot -proot -e "SHOW DATABASES;"

Check: PostgreSQL accessible?
  docker exec postgres_db psql -U admin -d analytics -c "SELECT 1;"
```

### **Dashboard Slow**

```
Check: Indexes created?
  SELECT * FROM pg_stat_indexes WHERE idx_at_time_brin;
  
Check: Partition pruning working?
  EXPLAIN SELECT * FROM analytic_table WHERE CMD_SSAR_START_DATETIME BETWEEN '2024-01-01' AND '2024-12-31';
  (Should say "Planning time: 0.XXX ms" — fast pruning)

Check: RC cache populated?
  SELECT COUNT(*) FROM rc_cache;  -- should be > 0
```

---

## Future Improvements

1. **Incremental ETL Only** — Load only changed records (watermark currently supports this)
2. **Parallel Index Building** — Create multiple indexes concurrently
3. **Archival Strategy** — Move old partitions to cold storage (2023 data)
4. **Real-time Streaming** — Kafka ingestion instead of batch ETL
5. **LLM Integration** — Wire up Ollama/OpenAI for AI chat
6. **Audit Logging** — Track who accessed what data and when
7. **Query Caching** — Redis layer for frequently-asked questions

---

**Last Updated:** 2024-01-15  
**Architecture Version:** 2.0  
**Status:** Production Ready
│                                       rc_cache + blue-green swap + mat views + VACUUM
│
└── scripts/
    ├── verify_etl.sh                ← checks row counts, partitions, indexes, mat views
    └── reset_dev.sh                 ← wipes all ETL output for clean dev run