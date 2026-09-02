---
name: xilinx-vitis-desktop-launch-fix
description: >-
  Diagnose and repair AMD Xilinx Vitis 2025.x GNOME menu entries when Vitis
  Commandline Tool immediately exits instead of opening an interactive shell,
  or Vitis Model Composer starts MATLAB only as an invisible background
  process. Use on Linux desktop launch failures after the tools are installed;
  do not use for installer hangs, license failures, or Dock icon matching.
---

# Xilinx Vitis desktop launch repair

Treat the two symptoms separately. Both vendor launchers may appear to do
nothing, but one loses its interactive terminal while the other needs a
controlling PTY for MATLAB. Diagnose from the real desktop session before
editing anything.

## Boundaries

- Keep diagnosis read-only until the user authorizes a repair.
- Modify only user files under `~/.local/`; never patch the Xilinx or MATLAB
  installation tree for these launch failures.
- Discover the installed version, paths, desktop filenames, active desktop,
  login shell, and terminal configuration. Do not reuse historical absolute
  paths or assume Ghostty is installed.
- Preserve the vendor launcher for rollback. If a fresh desktop ID is needed,
  hide the old user launcher with `NoDisplay=true` rather than deleting it.
- Do not kill invisible MATLAB or Model Composer processes without permission;
  they may contain user state.
- Route a running-window generic icon, duplicate Dock item, or wrong grouping
  to `$gnome-xwayland-dock-icon-fix`. Route MATLAB allocator crashes, GCC/MEX,
  or MATLAB's own launcher problems to `$matlab-cachyos-fix`.

## Establish the environment and exact launchers

Confirm GNOME and inspect the actual user launchers and executables:

```bash
printf 'session=%s desktop=%s shell=%s\n' \
  "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP" "$(getent passwd "$USER" | cut -d: -f7)"
command -v script desktop-file-validate update-desktop-database

rg -l --glob='*.desktop' \
  'Vitis Commandline Tool|Vitis Model Composer' \
  "$HOME/.local/share/applications" /usr/share/applications
rg '^(Name|Exec|Icon|Terminal|NoDisplay|Categories)=' /confirmed/launcher.desktop
```

Use `Exec=` and the live process command line to choose the launcher. Do not
confuse the graphical IDE, XSCT, Tcl shells, uninstallers, or another release
with these two entries.

Inspect recent launch evidence in the real user session:

```bash
journalctl --user -b --since '15 minutes ago' --no-pager |
  rg -i 'Vitis Commandline Tool|Vitis Python Shell|Model Composer|MATLAB|fatal|error'
pgrep -af 'model_composer|MATLAB|Vitis/bin/vitis|vitis_pytool'
```

## Repair Vitis Commandline Tool

This mode applies when the log proves that `vitis -i` starts, prints
`Welcome to Vitis Python Shell`, immediately reads EOF, asks whether to exit,
and terminates. The application is healthy; it was launched without a usable
terminal.

First compare a known-working terminal application such as btop++ rather than
guessing terminal-emulator flags:

```bash
rg '^(Name|Exec|Terminal|Categories)=' /usr/share/applications/btop.desktop
gsettings get org.gnome.desktop.default-applications.terminal exec
gsettings get org.gnome.desktop.default-applications.terminal exec-arg
```

Prefer the standard desktop contract:

```ini
[Desktop Entry]
Type=Application
Version=1.0
Name=Vitis Commandline Tool <installed-version>
Comment=Vitis Python interactive shell
Icon=<preserved-vendor-icon>
Exec=<confirmed-absolute-vitis-path> -i
Terminal=true
Categories=Development;ConsoleOnly;
```

If adding `Terminal=true` to the existing vendor-generated launcher still
produces the same immediate-EOF journal trace, verify whether GNOME is using a
stale cached desktop object. Create a user launcher with a new, simple basename
such as `vitis-commandline-tool-<version>.desktop`, keep the old launcher with
`NoDisplay=true`, and refresh the database. A new desktop ID is the repair for
the stale object; repeatedly changing `Exec=` on the cached ID is not.

If GNOME's Xilinx app folder stores an explicit list of desktop IDs, read its
current value and replace only the old Vitis CLI ID with the new one in the
same position:

```bash
gsettings get org.gnome.desktop.app-folders folder-children
gsettings list-recursively \
  org.gnome.desktop.app-folders.folder:/org/gnome/desktop/app-folders/folders/<folder-id>/
```

Preserve the complete original list as rollback information before using
`gsettings set`. Never reconstruct or reorder unrelated entries from memory.
After the change, have the user close the application overview completely and
reopen it. A logout is a last resort for a genuinely stale GNOME Shell cache;
a computer restart is unnecessary.

Successful verification is an opened terminal that remains at a prompt like:

```text
Welcome to Vitis Python Shell
Vitis [1]:
```

`exit()` or `Ctrl+D` should close it normally.

## Repair Vitis Model Composer

This mode applies when the log shows the Model Composer banner and MATLAB
startup banner, and `pgrep` shows persistent MATLAB children, but no MATLAB
window appears. On affected MATLAB R2025b GNOME hosts, starting Model Composer
without a controlling terminal leaves MATLAB alive in the background.

Create a user-owned wrapper under `~/.local/libexec/` that gives the launcher
a private PTY without showing a terminal window. Substitute the executable
path measured from the current launcher:

```bash
#!/usr/bin/env bash

set -e

model_composer=/confirmed/path/to/model_composer

if [[ ! -x "$model_composer" ]]; then
    printf 'model-composer-desktop: executable not found: %s\n' "$model_composer" >&2
    exit 1
fi

printf -v model_command 'exec %q' "$model_composer"
exec /usr/bin/script --quiet --flush --return \
    --command "$model_command" /dev/null
```

Make the wrapper executable and change only the confirmed user launcher's
`Exec=` to its absolute path. Preserve the vendor `Icon=` and other unrelated
fields. Do not use `Terminal=true` for this mode: the PTY is an implementation
detail and Model Composer should still present MATLAB, not a terminal window.

The observable success condition is a visible MATLAB window whose command
area prints the Model Composer links and reaches the MATLAB prompt:

```text
Vitis Model Composer: User Guide Examples and Tutorials
>>
```

That message is normal and proves `xmcStart` ran. If MATLAB later reports a
fatal allocator error, handle it as a separate MATLAB compatibility issue
rather than changing the PTY repair blindly.

## Validate and refresh

For every changed launcher or wrapper:

```bash
bash -n "$HOME/.local/libexec/<wrapper>"        # when a wrapper was created
test -x "$HOME/.local/libexec/<wrapper>"
desktop-file-validate "$HOME/.local/share/applications/<launcher>.desktop"
update-desktop-database "$HOME/.local/share/applications"
rg '^(Name|Exec|Icon|Terminal|NoDisplay|Categories)=' \
  "$HOME/.local/share/applications/<launcher>.desktop"
```

Vendor warnings about deprecated `Encoding=` or a redundant `Comment=` are
not validation errors and do not justify unrelated rewrites. Verify the actual
menu click and journal behavior; static file checks alone are insufficient.
