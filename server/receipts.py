"""Receipts — append-only, evidence-bearing records of every task run.

A receipt is the unit of trust in DID IT: plan, per-step execution with
machine-checkable evidence, and a verdict. Receipts persist as JSON under
./receipts/ so any client (or a human, or an auditor) can re-read the proof.
"""
import json
import pathlib
import time
import uuid

RECEIPTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "receipts"


def new_receipt_id() -> str:
    return f"rcpt_{int(time.time())}_{uuid.uuid4().hex[:8]}"


def save(receipt: dict) -> dict:
    RECEIPTS_DIR.mkdir(exist_ok=True)
    (RECEIPTS_DIR / f"{receipt['receipt_id']}.json").write_text(json.dumps(receipt, indent=2))
    return receipt


def get(receipt_id: str) -> dict | None:
    p = RECEIPTS_DIR / f"{receipt_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def list_all(limit: int = 25) -> list[dict]:
    RECEIPTS_DIR.mkdir(exist_ok=True)
    out = []
    for p in sorted(RECEIPTS_DIR.glob("rcpt_*.json"), reverse=True)[:limit]:
        out.append(json.loads(p.read_text()))
    return out