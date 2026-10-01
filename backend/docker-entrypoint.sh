#!/bin/sh
# Apply database migrations before starting, when RUN_MIGRATIONS=1.
# With several replicas, run migrations once (e.g. a release job) and leave this off.
set -e
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
  echo "Applying database migrations…"
  flask db upgrade
fi
exec "$@"
