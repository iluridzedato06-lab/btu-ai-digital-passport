#!/bin/sh
set -e

wait_for_db() {
  python - <<'PY'
import os, time, sys
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()
from django.db import connection
for i in range(60):
    try:
        connection.ensure_connection()
        sys.exit(0)
    except Exception as exc:
        print("waiting for database...", exc)
        time.sleep(2)
sys.exit(1)
PY
}

case "$1" in
  web)
    wait_for_db
    python manage.py migrate --noinput
    python manage.py createcachetable
    python manage.py build_sheet_template >/dev/null 2>&1 || true
    if [ "${SEED_DEMO_ON_START:-false}" = "true" ]; then python manage.py seed_demo; fi
    exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers "${GUNICORN_WORKERS:-3}" \
      --timeout 120 --access-logfile - --forwarded-allow-ips="*"
    ;;
  worker)
    wait_for_db
    # the web container runs migrations; wait until they are applied
    for i in $(seq 1 60); do python manage.py migrate --check >/dev/null 2>&1 && break; echo "waiting for migrations..."; sleep 2; done
    exec python manage.py run_worker
    ;;
  *)
    exec "$@"
    ;;
esac
