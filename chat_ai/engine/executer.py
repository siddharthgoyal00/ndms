"""
engine/executor.py

Executes a validated SELECT query against postgres and returns rows as
a list of JSON-serialisable dicts.

Handles:
  - datetime / date serialisation (converted to ISO strings)
  - Decimal serialisation (converted to float)
  - Hard row cap (500) as a final safety net
"""
import os
import logging
import decimal
from datetime import datetime, date

import psycopg2
import psycopg2.extras

logger = logging.getLogger(__name__)

_MAX_ROWS = int(os.environ.get("QUERY_MAX_ROWS", 500))


def _get_conn():
    return psycopg2.connect(
        host     = os.environ["PG_HOST"],
        dbname   = os.environ["PG_DB"],
        user     = os.environ["PG_USER"],
        password = os.environ["PG_PASSWORD"],
        port     = int(os.environ.get("PG_PORT", 5432)),
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def _serialise(value):
    """Convert postgres types that aren't JSON-native."""
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, decimal.Decimal):
        return float(value)
    return value


def run_query(sql: str) -> list[dict]:
    """
    Execute sql (already validated) and return up to _MAX_ROWS rows.

    Raises:
        psycopg2.Error  propagated to caller for error reporting.
    """
    conn   = _get_conn()
    cursor = conn.cursor()

    try:
        logger.info(f"executor: running SQL: {sql[:200]}")
        cursor.execute(sql)
        rows = cursor.fetchmany(_MAX_ROWS)
        result = [
            {k: _serialise(v) for k, v in row.items()}
            for row in rows
        ]
        logger.info(f"executor: fetched {len(result)} rows")
        return result

    except psycopg2.Error as e:
        logger.error(f"executor: postgres error: {e}")
        raise

    finally:
        cursor.close()
        conn.close()