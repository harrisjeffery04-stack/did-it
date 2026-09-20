#!/usr/bin/env bash
# ProvenDone local run: MCP server (Streamable HTTP) + voice-style web demo.
set -e
cd "$(dirname "$0")/.."

mkdir -p receipts demo/fixtures/photos demo/fixtures/vault

# demo fixtures (photos backup is idempotent; messy is recreated each start)
[ -f demo/fixtures/photos/IMG_0001.jpg ] || head -c 4096 /dev/urandom > demo/fixtures/photos/IMG_0001.jpg
[ -f demo/fixtures/photos/IMG_0002.jpg ] || head -c 8192 /dev/urandom > demo/fixtures/photos/IMG_0002.jpg
[ -f demo/fixtures/photos/IMG_0003.png ] || head -c 2048 /dev/urandom > demo/fixtures/photos/IMG_0003.png
rm -rf demo/fixtures/messy && mkdir -p demo/fixtures/messy
head -c 1024 /dev/urandom > demo/fixtures/messy/invoice_mar.pdf
head -c 2048 /dev/urandom > demo/fixtures/messy/cat_photo.jpg
head -c  512 /dev/urandom > demo/fixtures/messy/notes.txt

export PROVENDONE_PORT="${PROVENDONE_PORT:-8765}"
export BRIDGE_PORT="${BRIDGE_PORT:-8770}"

echo "[1/2] MCP server (Streamable HTTP)  -> http://127.0.0.1:${PROVENDONE_PORT}/mcp"
python3 -m server.app &
MCP_PID=$!

echo "[2/2] voice demo bridge + UI         -> http://127.0.0.1:${BRIDGE_PORT}"
python3 demo/bridge.py &
BRIDGE_PID=$!

trap 'kill $MCP_PID $BRIDGE_PID 2>/dev/null' EXIT
echo "Ctrl-C to stop."
wait