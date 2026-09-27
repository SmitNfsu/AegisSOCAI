#!/bin/bash
# One-command demo bring-up for AegisSOC AI (problem E1).
#   ./demo_up.sh
# Ensures DEV_MODE, refreshes the Risk Queue cache (safely), and starts the
# stack (Postgres + API + web, agent layer skipped). First run provisions a
# Python venv and installs deps via ./start.sh — give it a few minutes.
set -u
cd "$(dirname "$0")"

echo "▸ freeing port 5432 if another local Postgres holds it…"
docker rm -f deeptempo-postgres >/dev/null 2>&1 || true

echo "▸ ensuring .env with DEV_MODE=true…"
[ -f .env ] || cp env.example .env
grep -q '^DEV_MODE=' .env && sed -i 's/^DEV_MODE=.*/DEV_MODE=true/' .env || echo 'DEV_MODE=true' >> .env

echo "▸ refreshing Risk Queue data cache (skipped safely if deps/venv not ready)…"
# Prefer the project venv; never truncate the shipped cache on failure (write to
# a temp file and only swap it in on success).
PY="python3"; [ -x venv/bin/python3 ] && PY="venv/bin/python3"
if "$PY" -m core.risk.dashboard > build/dashboard_data.json.tmp 2>/dev/null; then
    mv build/dashboard_data.json.tmp build/dashboard_data.json
    echo "  cache refreshed."
else
    rm -f build/dashboard_data.json.tmp
    echo "  (refresh skipped — shipped cache in build/dashboard_data.json is used.)"
fi

echo "▸ starting the stack (Postgres + API + web)…"
echo "  → console will be at  http://localhost:7788  (Risk Queue in the nav)"
echo ""
SKIP_AGENT=1 ./start.sh
