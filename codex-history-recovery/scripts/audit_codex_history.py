#!/usr/bin/env python3
import argparse
import hashlib
import json
import sqlite3
from collections import Counter
from pathlib import Path


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rollout_inventory(home):
    result, errors = {}, []
    counts = {"active": 0, "archived": 0}
    for directory, label in (("sessions", "active"), ("archived_sessions", "archived")):
        root = home / directory
        if not root.exists():
            continue
        for path in root.rglob("*.jsonl"):
            try:
                first = json.loads(path.open(encoding="utf-8").readline())
                payload = first.get("payload", {})
                thread_id = payload.get("id")
                if not thread_id:
                    raise ValueError("missing session id")
                if thread_id in result:
                    raise ValueError(f"duplicate id also at {result[thread_id]['path']}")
                result[thread_id] = {"path": str(path), "bucket": label, "sha256": sha256(path)}
                counts[label] += 1
            except Exception as exc:
                errors.append({"path": str(path), "error": str(exc)})
    return result, counts, errors


def db_inventory(home):
    path = home / "state_5.sqlite"
    if not path.exists():
        return {"exists": False}
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        quick = conn.execute("PRAGMA quick_check").fetchone()[0]
        columns = [row[1] for row in conn.execute("PRAGMA table_info(threads)")]
        rows = conn.execute("SELECT id,title,archived,model_provider,rollout_path FROM threads").fetchall()
        providers = Counter(row["model_provider"] for row in rows)
        abnormal = []
        for row in rows:
            title = row["title"] or ""
            reasons = []
            if not title.strip(): reasons.append("empty")
            if len(title) > 30: reasons.append("long")
            if "\n" in title: reasons.append("multiline")
            if any(token in title for token in ("tool exec", "TRANSCRIPT", "Context（", "[1] user:")):
                reasons.append("transcript-like")
            if reasons:
                abnormal.append({"id": row["id"], "title": title, "archived": bool(row["archived"]), "reasons": reasons})
        return {
            "exists": True, "path": str(path), "quick_check": quick,
            "columns": columns, "threads": len(rows),
            "active": sum(not row["archived"] for row in rows),
            "archived": sum(bool(row["archived"]) for row in rows),
            "providers": dict(providers), "ids": sorted(row["id"] for row in rows),
            "abnormal_titles": abnormal,
            "wal": (home / "state_5.sqlite-wal").exists(),
            "shm": (home / "state_5.sqlite-shm").exists(),
        }
    finally:
        conn.close()


def inspect(home):
    rollouts, counts, errors = rollout_inventory(home)
    database = db_inventory(home)
    config = home / "config.toml"
    return {
        "home": str(home), "database": database,
        "rollouts": {"counts": counts, "ids": sorted(rollouts), "errors": errors},
        "config_sha256": sha256(config) if config.exists() else None,
    }, rollouts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    target, target_rollouts = inspect(args.target)
    report = {"target": target}
    if args.source:
        source, source_rollouts = inspect(args.source)
        target_ids = set(target["database"].get("ids", []))
        source_ids = set(source["database"].get("ids", []))
        collisions = sorted(set(target_rollouts) & set(source_rollouts))
        report.update({
            "source": source,
            "comparison": {
                "source_threads_missing_from_target": sorted(source_ids - target_ids),
                "target_only_threads": sorted(target_ids - source_ids),
                "rollout_id_collisions": collisions,
                "different_rollout_collisions": [thread_id for thread_id in collisions
                    if target_rollouts[thread_id]["sha256"] != source_rollouts[thread_id]["sha256"]],
            },
        })
    text = json.dumps(report, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
