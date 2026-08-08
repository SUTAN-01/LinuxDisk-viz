#!/bin/bash
# Package diskviz into a distributable tar.gz for Linux x86_64.
# Usage: ./scripts/package.sh [version]
set -euo pipefail

cd "$(dirname "$0")/.."

# Determine version: explicit arg > pyproject > fallback.
VERSION="${1:-}"
if [ -z "$VERSION" ]; then
    VERSION=$(grep -m1 '^version' webapp/pyproject.toml | sed 's/.*"\(.*\)".*/\1/')
fi
if [ -z "$VERSION" ]; then
    VERSION="0.0.0"
fi
echo "Packaging diskviz v${VERSION}"

# Build first.
./scripts/build.sh

STAGE="dist/diskviz-${VERSION}"
rm -rf "dist"
mkdir -p "$STAGE/bin" "$STAGE/lib"

cp scanner/build/disk-scanner "$STAGE/bin/"
cp -r webapp/diskviz_api "$STAGE/lib/"
cp webapp/pyproject.toml "$STAGE/lib/"
cp -r scripts "$STAGE/"
cp -r scanner/third_party "$STAGE/lib/" 2>/dev/null || true

ARCH=$(uname -m)
TARBALL="dist/diskviz-${VERSION}-linux-${ARCH}.tar.gz"
tar czf "$TARBALL" -C dist "diskviz-${VERSION}"

echo "Packaged: ${TARBALL}"
