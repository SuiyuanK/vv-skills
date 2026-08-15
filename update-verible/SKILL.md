---
name: update-verible
description: Manage the user's Linux x86_64 Verible installation from official chipsalliance/verible GitHub Releases. Use when Codex needs to interactively list and select Verible releases, verify the actual Linux release asset name, install or reinstall a release into ~/.local/bin, inspect the installed version, list backups, or safely clean old Verible backups.
---

# Update Verible

Use the bundled menu-driven script for deterministic release discovery, installation, backup, and cleanup.

## Safety boundaries

- Run as the normal user. Do not use sudo; installation targets /home/vv/.local/bin.
- Support only x86_64; stop on other architectures.
- Download only from the official chipsalliance/verible GitHub repository.
- Preserve existing verible-* commands in /home/vv/.local/share/verible-backups before installing.
- Keep backup deletion confirmation enabled.
- Keep temporary downloads under /home/vv/TMP/tmp.

## Workflow

1. Inspect the current installation:

~~~bash
command -v verible-verilog-lint || true
verible-verilog-lint --version 2>/dev/null || true
~~~

2. Run the menu:

~~~bash
bash scripts/update-verible.sh
~~~

3. Select one of these operations:

   - Upgrade or reinstall Verible: load all official release tags, select a release by number, show the actual release assets, and install the single matching Linux static x86_64 archive.
   - List backups: show timestamped backup directories from newest to oldest.
   - Clean backups: enter how many recent backups to retain, review exact deletion targets, and confirm.
   - Exit without changing anything.

4. Verify an installation:

~~~bash
command -v verible-verilog-lint
verible-verilog-lint --version
~~~

If network access is restricted, request permission before selecting the upgrade operation. Do not claim success unless the final version command succeeds.

## Bundled resource

- scripts/update-verible.sh: fully interactive release selector, asset validator, downloader, installer, backup manager, and guarded backup cleaner.
