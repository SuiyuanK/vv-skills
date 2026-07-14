---
name: codex-history-recovery
description: Safely diagnose, restore, merge, verify, and repair local Codex Desktop history on Windows, including sessions, archived sessions, state_5.sqlite metadata, saved projects, provider visibility, and unreadable sidebar titles. Use after uninstall/reinstall, provider changes, missing history or projects, partial restores, malformed titles, SQLite/WAL drift, or when a user supplies backup .codex and OpenAI package directories.
---

# Codex History Recovery

Recover local Codex data without overwriting the current account, configuration, new tasks, or user deletions.

## Core rules

- Treat every backup as read-only.
- Work from a user-approved target, normally `%USERPROFILE%\.codex`.
- Put task-specific scripts and reports in the active workspace's `.codex/vvwork/` and maintain its `INDEX.md`.
- Never restore `auth.json`, `config.toml`, `.codex-global-state.json`, or package state wholesale.
- Never trust a lone `state_5.sqlite` copy while WAL exists. Read or copy the database together with `-wal` and `-shm`, or use SQLite backup APIs.
- Take a timestamped rollback snapshot immediately before each mutation.
- Stop on same-name rollout files with different content.
- Preserve tasks created after reinstall and preserve intentional user deletions.
- Run SQLite `quick_check` before and after every database mutation.
- Never stop or relaunch Codex Desktop automatically. Ask the user to close it manually before writes and reopen it manually after verification.

Read [references/windows-layout.md](references/windows-layout.md) before changing live data.

## Workflow

1. Inventory source and target with `scripts/audit_codex_history.py`.
2. Compare rollout IDs, SQLite thread IDs, active/archive counts, providers, malformed rollout first lines, and path roots.
3. Record current `config.toml` SHA-256 and current task IDs.
4. Prepare and audit the repair while Codex is open, then ask the user to close Codex Desktop manually. Run writes from an external PowerShell only after the App is fully closed; the bundled title worker refuses to write while packaged Codex processes remain.
5. Merge rollout files by original relative path. Refuse differing collisions.
6. In one SQLite transaction, insert only missing `threads` rows using common columns. Add related dynamic-tool and valid spawn-edge rows only when their endpoints exist. Rewrite restored rollout paths to the current Codex home and set the intended provider.
7. Do not create missing historical working directories unless requested.
8. Restore saved projects separately by selectively merging existing workspace roots and project ordering from `.codex-global-state.json`. Do not derive projects from every historical `cwd`.
9. Repair titles after session restoration. Prefer a genuine prior Desktop App title when concise; otherwise derive a short action-and-object title from the actual rollout. Avoid raw prompts, pasted pages, paths, logs, plans, and duplicate placeholders.
10. Verify database integrity, unique IDs, rollout parsing, current-home paths, provider consistency, preserved configuration hash, and saved projects. Ask the user to reopen Codex manually, then verify the sidebar in the next turn.

## Read-only audit

```powershell
python scripts/audit_codex_history.py `
  --target "$env:USERPROFILE\.codex" `
  --source "D:\backup\.codex" `
  --report ".codex\vvwork\history-recovery\audit.json"
```

Use the report to calculate expected counts dynamically. Do not carry counts from an earlier run after the user archives or deletes tasks.

## Title repair

Create a UTF-8 JSON map:

```json
{
  "thread-uuid": "Short readable title"
}
```

Audit the plan:

```powershell
python scripts/apply_title_map.py audit --home "$env:USERPROFILE\.codex" --map title-map.json
```

After the audit passes, ask the user to close Codex Desktop manually. From an external PowerShell, run:

```powershell
& C:\Python314\python.exe `
  'scripts/run_title_repair.py' `
  --home "$env:USERPROFILE\.codex" `
  --map 'title-map.json' `
  --work-dir '.codex\vvwork\history-recovery'
```

The worker checks that packaged Codex processes are no longer running, backs up SQLite/WAL/index files, updates both `threads.title` and `session_index.jsonl`, and verifies the result. It never stops or relaunches the App. After it reports `complete`, ask the user to reopen Codex manually from the Start menu. Missing IDs are skipped by default so deleted tasks are not resurrected.

## Title quality

- Aim for roughly 6-18 Chinese characters or a similarly compact English title.
- Use `动作 + 对象`, such as `查找上海高校与研究所` or `分析 FFT 模块资源占用`.
- Distinguish genuinely different tasks; identical retry/approval artifacts may share one clear title.
- Preserve concise meaningful titles even when duplicated.
- Label contentless interrupted tasks conservatively, for example `未完成的空白任务`.

## Failure handling

- If a mutation or verification fails, keep Codex closed and restore the latest complete snapshot.
- After any successful repair, leave Codex closed and tell the user to reopen it manually; do not use `explorer.exe`, a hard-coded AppUserModelId, or a background auto-restart helper.
- If the database is correct but the UI is stale, inspect `session_index.jsonl`, the package App database, and restart behavior before rewriting data again.
- If an official rename API cannot find a restored thread, use the title-map workflow rather than assuming the task is absent.
- In Windows PowerShell 5, always read UTF-8 JSON with `Get-Content -Encoding UTF8`; avoid parsing Python UTF-8 output through the console.
