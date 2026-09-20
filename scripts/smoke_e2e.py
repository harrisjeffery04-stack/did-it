"""End-to-end smoke: boot the MCP server, drive it over real Streamable HTTP.

Proves the Alexa+-facing contract in one run:
  - server speaks Streamable HTTP and negotiates an MCP protocol version
  - run_task executes steps and returns done-and-proven receipts
  - receipts persist and re-read via get_receipt / list_receipts

Usage:  python scripts/smoke_e2e.py
"""
import asyncio
import json
import os
import socket
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO)

from mcp import ClientSession                      # noqa: E402
from mcp.client.streamable_http import streamablehttp_client  # noqa: E402

PORT = int(os.environ.get("DID_IT_PORT", "8765"))
URL = f"http://127.0.0.1:{PORT}/mcp"


def wait_port(timeout=25.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            socket.create_connection(("127.0.0.1", PORT), 1).close()
            return True
        except OSError:
            time.sleep(0.3)
    return False


def _j(res):
    data = getattr(res, "structuredContent", None)
    if isinstance(data, dict):
        return data
    return json.loads(res.content[0].text) if res.content else {}


async def main():
    proc = subprocess.Popen([sys.executable, "-m", "server.app"], cwd=REPO)
    ok = False
    try:
        assert wait_port(), "server did not open port {PORT}".format(PORT=PORT)
        async with streamablehttp_client(URL) as (read, write, _):
            async with ClientSession(read, write) as s:
                init = await s.initialize()
                print(f"PROTOCOL_VERSION_NEGOTIATED: {init.protocolVersion}")

                r1 = _j(await s.call_tool("run_task", {
                    "task": "smoke: back up the test suite",
                    "steps": [{"action": "file_backup",
                               "args": {"source_dir": "tests",
                                        "dest_dir": "/tmp/did-it_smoke_vault"}}]}))
                print(f"RUN_TASK verdict={r1['verdict']} steps={len(r1['steps'])} "
                      f"duration_ms={r1['duration_ms']}")
                print(f"  evidence sample: {json.dumps(r1['steps'][0]['evidence'][0])}")

                r2 = _j(await s.call_tool("get_receipt",
                                          {"receipt_id": r1["receipt_id"]}))
                print(f"GET_RECEIPT ok={r2.get('receipt_id') == r1['receipt_id']}")

                r3 = _j(await s.call_tool("list_receipts", {"limit": 5}))
                print(f"LIST_RECEIPTS count={r3['count']}")

                r4 = _j(await s.call_tool("run_task", {"task": "unparseable gibberish"}))
                print(f"NO_PLAN path verdict={r4['verdict']} (honest-failure check)")

                ok = (r1["verdict"] == "done-and-proven"
                      and r2.get("receipt_id") == r1["receipt_id"]
                      and r4["verdict"] == "failed")
    finally:
        proc.terminate()
        proc.wait(timeout=10)
    print("SMOKE_RESULT:", "PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())