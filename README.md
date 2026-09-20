# ProvenDone — done AND proven done

**Alexa+ track entry · Build, Ship, Shape: Amazon Developer Hackathon 2026**

Ask an assistant to do something and it says "OK, done." But did it?
ProvenDone is a self-hosted **MCP server for Alexa+** where every task ends in
a **receipt**: the plan, each step's execution, and machine-checkable
**evidence** — sha256 pairs, before/after listings, live HTTP responses.
An action is only `done` when it is *proven done*.

- MCP spec **`2025-11-25`** negotiated live on the wire (the Alexa+ track requires 2025-11-25 or later)
- Transport: **Streamable HTTP** (stateless) — the same path Alexa+ uses
- **7/7 unit tests + end-to-end smoke PASS** (`pytest tests/`, `python scripts/smoke_e2e.py`)

## Quick start

```bash
./scripts/run_local.sh
# MCP server  -> http://127.0.0.1:8765/mcp
# voice demo  -> http://127.0.0.1:8770
```

The demo UI has one-click tasks and a mic button (browser speech) — say
*"back up my photos"* and watch the receipt build: every copied file with
source/copy **sha256 pairs** compared in the same run.

## The tools

| MCP tool | What it does |
|---|---|
| `run_task(task, steps=None)` | Run a multi-step personal-ops task → returns a receipt (plan, per-step evidence, verdict) |
| `get_receipt(receipt_id)` | Re-read a stored receipt on demand — the proof, whenever you want it |
| `list_receipts(limit)` | Most recent receipts: id, task, verdict |

**Verified executors** (every one returns `action, ok, summary, evidence, verified`):

| Executor | Proof it must produce |
|---|---|
| `file_backup(source_dir, dest_dir)` | per-file sha256 of source **and** copy, byte counts, `match` flags |
| `web_check(url, expect_status, expect_text)` | HTTP status, latency, body sha256, text-found index |
| `dir_snapshot(path)` | listing, count, total bytes (the evidence primitive) |
| `file_organize(source_dir)` | before/after listings + per-move existence checks |
| `sys_check(path)` | disk usage + platform facts |

## A receipt (from the passing smoke run)

```json
{
  "receipt_id": "rcpt_1769296393_a1b2c3d4",
  "task": "smoke: back up the test suite",
  "verdict": "done-and-proven",
  "steps": [{"step": 1, "action": "file_backup", "verified": true,
             "evidence": [{"file": "test_core.py", "bytes": 3496,
                           "sha256_source": "e98d…7225",
                           "sha256_copy": "e98d…7225", "match": true}]}],
  "duration_ms": 2127
}
```

Three verdicts, and no way to fake the top one: **done-and-proven** (every step
verified), **done-unverified** (ran, proof missing), **failed** (honest,
recorded, never hidden — unparseable tasks return a receipt that says so).

## Architecture

```
 Alexa+  ──┐
           │ Streamable HTTP
 Browser ─▶ demo/bridge.py ──▶ server/app.py  (MCP server, FastMCP)
                              run_task ─▶ planner ─▶ verified executors
                                          │ (Bedrock if AWS creds, else rules)
                                          ▼
                                   receipts/*.json  (the proof, on disk)
```

- **server/app.py** — FastMCP server, Streamable HTTP, stateless
- **server/executors.py** — the verification discipline (hash/list/HTTP proofs)
- **server/planner.py** — LocalPlanner (offline rules) + BedrockPlanner (AWS mini)
- **demo/** — voice-first web UI + tiny bridge that speaks real MCP
- **tests/** + **scripts/smoke_e2e.py** — the receipt pipeline is test-proven

## Docs

- **docs/ALEXA_PLUS_SETUP.md** — expose this server to Alexa+ (tunnel + config)
- **docs/AWS_BUILDER.md** — Amazon Bedrock planner integration (mini challenge)
- **docs/DEMO_SCRIPT.md** — the 3-minute demo storyboard
- **FRICTION_LOG.md** — friction entries logged while building (10% bonus lane)
- **PRODUCT_FEEDBACK.md** — per-tool feedback, updated on real use

## Why this wins on the criteria

- **Tech Implementation** — a real MCP spec `2025-11-25` Streamable HTTP server (the track's literal requirement), evidence-bearing tools, tests that tamper data and expect the system to catch it.
- **Design** — voice-first interaction; the receipt is a first-class product object; failures are honest and explained.
- **Potential Impact** — "did it actually do it?" is the #1 consumer-agent trust gap; receipts generalize to any executor you add.
- **Quality of the Idea** — the assistant that won't claim success without proof. The LLM (Bedrock, optional) may propose; only the machine verifies.

MIT License — see LICENSE.