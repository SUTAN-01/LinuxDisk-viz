#!/bin/bash
# End-to-end smoke test: builds everything, runs all unit tests, then starts
# the server and curls /health + /scan to confirm the stack is wired up.
# Intended to run on the target Linux machine.
set -euo pipefail

cd "$(dirname "$0")/.."

export DISKVIZ_READ_TOKEN="${DISKVIZ_READ_TOKEN:-test-read}"
export DISKVIZ_WRITE_TOKEN="${DISKVIZ_WRITE_TOKEN:-test-write}"

echo "=== C++ unit tests ==="
cd scanner/build
ctest --output-on-failure
cd ../..

echo "=== Python unit + integration tests ==="
cd webapp
python -m pytest tests/unit tests/integration -q
cd ..

echo "=== Frontend unit tests ==="
cd frontend
npm test -- --run
cd ..

echo "=== Full build ==="
./scripts/build.sh

echo "=== Start server + curl smoke ==="
cd webapp
DISKVIZ_READ_TOKEN="$DISKVIZ_READ_TOKEN" \
DISKVIZ_WRITE_TOKEN="$DISKVIZ_WRITE_TOKEN" \
python -m uvicorn diskviz_api.main:app --host 127.0.0.1 --port 8765 &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null || true' EXIT

# Wait for server to come up.
for _ in $(seq 1 20); do
    if curl -sf -H "Authorization: Bearer $DISKVIZ_READ_TOKEN" http://127.0.0.1:8765/health >/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done

echo "GET /health:"
curl -sf -H "Authorization: Bearer $DISKVIZ_READ_TOKEN" http://127.0.0.1:8765/health
echo

echo "POST /scan (mock root /tmp):"
curl -sf -H "Authorization: Bearer $DISKVIZ_READ_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST -d '{"root":"/tmp"}' \
     http://127.0.0.1:8765/scan
echo

echo "=== ALL SMOKE TESTS PASSED ==="
