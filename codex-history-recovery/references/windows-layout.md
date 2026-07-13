# Windows Codex local-history layout

## Data sources

| Path | Role | Recovery policy |
|---|---|---|
| `%USERPROFILE%\.codex\sessions` | Active rollout JSONL | Merge by relative path and content hash |
| `%USERPROFILE%\.codex\archived_sessions` | Archived rollout JSONL | Merge separately; preserve archive state |
| `%USERPROFILE%\.codex\state_5.sqlite` | Primary task metadata | Transactional, missing rows only during restore |
| `%USERPROFILE%\.codex\state_5.sqlite-wal/-shm` | Uncheckpointed live state | Treat as part of the database |
| `%USERPROFILE%\.codex\sqlite\state_5.sqlite` | Version-dependent App database | Inspect and synchronize only when present |
| `%USERPROFILE%\.codex\session_index.jsonl` | Sidebar title index | Upsert alongside title changes |
| `%USERPROFILE%\.codex\.codex-global-state.json` | Saved projects and UI state | Selectively merge project keys only |
| `%USERPROFILE%\.codex\config.toml` | Provider/model configuration | Hash and preserve |
| `%USERPROFILE%\.codex\auth.json` | Account credentials | Never import from backup |

## SQLite cautions

- Discover table schemas with `PRAGMA table_info`; versions add columns.
- Insert using the intersection of source and target columns, while satisfying target non-null columns.
- Attach the source database read-only where possible.
- Validate `thread_dynamic_tools` by existing thread ID.
- Insert `thread_spawn_edges` only when parent and child endpoints exist.
- Normalize `\\?\C:\...` before Windows containment checks.
- Never infer current counts from copied main SQLite files when a WAL exists.

## Title authority

Use this order as evidence, not as an unconditional overwrite rule:

1. Concise title in the prior Desktop App database.
2. Existing `session_index.jsonl` title.
3. Legacy `threads.title`.
4. A new concise title derived from actual rollout user messages.

Reject a candidate title when it is empty, mostly a path, a pasted webpage, a transcript, a log, a code block, a multi-step plan, or substantially longer than a sidebar label.

## Saved projects

Project visibility is not reconstructed merely by restoring thread `cwd`. Inspect backup and current global-state JSON, identify the version-specific saved-root/order/assignment keys, retain only roots that still exist, and merge only those keys. Back up the whole current global-state file first.

## Process lifecycle

The reliable Windows pattern is:

1. Start an independent worker process while Codex is still open.
2. Let that worker wait briefly.
3. Stop only processes whose executable path matches `C:\Program Files\WindowsApps\OpenAI.Codex_*\app\*`.
4. Mutate and verify data in the already-running worker.
5. Restart with `explorer.exe shell:AppsFolder\OpenAI.Codex_2p2nqsd0c76g0!App`.

Starting Python from a new Windows PowerShell process after Codex is killed can fail in some packaged environments; start the Python worker first.
