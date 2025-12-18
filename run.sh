#!/usr/bin/env bash
set -euo pipefail

PORT=${PORT:-5000}
# Bind to 0.0.0.0 so Render can route to the service
exec gunicorn "app:app" -b "0.0.0.0:${PORT}" --workers 2 --log-level info
