FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN  pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

# 1 worker — stateless API, but keeping simple for dev
# increase workers to 4 when moving to production
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60", \
     "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", \
     "app:app"]