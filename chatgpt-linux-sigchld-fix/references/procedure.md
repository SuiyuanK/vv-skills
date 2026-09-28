# Verified case and procedure

## Compatibility and evidence

- Date: 2026-09-28. CachyOS x86-64, GNOME, kernel 7.2.8, glibc 2.44.
- ChatGPT Desktop 26.924.22138; build 11645; app commit `2e782921399a788a842b74ee1944a2e1e6e003a1`; Electron 42.3.0.
- Executable: `/usr/lib/chatgpt/ChatGPT`.
- SHA-256: `23b753552181a8ea661681256c2dbf993fea1285fbc5c824478bad9cbdd45c91`.
- A SIGCHLD installer at virtual address `0x723eb00` invokes `sigaction(17, ...)` with handler `0x117d9f78`. That jump (`e9 4b ca 50 00`) reaches `0x11ce69c8`, bytes `55 48 89 e5 5d c3`: an empty function. These were disassembled locally, independently of the issue report.
- The initial client kept exited zsh/git/ps/gh helpers as zombies. Account lookup and metadata reads worked. Restoring a thread timed out after 30 seconds.
- Two separate 15-second headless instances: stock had 4 zombie children and a 5-second shell environment timeout; guarded had 0 zombies, no shell timeout, and emitted the guard interception notice. Both connected to their isolated app-server.
- Real signed-in restart: guard present in `/proc/<main-pid>/maps`, 0 direct zombie children; `thread/resume` succeeded in 93 ms; navigation reached `content_visible` and success in 1262.5 ms. The user subsequently confirmed recovery. No history or authentication files were deleted.

Reference: https://github.com/openai/codex/issues/48554 (user report in the OpenAI repository, not an official release guarantee). Recheck current upstream status when deciding whether a new version still needs a fix.

## Build

Set `WORKSPACE` to the directory where the task began. Use an absolute existing directory, not the skill directory merely because commands run there.

```sh
python3 -B scripts/build_guard.py --workspace "$WORKSPACE"
```

Run from this skill directory, or use the script's absolute path. The output is a newly created directory containing `guard.c`, `guard.so`, and `binary.sha256`. The script refuses an unsupported executable before compilation. Keep generated binaries out of the skill repository.

## Optional isolated A/B validation

Use separate stock/guard profiles, no account sign-in, and explicit HOME, CODEX_HOME, XDG_CONFIG_HOME, XDG_CACHE_HOME, XDG_STATE_HOME, XDG_DATA_HOME, XDG_RUNTIME_DIR, TMPDIR and `--user-data-dir`, all under a unique workspace `tmp/` directory. This prevents touching the real app state.

The validated method used bubblewrap: read-only host root, writable test directory, private PID namespace, private proc/dev, and test tmp bound over `/tmp` and `/var/tmp`. Start the installed executable directly with `--ozone-platform=headless --disable-gpu`. `--no-sandbox` was used only inside that separate unauthenticated outer sandbox; do not copy it to the real desktop launcher. Apply `LD_PRELOAD` to the executable inside the sandbox, not to the bwrap process. Inspect each instance's own process tree after 15 seconds and its shell-env/handshake logs, then terminate only that test process group.

If temporary writes cannot be contained or headless startup is unsupported, stop that test method and report the limitation. Do not launch an unisolated second instance or use the real profile for A/B tests.

## User-level installation

1. Inspect current `~/.local/bin/chatgpt`, the vendor `.desktop`, and any user `.desktop` override. Preserve existing unrelated customizations; snapshot file contents, mode, symlink target, and absent/present status in a unique persistent backup directory. Do not overwrite an unrelated wrapper silently.
2. Use `~/.local/share/chatgpt-sigchld-fix/` for persistent `guard.so`, `guard.c`, and `binary.sha256`. Write the original session workspace absolute path plus a newline into `workspace-root` there. Copy `scripts/launcher.py` to the agreed user launcher path, normally `~/.local/bin/chatgpt`, and make it executable. The template looks for that fixed user-level data directory; update both locations deliberately if choosing another destination.
3. Preserve the existing desktop entry's MIME types, icon, categories, actions and other settings. Change only the main `Exec=` to an absolute launcher path and retain its argument field codes (`%U` in the validated case). Quote/escape paths correctly for desktop-entry syntax. Inspect action-specific Exec fields if they launch the same executable. Put the user override under the same desktop ID as the vendor entry; do not modify `/usr/share/applications/`.
4. Validate the desktop file if desktop-file-validate is present. Confirm no extra global LD_PRELOAD settings were introduced. The wrapper preserves literal one-argument-per-line `chatgpt-flags.conf` entries; it never evaluates shell code. If an existing LD_PRELOAD is set, it skips this guard rather than discarding another preload. Investigate that case explicitly.
5. Gracefully stop the **verified main PID** and wait for exit before starting the wrapper. If it does not exit, report the running state instead of force-killing. A known user unit's MainPID is preferable to a broad pgrep. Recheck `/proc` identity immediately before signaling to avoid PID reuse.
6. Launch in the user's actual graphical session environment. A transient `systemd-run --user --collect --property=Type=exec` unit was used successfully; it is not required for future menu launches. Do not inherit tool sandbox proxy credentials or synthetic display settings.
7. Verify loaded guard and history rendering as described in SKILL.md. Inspect TMPDIR and runtime pipe locations without exposing the full process environment. Subsequent menu launches must hit the wrapper; direct `/usr/bin/chatgpt` bypasses it. A CLI `chatgpt` command works only if PATH resolves to the user wrapper first.

The launcher deliberately gates on the exact executable SHA-256, not a package version alone. It creates each runtime temporary directory under the recorded workspace `tmp/`, without overwriting existing directories. Keep that workspace available for future launches. It does not automatically clean runtime directories because active sockets/files may still be in use.

## Updates and rollback

A changed executable skips the guard automatically. Confirm new-version behavior and upstream status before adapting. Do not reuse offsets with a new allowlisted hash without disassembly and isolated tests. An existing installation remains on its current launcher revision when merely recording this skill; updating the skill is not permission to replace live repair files.

To roll back: quit the verified app, restore the exact original user launcher and desktop entry from the installation backup; remove only entries proven newly created by this repair when the originals were absent. Leave vendor files, profiles, history and authentication untouched. Start through the restored entry or `/usr/bin/chatgpt`. Remove the repair data only after verifying rollback and confirming no launcher references it. Clean only known inactive temporary directories created by this task, never the whole workspace tmp tree.
