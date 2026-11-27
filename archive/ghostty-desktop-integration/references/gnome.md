# Ghostty terminal integration on GNOME and CachyOS/Arch

Use this reference after confirming an active GNOME session. Check terminal selection and the keyboard shortcut independently.

## Terminal selection

Check the installed versions and the terminal candidates on PATH:

```bash
pacman -Q glib2 gsettings-desktop-schemas ghostty
command -v xdg-terminal-exec ghostty
```

Inspect the installed `org.gnome.desktop.default-applications.terminal` schema. When it marks `exec` and `exec-arg` as deprecated and ignored, verify terminal selection through GIO. If `xdg-terminal-exec` is available, inspect its selection with `xdg-terminal-exec --print-id`. Otherwise, test a known application that uses `Terminal=true` and observe which terminal starts. The fallback list can vary by distribution and package build.

On 2026-11-27, CachyOS with GNOME 51.1, `glib2 2.90.2-1.1` and Ghostty 1.4.0 selected `ghostty -e` through GIO without `xdg-terminal-exec`. A launch trace confirmed this both with an isolated settings backend and after clearing the legacy user overrides.

On a system where the keys are ignored, clear these overrides only when the user requests cleanup and the stored values match the old Ghostty setup. Read and retain those values for rollback with:

```bash
dconf read /org/gnome/desktop/applications/terminal/exec
dconf read /org/gnome/desktop/applications/terminal/exec-arg
```

For the old setup the stored values are `'ghostty'` and `''`. Reset just these two keys and verify that both `dconf read` commands return no value. GSettings can still show schema defaults after the reset.

```bash
gsettings reset org.gnome.desktop.default-applications.terminal exec
gsettings reset org.gnome.desktop.default-applications.terminal exec-arg
```

Repeat the GIO launch test after cleanup.

## Ctrl+Alt+T

The installed GNOME Settings Daemon 51.1 on CachyOS has no built-in terminal shortcut. A custom binding can call `ghostty` directly.

```bash
gsettings list-keys org.gnome.settings-daemon.plugins.media-keys
gsettings get org.gnome.settings-daemon.plugins.media-keys custom-keybindings
```

Inspect the matching custom entry for its command and binding. Use GNOME Settings → Keyboard → View and Customize Shortcuts → Custom Shortcuts to add or edit the Ghostty binding if requested. Preserve the other shortcut entries. Press `Ctrl+Alt+T` and verify that it opens a Ghostty window.

If the task involves a file manager action, test **Open in Terminal** in the selected folder. Before removing an old terminal package, check reverse dependencies and get approval for the specific package removal.
