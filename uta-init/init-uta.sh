#!/usr/bin/env bash
set -euo pipefail

echo "Restoring UTA from local gzip…"

gzip -cd /docker-entrypoint-initdb.d/uta_20241220.pgd.gz \
  | psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"
