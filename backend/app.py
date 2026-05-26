"""
app.py — Flask backend entry point

Registers all route blueprints and applies CORS.
All routes are prefixed with /api to separate from ETL service routes.

Port: 5000 (ETL runs on 5001)
"""
import logging
from flask import Flask, jsonify
from flask_cors import CORS

from routes.observations import observations_bp
from routes.analytics    import analytics_bp
from routes.charts       import charts_bp
from routes.map          import map_bp
from routes.etl          import etl_bp
from routes.ai           import ai_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

app = Flask(__name__)

# allow frontend (localhost:8080) to call backend (localhost:5000)
CORS(app)

# ── Register blueprints ───────────────────────────────────────────────────────
# No /api prefix — matches existing frontend api.js URL patterns exactly
app.register_blueprint(observations_bp)   # /search
app.register_blueprint(analytics_bp)     # /analytics
app.register_blueprint(charts_bp)        # /rc_stats
app.register_blueprint(map_bp)           # /map_polygons
app.register_blueprint(etl_bp)           # /etl/trigger  /etl/status
app.register_blueprint(ai_bp)            # /ai/query


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/metrics")
def metrics():
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)