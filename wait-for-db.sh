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