#!/usr/bin/env python3
import argparse
import datetime as dt
import json
import subprocess
import time
from pathlib import Path

from apply_title_map import run


def write(path, state, message, log, backup=""):
    path.write_text(json.dumps({"timestamp": dt.datetime.now().astimezone().isoformat(), "state": state, "message": message, "log": str(log), "backup": backup}, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home", type=Path, required=True)
    parser.add_argument("--map", dest="map_path", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--delay", type=int, default=12)
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
            write(status, "waiting", "Independent worker waiting before closing Codex.", log_path)
            time.sleep(args.delay)
            stop = "Get-Process -ErrorAction SilentlyContinue | Where-Object { try { $_.Path -like 'C:\\Program Files\\WindowsApps\\OpenAI.Codex_*\\app\\*' } catch { $false } } | Stop-Process -Force"
            result = subprocess.run(["powershell.exe", "-NoProfile", "-Command", stop], capture_output=True, text=True, timeout=30)
            log.write(f"stop rc={result.returncode} stdout={result.stdout!r} stderr={result.stderr!r}\n"); log.flush()
            if result.returncode: raise RuntimeError("could not stop Codex")
            time.sleep(4)
            write(status, "applying", "Codex stopped; applying title map.", log_path)
            applied = run("apply", args.home, args.map_path, backup_root, apply_report, args.fail_missing)
            backup = applied.get("backup", "")
            run("verify", args.home, args.map_path, None, verify_report, args.fail_missing)
            write(status, "complete", "Title repair completed and verified.", log_path, backup)
        except Exception as exc:
            log.write(f"ERROR {type(exc).__name__}: {exc}\n"); log.flush()
            write(status, "failed", f"{type(exc).__name__}: {exc}", log_path, backup)
        finally:
            subprocess.Popen(["explorer.exe", "shell:AppsFolder\\OpenAI.Codex_2p2nqsd0c76g0!App"])


if __name__ == "__main__":
    main()
