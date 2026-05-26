"""
routes/observations.py — GET /api/search
Paginated observation table — feeds the Information Table on dashboard.
"""
from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from db.queries import OBSERVATIONS_SELECT, OBSERVATIONS_ORDER, COUNT_QUERY, build_where_clause
from services.pagination_service import get_page_params, calc_total_pages

observations_bp = Blueprint("observations", __name__)


@observations_bp.route("/search")
def search():
    filters          = request.args.to_dict()
    page, limit, offset = get_page_params(filters)
    where, params    = build_where_clause(filters)

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        # total row count for pagination
        cursor.execute(COUNT_QUERY + where, params)
        total_rows  = cursor.fetchone()["total"]
        total_pages = calc_total_pages(total_rows, limit)

        # paginated data
        cursor.execute(
            OBSERVATIONS_SELECT + where + OBSERVATIONS_ORDER,
            params + [limit, offset]
        )
        rows = cursor.fetchall()

        # convert datetime objects to strings for JSON serialisation
        observations = []
        for row in rows:
            r = dict(row)
            for key, val in r.items():
                if hasattr(val, "isoformat"):
                    r[key] = val.isoformat()
            observations.append(r)

        return jsonify({
            "observations": observations,
            "page":         page,
            "total_pages":  total_pages,
            "total_rows":   total_rows,
        })

    finally:
        cursor.close()
        conn.close()