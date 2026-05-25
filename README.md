frontend/
├── nginx.conf                        ← only needed for Docker/prod
└── src/
    ├── index.html                    ← clean HTML, zero inline JS
    ├── css/
    │   └── styles.css                ← paste your existing CSS here
    └── js/
        ├── api.js                    ← ALL fetch() calls live here only
        ├── main.js                   ← app entry, DOMContentLoaded, wires everything
        ├── components/
        │   ├── filters.js            ← toggle logic + collectFilters()
        │   ├── map.js                ← Leaflet init, drawPolygons(), WKT parsing
        │   ├── chart.js              ← loadRCChart()
        │   ├── analytics_table.js    ← renderAnalyticTable()
        │   ├── data_table.js         ← renderObservationTable()
        │   ├── ai_chat.js            ← initChat(), appendMessage()
        │   └── etl_trigger.js        ← ⚠ DEV ONLY — delete before prod
        └── utils/
            ├── pagination.js         ← renderPagination()
            └── csv_export.js         ← downloadAnalyticsCsv()



etl_package/
│
├── docker-compose.yml               ← 5 containers: mysql, mariadb, postgres, etl, frontend
├── .gitignore                       ← excludes dumps/*.sql, *.tar, __pycache__
│
├── dumps/
│   ├── mysql/
│   │   └── mysql_dump.sql           ← PUT YOUR MYSQL DUMP HERE
│   └── mariadb/
│       └── mariadb_dump.sql         ← PUT YOUR MARIADB DUMP HERE
│
├── postgres/
│   └── init/
│       └── 01_schema.sql            ← auto-runs on first postgres start
│                                       creates raw schema, analytic_table (partitioned),
│                                       11 indexes, 3 materialized views
│
├── etl/
│   ├── Dockerfile                   ← python:3.10-slim, gunicorn 1 worker, 300s timeout
│   ├── requirements.txt             ← Flask, gunicorn, psycopg2-binary, PyMySQL
│   ├── etl_service.py               ← Flask app: /etl/trigger /etl/status /health
│   │
│   └── core/
│       ├── __init__.py
│       ├── db.py                    ← get_pg_conn() get_mysql_conn() get_mariadb_conn()
│       ├── phase1_raw_load.py       ← dynamic table discovery, batch copy, type mapping
│       └── phase2_transform.py      ← CTE + UNION ALL + partitions + indexes +
│                                       rc_cache + blue-green swap + mat views + VACUUM
│
└── scripts/
    ├── verify_etl.sh                ← checks row counts, partitions, indexes, mat views
    └── reset_dev.sh                 ← wipes all ETL output for clean dev run