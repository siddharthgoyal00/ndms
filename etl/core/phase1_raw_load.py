"""
core/phase1_raw_load.py — ETL Phase 1: Raw Load

Discovers ALL tables in MySQL and MariaDB dynamically,
then copies them into the PostgreSQL raw schema.

Why dynamic discovery instead of hardcoded table names:
  You have 25+ tables across two source DBs. Hardcoding them means
  updating this file every time a table is added or renamed.
  Dynamic reflection reads SHOW TABLES from each source and creates
  matching tables in postgres automatically.

Naming convention in postgres raw schema:
  MySQL table   "cop_observation" → raw.cop_observation_mysql
  MariaDB table "scene"          → raw.scene_mariadb

The _mysql / _mariadb suffix prevents name collisions if both
source DBs happen to have a table with the same name.

Flow per source DB:
  1. SHOW TABLES → get list of all table names
  2. DESCRIBE {table} → get column names and types
  3. Map MySQL types → PostgreSQL types
  4. DROP + CREATE raw.{table}_{suffix} in postgres
  5. SELECT * FROM source in 500-row batches → INSERT into postgres
"""
import logging
import pymysql
from .db import get_pg_conn, get_mysql_conn, get_mariadb_conn

logger = logging.getLogger(__name__)

BATCH_SIZE = 500   # rows per INSERT batch — balance memory vs round trips


# ── MySQL → PostgreSQL type mapping ──────────────────────────────────────────

MYSQL_TO_PG = {
    "int":        "INTEGER",
    "tinyint":    "SMALLINT",
    "smallint":   "SMALLINT",
    "mediumint":  "INTEGER",
    "bigint":     "BIGINT",
    "float":      "REAL",
    "double":     "DOUBLE PRECISION",
    "decimal":    "NUMERIC",
    "varchar":    "TEXT",
    "char":       "TEXT",
    "text":       "TEXT",
    "mediumtext": "TEXT",
    "longtext":   "TEXT",
    "tinytext":   "TEXT",
    "blob":       "BYTEA",
    "mediumblob": "BYTEA",
    "longblob":   "BYTEA",
    "datetime":   "TIMESTAMP",
    "timestamp":  "TIMESTAMP",
    "date":       "DATE",
    "time":       "TIME",
    "year":       "INTEGER",
    "json":       "JSONB",
    "enum":       "TEXT",
    "set":        "TEXT",
    "bit":        "BOOLEAN",
}


def mysql_type_to_pg(mysql_type: str) -> str:
    """Extract base type from MySQL type string and map to PostgreSQL."""
    base = mysql_type.lower().split("(")[0].strip()
    return MYSQL_TO_PG.get(base, "TEXT")   # TEXT for any unknown type


def get_table_names(src_conn) -> list:
    """Get all table names from a MySQL/MariaDB connection."""
    with src_conn.cursor() as cur:
        cur.execute("SHOW TABLES")
        return [list(row.values())[0] for row in cur.fetchall()]


def get_columns(src_conn, table: str) -> list:
    """
    Returns list of (column_name, pg_type) for a source table.
    Uses DESCRIBE which works on both MySQL and MariaDB.
    """
    with src_conn.cursor() as cur:
        cur.execute(f"DESCRIBE `{table}`")
        return [(row["Field"], mysql_type_to_pg(row["Type"])) for row in cur.fetchall()]


def recreate_raw_table(pg_conn, pg_table: str, columns: list):
    """
    Drops and recreates the raw staging table in postgres.
    Always does a full drop+create — raw tables are not blue-green swapped
    because the dashboard never reads from raw schema directly.
    """
    col_defs = ", ".join(f'"{col}" {dtype}' for col, dtype in columns)
    with pg_conn.cursor() as cur:
        cur.execute(f'DROP TABLE IF EXISTS raw."{pg_table}" CASCADE')
        cur.execute(f'CREATE TABLE raw."{pg_table}" ({col_defs})')
    pg_conn.commit()


