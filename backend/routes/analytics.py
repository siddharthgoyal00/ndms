"""
routes/analytics.py — GET /api/analytics
Summary counts for the Analytic Table widget on dashboard.
"""
from flask import Blueprint, request, jsonify
from services.analytics_service import get_analytics_counts

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
def analytics():
    filters = request.args.to_dict()
    result  = get_analytics_counts(filters)
    return jsonify(result)