---
name: ghostty-desktop-integration
description: Configure and diagnose Ghostty desktop integration on Arch-family Linux systems running GNOME or Cinnamon/Nemo. Use when the default terminal or Ctrl+Alt+T opens the wrong app, when safely replacing an old terminal with Ghostty, or when Nemo Open in Terminal opens an existing Ghostty window's directory instead of the selected folder.
---

# Ghostty Desktop Integration

Route the request by the active desktop and observed failure. Do not mix GNOME and Cinnamon settings: they use different schemas and solve different problems.

## Identify the environment first

Start read-only:

```bash
printf 'XDG_CURRENT_DESKTOP=%s\n' "$XDG_CURRENT_DESKTOP"
printf 'DESKTOP_SESSION=%s\n' "$DESKTOP_SESSION"
command -v ghostty
ghostty --version
```

- For a GNOME session, read [references/gnome.md](references/gnome.md). Use it for the default terminal, `Ctrl+Alt+T`, and safe removal of an old terminal.
- For Cinnamon with Nemo, read [references/cinnamon-nemo.md](references/cinnamon-nemo.md). Use it only for Nemo's **Open in Terminal** working-directory failure caused by Ghostty single-instance reuse.
- If the variables are empty, conflicting, or identify another desktop, gather session evidence and ask the user before changing any setting. Do not guess a schema from installed packages alone.

## Shared boundaries

- Inspect current settings and targets before writes. A diagnostic request does not authorize a repair.
- Keep changes user-scoped unless the selected reference explicitly reaches an approved package operation.
- Do not modify system Ghostty desktop files or global Ghostty configuration to solve a file-manager integration problem.
- Before uninstalling another terminal, launch Ghostty and verify the intended shortcut or file-manager action end to end.
- Preserve rollback information for every changed setting or user-owned wrapper.
