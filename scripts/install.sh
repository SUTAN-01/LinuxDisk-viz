#!/bin/bash
# Install diskviz from a packaged tar.gz onto the target Linux machine.
# Usage: ./install.sh [tarball] [install_dir]
set -euo pipefail

TARBALL="${1:-dist/diskviz-*-linux-*.tar.gz}"
INSTALL_DIR="${2:-/opt/diskviz}"

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: run as root (sudo)." >&2
    exit 1
fi

# Resolve glob to a single file.
TARBALL=$(ls $TARBALL 2>/dev/null | head -n1 || true)
if [ -z "$TARBALL" ] || [ ! -f "$TARBALL" ]; then
    echo "ERROR: no tarball found. Run ./scripts/package.sh first." >&2
    exit 1
fi

echo "Installing from ${TARBALL} to ${INSTALL_DIR}"
mkdir -p "$INSTALL_DIR/bin" "$INSTALL_DIR/lib"

TMP=$(mktemp -d)
tar xzf "$TARBALL" -C "$TMP"
SRC="$TMP"/diskviz-*

cp "$SRC"/bin/disk-scanner "$INSTALL_DIR/bin/"
cp -r "$SRC"/lib/* "$INSTALL_DIR/lib/"

# Install the Python webapp in editable mode so diskviz-serve is on PATH.
cd "$INSTALL_DIR/lib"
pip install -e .

# systemd unit.
cp "$SRC"/scripts/diskviz.service /etc/systemd/system/

# Generate tokens + config if not already present.
mkdir -p /etc/diskviz
if [ ! -f /etc/diskviz/env ]; then
    READ_TOKEN=$(openssl rand -hex 32)
    WRITE_TOKEN=$(openssl rand -hex 32)
    cat > /etc/diskviz/env <<EOF
DISKVIZ_READ_TOKEN=${READ_TOKEN}
DISKVIZ_WRITE_TOKEN=${WRITE_TOKEN}
DISKVIZ_SCANNER_BINARY=${INSTALL_DIR}/bin/disk-scanner
DISKVIZ_SCANS_DIR=${INSTALL_DIR}/var/scans
DISKVIZ_BIND_HOST=127.0.0.1
DISKVIZ_BIND_PORT=8765
EOF
    chmod 600 /etc/diskviz/env
    echo "Generated new tokens in /etc/diskviz/env"
else
    echo "Keeping existing /etc/diskviz/env"
fi

mkdir -p "$INSTALL_DIR/var/scans"

systemctl daemon-reload
systemctl enable --now diskviz

rm -rf "$TMP"

echo ""
echo "=== Installation complete ==="
echo "Service:  systemctl status diskviz"
echo "Tokens:   /etc/diskviz/env  (chmod 600)"
echo "Access:   ssh -L 8765:127.0.0.1:8765 user@server"
echo "           then open http://localhost:8765"
