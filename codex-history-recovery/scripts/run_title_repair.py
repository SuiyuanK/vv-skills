#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
from pathlib import Path

from apply_title_map import run


def write(path, state, message, log, backup=""):
    path.write_text(json.dumps({"timestamp": dt.datetime.now().astimezone().isoformat(), "state": state, "message": message, "log": str(log), "backup": backup}, ensure_ascii=False, indent=2), encoding="utf-8")


def packaged_codex_processes():
    command = r'''Get-Process -ErrorAction SilentlyContinue |
Where-Object { try { $_.Path -like 'C:\Program Files\WindowsApps\OpenAI.Codex_*\app\*' } catch { $false } } |
ForEach-Object { "$($_.Id)|$($_.Path)" }'''
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode:
        raise RuntimeError(f"could not inspect Codex processes: {result.stderr.strip()}")
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--fail-missing", action="store_true")
    args = parser.parse_args()
    args.work_dir.mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    status = args.work_dir / "latest-title-repair-status.json"
    log_path = args.work_dir / f"title-repair-{stamp}.log"
    apply_report = args.work_dir / f"title-apply-{stamp}.json"
    verify_report = args.work_dir / f"title-verify-{stamp}.json"
    backup_root = args.home / "backups_state" / "title-repair"
    backup = ""
    with log_path.open("w", encoding="utf-8") as log:
        try:
            running = packaged_codex_processes()
            if running:
                message = "Codex Desktop is still running. Close it manually, wait for packaged processes to exit, and rerun this command."
                log.write(f"BLOCKED {message} processes={running!r}\n"); log.flush()
                write(status, "blocked", message, log_path)
                return 2
            write(status, "applying", "Codex is closed; applying title map.", log_path)
            applied = run("apply", args.home, args.map_path, backup_root, apply_report, args.fail_missing)
            backup = applied.get("backup", "")
            run("verify", args.home, args.map_path, None, verify_report, args.fail_missing)
            write(status, "complete", "Title repair completed and verified. Reopen Codex Desktop manually.", log_path, backup)
            return 0
        except Exception as exc:
            log.write(f"ERROR {type(exc).__name__}: {exc}\n"); log.flush()
            write(status, "failed", f"{type(exc).__name__}: {exc}", log_path, backup)
            return 1


if __name__ == "__main__":
    raise SystemExit(main())
