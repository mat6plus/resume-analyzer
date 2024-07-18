


#!/bin/bash

set -euo pipefail

HOST="${DB_HOST:?DB_HOST environment variable is not set}"
DB_USERNAME="${DB_USERNAME:?DB_USERNAME environment variable is not set}"
DB_PASSWORD="${DB_PASSWORD:?DB_PASSWORD environment variable is not set}"
DB_NAME="${DB_NAME:?DB_NAME environment variable is not set}"
CMD="${@:?Please provide a command to execute}"

TRIES=0
MAX_TRIES=5
SLEEP_TIME=12

until export PGPASSWORD="${DB_PASSWORD}" && psql -h "${HOST}" -U "${DB_USERNAME}" -d "${DB_NAME}" -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep ${SLEEP_TIME}
  ((TRIES++))
  if [ ${TRIES} -ge ${MAX_TRIES} ]; then
    >&2 echo "Error: Postgres is not available after ${MAX_TRIES} tries. Check your database connection."
    exit 1
  fi
done

>&2 echo "Postgres is up - executing command"
exec "${CMD}"






version: '3.8'

services:
  db:
    image: postgres
    environment:
      - POSTGRES_DB=${DB_NAME}
      - POSTGRES_USER=${DB_USERNAME}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - db-data:/var/lib/postgresql/data

  app:
    build: .
    command: sh -c "./wait-for-db.sh db 5432 python manage.py migrate && gunicorn --bind 0.0.0.0:8000 resume_analyzer.wsgi:application"
    depends_on:
      - db
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=${DEBUG}
      - DATABASE_PROVIDER=${DATABASE_PROVIDER}
      - DB_NAME=${DB_NAME}
      - DB_USERNAME=${DB_USERNAME}
      - DB_PASSWORD=${DB_PASSWORD}
      - DB_HOST=db
      - DB_PORT=5432
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - EMAIL_PORT=${EMAIL_PORT}
    ports:
      - "8000:8000"

volumes:
  db-data: