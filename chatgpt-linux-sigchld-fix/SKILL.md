---
name: chatgpt-linux-sigchld-fix
description: Diagnose and repair Linux ChatGPT/Codex Desktop conversations stuck loading when shell environment probes time out, Git is reported unavailable, and zombie helper processes accumulate. Includes a verified SIGCHLD workaround for the exact 26.924.22138 x86-64 executable, version-gated launch persistence, validation, and rollback.
---

# Linux ChatGPT/Codex conversation loading failure

Use for a desktop window that opens but cannot restore conversations or start new ones, especially with `Failed to load shell env`, `Git is unavailable`, and zombie children. This is not a general network, authentication, or deleted-history repair.

## Diagnose before changing anything

1. Identify the actual desktop executable, package/build, main PID, and latest logs. The package can be named `chatgpt-desktop-bin` while logs live under `~/.local/state/codex/logs/` and the profile under `~/.config/Codex`. Do not assume they are separate products.
2. Read recent relevant events, redacting tokens and signed asset URLs. Look for successful account queries and `thread/read`, followed by hydration/navigation timeout without a completed `thread/resume`. These distinguish successful data access from a stalled restore.
3. Confirm helper processes are zombies whose **PPID is the desktop main PID**. Check `git --version` separately. An executable found in PATH does not prove the app can observe its exit.
4. Restricted tool PID namespaces may expose only tool processes. Obtain normal host read access instead of concluding the app is absent. Identify the main PID through the user service or desktop PID metadata; never use an empty/unreadable cmdline as evidence that every Electron child is a main process.
5. If symptoms match, read [the validated case and operating procedure](references/procedure.md). A version string alone is insufficient. The included guard supports only the recorded executable hash and path.

Do not clear cookies, session databases, caches, or reinstall Git to treat this confirmed signal-handler defect. If the hash or symptom pattern differs, continue diagnosis; never refresh the allowlisted hash merely to force the old offsets onto a new build.

## Prepare, install, and verify

- Use [scripts/build_guard.py](scripts/build_guard.py) to verify the executable and compile [scripts/guard.c](scripts/guard.c) with existing GCC. It creates a unique build directory under the supplied session workspace `tmp/`; it does not install or restart anything.
- The guard blocks only the known empty SIGCHLD handler replacing an already installed handler. Other calls pass through. It removes its own `LD_PRELOAD` before children start. Never inject it globally or through `/usr/bin/chatgpt` (a shell wrapper consumes the preload first).
- [scripts/launcher.py](scripts/launcher.py) is a user-level launcher template. Follow the procedure for its config files, existing launcher backups, desktop entry preservation, and rollback. Installation requires no new service or permanent environment variable.
- If dependencies are missing, explain GCC/libc headers for compilation, Python 3.11+ for the launcher, binutils/procps for diagnosis, and optional bubblewrap/desktop-file-utils for validation. Do not install software merely to record or inspect this skill.
- Honor authorization already given for repair/restart; do not ask repeatedly. Otherwise explain that restart closes the app window before obtaining authorization. Stop the verified main process gracefully; do not indiscriminately signal all matching processes.
- After restart, require loaded guard evidence, no accumulating zombie children, and successful history rendering (`thread/resume` plus `thread_navigation outcome=success`/`content_visible`). Ask the user to check ordinary chat and new conversations if tools cannot verify them. Do not send test messages without authorization.
- Updates change the executable hash and automatically disable this guard. Report it as a version-specific workaround, not an upstream fix or permanent cross-version patch.

## Validate skill changes

Run `python3 -B scripts/test_behavior.py --workspace "$WORKSPACE"` for update bypass, existing preload preservation, literal argument handling, temporary paths, and unsupported-build refusal. Run the builder once on the supported installed binary. These checks do not start or alter the real client.

## Provenance

This is a self-authored operational skill and narrowly scoped guard from a local diagnosis and successful repair on 2026-09-28. The upstream issue is supporting technical evidence, not a vendored third-party skill: https://github.com/openai/codex/issues/48554 . The known case, test observations, and exact compatibility boundary are recorded in the procedure.
