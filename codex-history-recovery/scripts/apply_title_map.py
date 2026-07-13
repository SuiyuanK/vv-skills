#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import os
import shutil
import sqlite3
from pathlib import Path


def load_map(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(data, list):
        data = {item["id"]: item["title"] for item in data}
    if not isinstance(data, dict) or not data:
        raise ValueError("title map must be a non-empty object or [{id,title}] list")
    result = {}
    for thread_id, title in data.items():
        if not isinstance(thread_id, str) or not isinstance(title, str) or not title.strip():
            raise ValueError(f"invalid title-map entry: {thread_id!r}")
        if "\n" in title or len(title) > 80:
            raise ValueError(f"title is not sidebar-safe: {thread_id}")
        result[thread_id] = title.strip()
    return result


def connect(path):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def inspect(home, mapping):
    db = home / "state_5.sqlite"
    with connect(db) as conn:
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        if quick != "ok":
            raise RuntimeError(f"SQLite quick_check failed: {quick}")
        rows = {row["id"]: row for row in conn.execute("SELECT id,title,archived FROM threads")}
        counts = tuple(conn.execute("SELECT COUNT(*),SUM(archived=0),SUM(archived=1) FROM threads").fetchone())
    existing = {key: value for key, value in mapping.items() if key in rows}
    missing = sorted(set(mapping) - set(rows))
    pending = {key: value for key, value in existing.items() if rows[key]["title"] != value}
    return rows, existing, missing, pending, {"total": counts[0], "active": counts[1], "archived": counts[2]}


def snapshot(home, root):
    destination = root / dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    destination.mkdir(parents=True, exist_ok=False)
    for name in ("state_5.sqlite", "state_5.sqlite-wal", "state_5.sqlite-shm", "session_index.jsonl"):
        source = home / name
        if source.exists(): shutil.copy2(source, destination / name)
    return destination


def read_index(path):
    if not path.exists(): return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def run(mode, home, map_path, backup_root=None, report_path=None, fail_missing=False):
    mapping = load_map(map_path)
    rows, existing, missing, pending, counts = inspect(home, mapping)
    if fail_missing and missing:
        raise RuntimeError(f"missing thread IDs: {missing}")
    result = {"mode": mode, "mapped": len(mapping), "existing": len(existing), "skipped_missing": len(missing), "pending": len(pending), "counts": counts}
    if mode == "audit":
        result["changes"] = [{"id": key, "archived": bool(rows[key]["archived"]), "old": rows[key]["title"], "new": value} for key, value in pending.items()]
    elif mode == "apply":
        if backup_root is None: raise ValueError("backup root is required for apply")
        backup = snapshot(home, backup_root)
        db = home / "state_5.sqlite"
        with connect(db) as conn:
            conn.execute("BEGIN IMMEDIATE")
            for thread_id, title in pending.items():
                if conn.execute("UPDATE threads SET title=? WHERE id=?", (title, thread_id)).rowcount != 1:
                    raise RuntimeError(f"failed to update {thread_id}")
            conn.commit()
        index_path = home / "session_index.jsonl"
        records = read_index(index_path)
        by_id = {record.get("id"): record for record in records}
        now = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
        for thread_id, title in existing.items():
            record = by_id.get(thread_id)
            if record is None:
                record = {"id": thread_id, "thread_name": title, "updated_at": now}
                records.append(record); by_id[thread_id] = record
            else:
                record.update({"thread_name": title, "updated_at": now})
        temporary = index_path.with_suffix(".jsonl.tmp")
        temporary.write_text("".join(json.dumps(x, ensure_ascii=False, separators=(",", ":")) + "\n" for x in records), encoding="utf-8")
        os.replace(temporary, index_path)
        _, _, _, remaining, counts2 = inspect(home, mapping)
        if remaining: raise RuntimeError(f"titles still pending: {sorted(remaining)}")
        result.update({"backup": str(backup), "updated": len(pending), "pending_after": 0, "counts_after": counts2})
    else:
        if pending: raise RuntimeError(f"verification found {len(pending)} pending titles")
        index = {item.get("id"): item.get("thread_name") for item in read_index(home / "session_index.jsonl")}
        bad = sorted(key for key, title in existing.items() if index.get(key) != title)
        if bad: raise RuntimeError(f"session index mismatch: {bad}")
        result["index_matches"] = len(existing)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if report_path:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(text, encoding="utf-8")
    print(text)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("audit", "apply", "verify"))
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path, required=True)
    parser.add_argument("--backup-root", type=Path)
    parser.add_argument("--report", dest="report_path", type=Path)
    parser.add_argument("--fail-missing", action="store_true")
    args = parser.parse_args()
    run(**vars(args))


if __name__ == "__main__":
    main()
