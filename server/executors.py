"""Executors — every action returns RESULT + EVIDENCE + a verified flag.

The DID IT rule: an action is only "done" when the executor can PROVE it.
Proof = re-read what was written, hash both sides, compare listings before and
after, assert on real HTTP responses. Only then does the step earn verified=True.
"""
import hashlib
import platform
import re
import shutil
import time
import pathlib

import httpx

MAX_HASH_BYTES = 256 * 1024 * 1024  # cap hashing at 256 MB per file


def sha256_file(p: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _res(action, ok, summary, evidence, verified):
    return {"action": action, "ok": ok, "summary": summary,
            "evidence": evidence, "verified": verified}


# ---------------------------------------------------------------- executors

def file_backup(source_dir, dest_dir, pattern="*"):
    """Copy files, then prove the copies: sha256 both sides, compare."""
    src, dst = pathlib.Path(source_dir).expanduser(), pathlib.Path(dest_dir).expanduser()
    if not src.is_dir():
        return _res("file_backup", False, f"source dir not found: {src}", {"source_dir": str(src)}, False)
    dst.mkdir(parents=True, exist_ok=True)
    ev = []
    for p in sorted(src.glob(pattern)):
        if not p.is_file():
            continue
        target = dst / p.name
        shutil.copy2(p, target)
        s1, s2 = sha256_file(p), sha256_file(target)
        ev.append({"file": p.name, "bytes": p.stat().st_size,
                   "sha256_source": s1, "sha256_copy": s2, "match": s1 == s2})
    if not ev:
        return _res("file_backup", False, "no files matched", {"source_dir": str(src), "pattern": pattern}, False)
    n_ok = sum(1 for e in ev if e["match"])
    ok = n_ok == len(ev)
    return _res("file_backup", ok, f"{n_ok}/{len(ev)} files copied, sha256-verified on both sides", ev, ok)


def web_check(url, expect_status=200, expect_text=None):
    """Fetch a URL and prove what came back: status, latency, body hash, text hit."""
    t0 = time.time()
    r = httpx.get(url, timeout=15.0, follow_redirects=True)
    latency_ms = round((time.time() - t0) * 1000)
    body = r.text
    ev = {"url": url, "final_url": str(r.url), "status": r.status_code,
          "latency_ms": latency_ms, "body_bytes": len(r.content),
          "body_sha256": hashlib.sha256(r.content).hexdigest(),
          "expect_status": expect_status, "status_match": r.status_code == expect_status}
    idx = -1
    if expect_text:
        idx = body.find(expect_text)
        ev["expect_text"] = expect_text
        ev["text_found_at_index"] = idx
    ok = ev["status_match"] and (idx >= 0 if expect_text else True)
    txt = "found" if idx >= 0 else ("NOT found" if expect_text else "not requested")
    return _res("web_check", ok, f"HTTP {r.status_code} in {latency_ms} ms, text {txt}", ev, ok)


def dir_snapshot(path):
    """Evidence primitive: listing of a directory, count and total bytes."""
    d = pathlib.Path(path).expanduser()
    if not d.is_dir():
        return _res("dir_snapshot", False, f"dir not found: {d}", {"path": str(d)}, False)
    entries, total = [], 0
    for p in sorted(d.iterdir()):
        sz = p.stat().st_size if p.is_file() else None
        if p.is_file():
            total += sz
        entries.append({"name": p.name, "type": "dir" if p.is_dir() else "file", "bytes": sz})
    return _res("dir_snapshot", True, f"{len(entries)} entries, {total} bytes",
                {"path": str(d), "entries": entries, "count": len(entries), "total_bytes": total}, True)


def file_organize(source_dir):
    """Move files into per-extension subfolders; prove with before/after listings."""
    src = pathlib.Path(source_dir).expanduser()
    if not src.is_dir():
        return _res("file_organize", False, f"dir not found: {src}", {"path": str(src)}, False)
    before = dir_snapshot(source_dir)["evidence"]
    moved = []
    for p in sorted(src.iterdir()):
        if p.is_file():
            sub = src / p.suffix.lstrip(".").lower()
            sub.mkdir(exist_ok=True)
            dest = sub / p.name
            shutil.move(str(p), str(dest))
            moved.append({"file": p.name, "to": str(dest), "exists_after": dest.exists()})
    after = dir_snapshot(source_dir)["evidence"]
    ok = bool(moved) and all(m["exists_after"] for m in moved) \
        and after["count"] >= before["count"]
    return _res("file_organize", ok, f"moved {len(moved)} files into extension folders",
                {"before": before, "moved": moved, "after": after}, ok)


def sys_check(path="/"):
    """System facts (disk usage) as evidence."""
    d = pathlib.Path(path).expanduser()
    if not d.exists():
        return _res("sys_check", False, f"path not found: {d}", {"path": str(d)}, False)
    t, u, f = shutil.disk_usage(str(d))
    ev = {"path": str(d), "total_bytes": t, "used_bytes": u, "free_bytes": f,
          "platform": platform.platform(), "python": platform.python_version()}
    return _res("sys_check", True, f"{f/1e9:.1f} GB free of {t/1e9:.1f} GB", ev, True)


EXECUTORS = {
    "file_backup": file_backup,
    "web_check": web_check,
    "dir_snapshot": dir_snapshot,
    "file_organize": file_organize,
    "sys_check": sys_check,
}


def execute(action: str, args: dict) -> dict:
    if action not in EXECUTORS:
        raise ValueError(f"unknown action '{action}'; available: {sorted(EXECUTORS)}")
    return EXECUTORS[action](**args)