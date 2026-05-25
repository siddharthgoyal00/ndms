FROM python:3.10-slim

WORKDIR /app

# System libs needed by psycopg2 and pymysql
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# --network=host lets pip reach PyPI through the host network
# Remove flag if your network allows direct container internet access
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5001

# 1 worker only — ETL does DDL (DROP/RENAME tables)
# Parallel workers would race on blue-green swap and corrupt live table
# 300s timeout — Phase 1 raw load of large dumps can take several minutes
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5001", \
     "--workers", "1", \
     "--timeout", "300", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "etl_service:app"]