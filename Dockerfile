# Production Dockerfile for DocuSense AI Django REST API Backend
# Uses official lightweight Python runtime
FROM python:3.12-slim

# Prevent Python from writing .pyc and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . /app/

# Create persistent storage directories & static target
RUN mkdir -p /data/media /app/staticfiles

# Collect static files into staticfiles
RUN python manage.py collectstatic --noinput

# Set environment defaults for production volume mount
ENV SQLITE_DB_PATH=/data/db.sqlite3
ENV MEDIA_DIR=/data/media

# Default port
EXPOSE 8000

# Production start command using Gunicorn with SQLite-safe concurrency
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--timeout", "120", "core.wsgi:application"]
