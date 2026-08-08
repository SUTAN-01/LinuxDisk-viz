#!/bin/bash
# Build diskviz: C++ scanner + frontend, then stage static assets into webapp.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "=== Building C++ scanner (Release) ==="
cd scanner
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j"$(nproc 2>/dev/null || echo 4)"
cd ..

echo "=== Building frontend ==="
cd frontend
npm ci
npm run build
cd ..

echo "=== Staging static assets into webapp ==="
mkdir -p webapp/diskviz_api/static
cp -r frontend/dist/* webapp/diskviz_api/static/

echo "Build complete."
echo "  scanner: scanner/build/disk-scanner"
echo "  webapp:  webapp/diskviz_api/ (static assets staged)"
