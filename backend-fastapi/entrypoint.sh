#!/bin/sh
set -e

# Wait for PostgreSQL to accept connections before migrating
echo "Waiting for database..."
until python -c "
import os, sys
try:
    import psycopg2
    psycopg2.connect(os.environ['DATABASE_URL']).close()
except Exception as e:
    sys.exit(1)
" 2>/dev/null; do
    echo "  database not ready, retrying in 3s..."
    sleep 3
done
echo "Database ready."

echo "Running migrations..."
alembic upgrade head

echo "Starting server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
