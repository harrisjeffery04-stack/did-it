"""Unit tests for the ProvenDone core (offline-safe, no network).

These test the verification discipline itself: every executor must return
evidence and only set verified=True when the proof holds.
"""
import json
import pathlib

import pytest

from server import receipts
from server.executors import (file_backup, file_organize, dir_snapshot,
                             execute, sha256_file)
from server.planner import LocalPlanner


def _mkfiles(d: pathlib.Path, names=("a.txt", "b.txt", "c.jpg")):
    d.mkdir(parents=True, exist_ok=True)
    for n in names:
        p = d / n
        p.write_bytes(f"provendone fixture {n} ".encode() * 50)
    return d


def test_file_backup_proves_copies(tmp_path):
    src = _mkfiles(tmp_path / "src")
    dst = tmp_path / "vault"
    r = file_backup(str(src), str(dst))
    assert r["verified"] and r["ok"]
    assert len(r["evidence"]) == 3
    for e in r["evidence"]:
        assert e["match"] is True
        assert e["sha256_source"] == e["sha256_copy"]
    # tamper one copy: hashes now diverge — proof of tampering is visible
    (dst / "a.txt").write_bytes(b"TAMPERED")
    assert sha256_file(src / "a.txt") != sha256_file(dst / "a.txt")
    # a fresh backup run REPAIRS the tampered copy and re-proves it
    # (idempotent + self-healing: evidence is gathered per run)
    r2 = file_backup(str(src), str(dst))
    assert r2["verified"] and r2["evidence"][0]["match"] is True


def test_file_backup_missing_source(tmp_path):
    r = file_backup(str(tmp_path / "nope"), str(tmp_path / "dst"))
    assert r["ok"] is False and r["verified"] is False


def test_dir_snapshot_counts(tmp_path):
    _mkfiles(tmp_path / "d")
    r = dir_snapshot(str(tmp_path / "d"))
    assert r["verified"] and r["evidence"]["count"] == 3
    assert r["evidence"]["total_bytes"] > 0


def test_file_organize_before_after(tmp_path):
    _mkfiles(tmp_path / "messy", names=("x.png", "y.jpg", "z.txt"))
    r = file_organize(str(tmp_path / "messy"))
    assert r["verified"]
    assert r["evidence"]["before"]["count"] == 3
    assert r["evidence"]["after"]["count"] >= 3  # files now inside ext subfolders
    moved_names = [m["file"] for m in r["evidence"]["moved"]]
    assert set(moved_names) == {"x.png", "y.jpg", "z.txt"}
    for m in r["evidence"]["moved"]:
        assert pathlib.Path(m["to"]).exists()


def test_execute_dispatch_errors():
    with pytest.raises(ValueError, match="unknown action"):
        execute("not_a_tool", {})
    r = execute("sys_check", {})
    assert r["verified"]


def test_local_planner_rules():
    pl = LocalPlanner()
    p = pl.plan("backup /data/photos to /data/vault")
    assert p == [{"action": "file_backup",
                  "args": {"source_dir": "/data/photos", "dest_dir": "/data/vault"}}]
    p = pl.plan("check https://example.com is up")
    assert p[0]["action"] == "web_check" and p[0]["args"]["url"].startswith("https://")
    p = pl.plan("organize /data/messy")
    assert p == [{"action": "file_organize", "args": {"source_dir": "/data/messy"}}]
    assert pl.plan("do something completely unrelated") == []


def test_receipts_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(receipts, "RECEIPTS_DIR", tmp_path)
    r = {"receipt_id": "rcpt_test_1", "task": "t", "verdict": "done-and-proven",
         "steps": []}
    receipts.save(r)
    assert receipts.get("rcpt_test_1")["task"] == "t"
    assert receipts.get("missing") is None
    assert receipts.list_all()[0]["receipt_id"] == "rcpt_test_1"