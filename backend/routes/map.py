"""
routes/map.py — GET /api/map_polygons
Returns WKT polygon geometries for Leaflet map rendering.
One polygon per unique observation_id (DISTINCT ON prevents duplicates).
"""
from flask import Blueprint, request, jsonify
from db.connection import get_db_connection
from db.queries import MAP_POLYGONS_SELECT, MAP_POLYGONS_ORDER, build_where_clause

map_bp = Blueprint("map", __name__)


@map_bp.route("/map_polygons")
def map_polygons():
    filters      = request.args.to_dict()
    where, params = build_where_clause(filters)

    # map_polygons already has WHERE WKT_POLYGON IS NOT NULL
    # merge with filter WHERE clause
    if where != "WHERE 1=1":
        # strip leading WHERE from filter clause and append as AND
        extra = where.replace("WHERE 1=1", "").strip()
        if extra:
            combined = MAP_POLYGONS_SELECT + extra + MAP_POLYGONS_ORDER
        else:
            combined = MAP_POLYGONS_SELECT + MAP_POLYGONS_ORDER
    else:
        combined = MAP_POLYGONS_SELECT + MAP_POLYGONS_ORDER

    conn   = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(combined, params)
        rows = cursor.fetchall()
        return jsonify({"polygons": [dict(r) for r in rows]})
    finally:
        cursor.close()
        conn.close()