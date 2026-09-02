---
name: gnome-xwayland-dock-icon-fix
description: >-
  Diagnose and fix GNOME Wayland/XWayland applications whose menu icon is
  correct but whose running window shows a generic icon, creates a second Dock
  item, or groups under the wrong launcher. Use for launcher-to-window matching
  failures across AppImage, Java/Tk, EDA, and other XWayland applications when
  no more specific app skill applies; do not use for missing menu entries,
  launch failures, or native Wayland app-id problems.
---

# GNOME XWayland Dock icon matching

Fix the launcher-to-window identity mismatch, not the icon artwork. A correct
application-menu icon proves that `Icon=` resolves; GNOME still needs the
running XWayland main window to match the intended `.desktop` entry.

## Safety and scope

- Keep diagnosis read-only until the user authorizes a fix.
- Prefer a confirmed launcher under `~/.local/share/applications/`. Never edit
  `/usr/share/applications/` or vendor installation files for this repair.
- If only a system launcher exists, create a user-local override of that exact
  launcher after authorization; preserve its original basename and fields.
- Do not infer `StartupWMClass` from an executable, desktop filename, window
  title, icon name, helper process, or a previous application version.
- Do not force-quit a running application. Existing windows may contain
  unsaved state and normally must be closed and reopened before regrouping.
- Do not recommend `Alt+F2` then `r` in a GNOME Wayland session.

This skill is for XWayland windows that expose `WM_CLASS`. If the mapped main
window is native Wayland and has no X11 window properties, stop and diagnose
its compositor app-id instead of inventing a `StartupWMClass` value.

## Establish the symptom and environment

Confirm all of the following before editing:

- the application is visible in GNOME's menu with the intended icon;
- its running window uses a generic icon, creates a second Dock item, or groups
  with the wrong launcher; and
- the session and required diagnostic tools are known.

```bash
printf 'session=%s desktop=%s display=%s\n' \
  "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP" "$DISPLAY"
command -v xprop desktop-file-edit desktop-file-validate \
  update-desktop-database
```

On Arch/CachyOS, `xprop` is normally provided by `xorg-xprop`, while the three
desktop-file commands come from `desktop-file-utils`. Report missing packages;
do not install them without authorization.

Desktop and process inspection must run in the user's real desktop session.
If the user visibly has the application open but a sandboxed `ps` or `xprop`
returns nothing, repeat the read-only checks in the host desktop context. Do
not report that the application is closed merely because the sandbox cannot
see the host PID or XWayland client list.

## Identify the exact launcher

Search user and system application directories using the application's current
name and executable, then read each candidate's identity fields:

```bash
find "$HOME/.local/share/applications" /usr/share/applications \
  -maxdepth 2 -type f -name '*.desktop' -print

grep -E '^(Name|Exec|TryExec|Icon|NoDisplay|StartupWMClass)=' \
  /path/to/candidate.desktop
```

Use `Exec=` and `TryExec=` plus the live process command line to select the
launcher that actually starts the visible application. Hidden URI handlers,
updaters, Tcl shells, old AppImage integration entries, and launchers from a
previous version are not interchangeable with the visible main launcher.

If multiple candidates cannot be distinguished safely, stop and ask the user
which menu entry they use. Do not modify every candidate.

## Measure the main window's real class

Wait until the full main window is mapped, then enumerate XWayland clients:

```bash
for window_id in $(
  xprop -root _NET_CLIENT_LIST 2>/dev/null | grep -oE '0x[0-9a-f]+'
); do
  printf 'WINDOW=%s ' "$window_id"
  xprop -id "$window_id" \
    _NET_WM_PID WM_CLASS _NET_WM_NAME 2>/dev/null | tr '\n' ' '
  printf '\n'
done
```

Relate `_NET_WM_PID` and `_NET_WM_NAME` to the selected launcher and process.
For the confirmed main window, `WM_CLASS` normally contains two strings:

```text
WM_CLASS(STRING) = "instance", "class"
```

Use the second string, the class, as `StartupWMClass`. Measure dialogs and
splash screens only to distinguish them; do not let a transient helper window
override the fully mapped main window.

Examples observed during validated repairs are evidence of the method, not
values to reuse:

| Application/version | Measured main-window `WM_CLASS` | Class used |
| --- | --- | --- |
| WeChat 4.1.1 AppImage | `"wechat", "wechat"` | `wechat` |
| MATLAB R2025b Update 6 | `"Matlab-GLEE", "MATLAB R2025b Update 6"` | `MATLAB R2025b Update 6` |
| Vivado 2025.2.1 | `"Vivado", "Vivado"` | `Vivado` |

Remeasure after reinstalling or updating an application because launchers and
window classes can change.

## Repair the user launcher

Capture the launcher's current `Exec=`, `TryExec=`, and `Icon=` values so they
can be compared after the edit. Set only the measured class on the confirmed
user launcher:

```bash
desktop_file="$HOME/.local/share/applications/current-app.desktop"
measured_class='value from the second WM_CLASS string'

desktop-file-edit \
  --set-key=StartupWMClass \
  --set-value="$measured_class" \
  "$desktop_file"
desktop-file-validate "$desktop_file"
update-desktop-database "$HOME/.local/share/applications"
```

Validation warnings about deprecated vendor-generated fields can be reported
without rewriting unrelated keys. Treat actual validation errors as a failed
repair. Ensure only the intended visible launcher claims the measured class.

## Verify observable behavior

Static checks are necessary but not sufficient:

```bash
grep -E '^(Name|Exec|TryExec|Icon|StartupWMClass)=' "$desktop_file"
desktop-file-validate "$desktop_file"
```

Ask the user to save work, close the application normally, and reopen it from
the repaired menu entry. No desktop or computer restart should be required.
Confirm that:

- the running window uses the launcher's intended icon;
- it joins the expected Dock item instead of creating a generic second item;
- `Exec=`, `TryExec=`, and `Icon=` remain unchanged; and
- the application still launches normally.

If the wrong pinned item remains, distinguish stale GNOME pinning from window
matching: unpin the obsolete generic item and pin the correctly matched
launcher only after the new window is verified. If the problem persists,
remeasure the reopened main window and recheck that the edited launcher is the
one actually used; do not escalate to icon-theme replacement or vendor-file
changes without new evidence.
