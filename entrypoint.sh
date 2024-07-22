#!/bin/sh

set -e

# Wait for the database
echo "Waiting for database..."
while ! PGPASSWORD=$DB_PASSWORD psql -h "db" -U "$DB_USERNAME" -d "$DB_NAME" -c '\q'; do
  echo "Database is unavailable - sleeping"
  sleep 1
done

echo "Database is up - executing command"

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate

# Start Gunicorn
echo "Starting Gunicorn..."
gunicorn --bind 127.0.0.1:8000 resume_analyzer.wsgi:application