"""ProvenDone MCP server — the Alexa+ integration.

Self-hosted MCP server (Streamable HTTP transport, MCP spec 2025-11-25+)
exposing the verified personal-ops toolset:

  run_task(task, steps=None)  -> executes a multi-step task; returns a receipt
                                 (plan, per-step evidence, verdict)
  get_receipt(receipt_id)     -> re-reads a stored receipt on demand
  list_receipts(limit)       -> most recent receipts (id, task, verdict)

Run:  python -m server.app   (or scripts/run_local.sh)
"""
import os
import time

from mcp.server.fastmcp import FastMCP

from . import receipts
from .executors import EXECUTORS, execute
from .planner import get_planner

mcp = FastMCP(
    "provendone",
    instructions=(
        "ProvenDone: personal-ops tasks that end in verification receipts. "
        "Call run_task with a task description and optional explicit steps: "
        "a list of {\"action\": ..., \"args\": {...}}. Available actions: "
        + ", ".join(sorted(EXECUTORS)) +
        ". Every step is executed AND verified with machine-checkable evidence "
        "(sha256 pairs, before/after listings, live HTTP responses); the returned "
        "receipt proves the task is done. Use get_receipt(receipt_id) to re-read "
        "the stored proof at any time."
    ),
    stateless_http=True,
    host=os.environ.get("PROVENDONE_HOST", "127.0.0.1"),
    port=int(os.environ.get("PROVENDONE_PORT", "8765")),
)


@mcp.tool()
def run_task(task: str, steps: list[dict] | None = None) -> dict:
    """Run a multi-step personal-ops task and return a verification receipt.

    Args:
        task: what the user wants done, in plain language.
        steps: optional explicit plan — list of {"action": ..., "args": {...}}.
               If omitted, a planner proposes one (Amazon Bedrock when AWS
               credentials are configured, else a rule-based local planner).

    Returns a receipt: receipt_id, task, per-step results with evidence,
    verdict (done-and-proven / done-unverified / failed), duration, summary.
    """
    t0 = time.time()
    rid = receipts.new_receipt_id()
    pl = get_planner()
    plan = steps if steps else pl.plan(task)
    if not plan:
        receipt = {
            "receipt_id": rid, "task": task, "planner": pl.name, "steps": [],
            "verdict": "failed",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
            "duration_ms": round((time.time() - t0) * 1000),
            "summary": ("No plan could be proposed for this task. Pass explicit "
                        "steps (actions: " + ", ".join(sorted(EXECUTORS)) +
                        ") or configure the Bedrock planner — see docs/AWS_BUILDER.md."),
        }
        receipts.save(receipt)
        return receipt

    results = []
    for i, step in enumerate(plan, 1):
        try:
            r = execute(step.get("action"), step.get("args", {}))
        except Exception as e:  # honest failure is recorded, never hidden
            r = {"action": step.get("action"), "ok": False, "verified": False,
                 "summary": f"executor error: {e}", "evidence": {"error": str(e)}}
        results.append({"step": i, **r})

    verified_all = all(s["verified"] for s in results)
    any_ok = any(s["ok"] for s in results)
    verdict = "done-and-proven" if verified_all else ("done-unverified" if any_ok else "failed")
    receipt = {
        "receipt_id": rid, "task": task,
        "planner": "explicit" if steps else pl.name,
        "steps": results, "verdict": verdict,
        "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t0)),
        "duration_ms": round((time.time() - t0) * 1000),
        "summary": "; ".join(s["summary"] for s in results),
    }
    receipts.save(receipt)
    return receipt


@mcp.tool()
def get_receipt(receipt_id: str) -> dict:
    """Re-read a stored verification receipt by ID — the proof, on demand."""
    r = receipts.get(receipt_id)
    return r if r else {"error": f"receipt '{receipt_id}' not found"}


@mcp.tool()
def list_receipts(limit: int = 10) -> dict:
    """List the most recent receipts: receipt_id, task, verdict."""
    items = [{"receipt_id": r["receipt_id"], "task": r["task"], "verdict": r["verdict"]}
             for r in receipts.list_all(limit)]
    return {"count": len(items), "receipts": items}


def main() -> None:
    """Entry point — serve MCP over Streamable HTTP."""
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()