def sanitize_value(val):
    """
    Converts MySQL-specific values that PostgreSQL rejects.
    MySQL allows 0000-00-00 00:00:00 as a zero date — PostgreSQL does not.
    Also handles Python datetime objects with zero dates from pymysql.
    """
    if val is None:
        return None
    if isinstance(val, str):
        if val.startswith("0000-00-00"):
            return None
    # pymysql sometimes returns datetime.datetime(1, 1, 1, ...) for zero dates
    import datetime
    if isinstance(val, datetime.datetime):
        if val.year < 1:
            return None
    if isinstance(val, datetime.date):
        if val.year < 1:
            return None
    return val


def copy_table_data(src_conn, pg_conn, src_table: str, pg_table: str, columns: list) -> int:
    """
    Copies all rows from source table to postgres raw schema in batches.
    Returns total rows copied.

    Batch strategy:
      fetchmany(BATCH_SIZE) avoids loading entire table into memory.
      executemany() sends one INSERT with 500 rows — much faster than
      500 individual INSERT statements.
    """
    col_names    = [col for col, _ in columns]
    pg_cols      = ", ".join(f'"{c}"' for c in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))
    insert_sql   = f'INSERT INTO raw."{pg_table}" ({pg_cols}) VALUES ({placeholders})'

    total = 0
    with src_conn.cursor() as src_cur:
        src_cur.execute(f"SELECT * FROM `{src_table}`")
        with pg_conn.cursor() as pg_cur:
            while True:
                rows = src_cur.fetchmany(BATCH_SIZE)
                if not rows:
                    break
                # DictCursor rows → extract values in column definition order
                batch = [tuple(sanitize_value(row[c]) for c in col_names) for row in rows]
                pg_cur.executemany(insert_sql, batch)
                total += len(batch)
        pg_conn.commit()

    return total


def load_one_source(label: str, src_conn, pg_conn, suffix: str) -> int:
    """
    Copies all tables from one source DB into postgres raw schema.
    Returns total rows loaded.
    Raises on any table copy failure — ETL should fail loudly here.
    """
    tables = get_table_names(src_conn)
    logger.info(f"[Phase 1] {label}: {len(tables)} tables found → {tables}")

    total_rows = 0
    for table in tables:
        pg_table = f"{table}{suffix}"
        try:
            columns = get_columns(src_conn, table)
            recreate_raw_table(pg_conn, pg_table, columns)
            rows = copy_table_data(src_conn, pg_conn, table, pg_table, columns)
            total_rows += rows
            logger.info(f"  ✓ {label}.{table} → raw.{pg_table} ({rows:,} rows)")
        except Exception as e:
            logger.error(f"  ✗ Failed: {label}.{table} → {e}")
            raise

    return total_rows


# ── Entry point ───────────────────────────────────────────────────────────────

def run_phase1() -> dict:
    """
    Phase 1 entry point — called by etl_service.py run_full_etl().
    Returns dict with row counts for audit logging.
    """
    logger.info("=" * 60)
    logger.info("ETL PHASE 1 — RAW LOAD STARTED")
    logger.info("=" * 60)

    pg_conn      = get_pg_conn()
    mysql_conn   = get_mysql_conn()
    mariadb_conn = get_mariadb_conn()

    try:
        # Ensure raw schema exists (idempotent)
        with pg_conn.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw")
        pg_conn.commit()

        mysql_rows   = load_one_source("MySQL",   mysql_conn,   pg_conn, "_mysql")
        mariadb_rows = load_one_source("MariaDB", mariadb_conn, pg_conn, "_mariadb")

        total = mysql_rows + mariadb_rows
        logger.info(f"Phase 1 complete — {total:,} total rows in raw schema")

        return {
            "mysql_rows":   mysql_rows,
            "mariadb_rows": mariadb_rows,
            "total":        total,
        }

    finally:
        mysql_conn.close()
        mariadb_conn.close()
        pg_conn.close()