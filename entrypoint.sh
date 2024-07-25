#!/bin/sh

set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
gunicorn -c gunicorn.conf.py resume_analyzer.wsgi:application



# set -e

# # Wait for the database to be ready
# echo "Waiting for database..."
# /app/wait-for-db.sh db "$@"

# # Apply database migrations
# echo "Applying database migrations..."
# python manage.py migrate

# # Collect static files
# echo "Collecting static files..."
# python manage.py collectstatic --noinput

# # Exit successfully
# echo "Setup complete. Gunicorn will now start..."
# exec "$@"