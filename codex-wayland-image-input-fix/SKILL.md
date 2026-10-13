---
name: codex-wayland-image-input-fix
description: Diagnose and repair Codex or ChatGPT Desktop on Linux Wayland when dragging image files into the composer does nothing while file-manager copy and paste works. Includes native Wayland startup validation, user-level launch persistence, and the separate GNOME Loupe clipboard lifetime issue. Use for these image-input symptoms, not general attachment, authentication, or network failures.
---

# Codex Wayland image input repair

Separate file drag-and-drop from clipboard copying. On the validated GNOME case, switching Codex from XWayland to native Wayland restored dragging; keeping Loupe open until pasting resolved copying. Do not assume either observation applies to every Linux desktop or client version.

## Diagnose without changing the session

Identify the real executable, package/build, desktop session, menu launcher, user wrapper, and active rendering backend. The product may say Codex while its package, executable, and desktop entry use ChatGPT names.

Useful read-only checks (adapt names to the installed layout):

~~~bash
printf '%s\n' "$XDG_SESSION_TYPE"
pacman -Q chatgpt-desktop-bin loupe wl-clipboard xclip
ps -C ChatGPT -o pid=,ppid=,args=
xdg-mime query default image/png
rg -n '^Exec=' ~/.local/share/applications/chatgpt.desktop /usr/share/applications/chatgpt.desktop
~~~

- A Wayland desktop does not prove Codex uses Wayland. Inspect the GPU/renderer process for `--ozone-platform=x11` or `--ozone-platform=wayland`.
- Restricted tool processes may not see the desktop PID namespace or Wayland socket. Use permitted host access; a sandbox failure is not evidence of a broken desktop.
- Do not dump whole process environments, clipboard contents, account data, or signed asset URLs. Read clipboard MIME types only.
- Ask whether dragging comes from the file manager or the viewer, whether dropping does nothing or inserts a path, and whether copying happens before the viewer is closed.
- Inspect the actual wrapper before choosing a flags file. Preserve unrelated launcher fixes, arguments, and version-gated preload behavior. Do not force an old preload onto a new binary.

## Distinguish clipboard lifetime from Codex failures

After the user copies in the viewer, keep it open while checking:

~~~bash
wl-paste --list-types
timeout 4 xclip -selection clipboard -o -t TARGETS
~~~

Use `xclip` only for the XWayland side and only if installed. Missing diagnostic tools do not justify installing packages without authorization.

In the validated Loupe 51 case, its live clipboard offered file-transfer formats such as `application/vnd.portal.filetransfer`, `application/vnd.portal.files`, and `text/uri-list`; Codex successfully attached the image. After Loupe exited, only text remained and pasting produced a path.

**Absence of `image/png` alone is not a failure:** a live file-transfer payload can attach an image. Compare viewer-open versus viewer-closed states and the actual paste outcome.

For this confirmed lifetime issue, tell the user to copy, paste into Codex, then close Loupe. File-manager Ctrl+C followed by Codex Ctrl+V was also verified. Do not change system clipboard configuration for this finding.

## Validate native Wayland before restarting

If file-manager dragging does nothing and the client actually uses XWayland, test native Wayland as a targeted workaround. Holding Shift did not fix the validated case; do not present it as a guaranteed desktop remedy.

Read [references/launch-and-case.md](references/launch-and-case.md) before launching a test or arranging any restart. It provides a tested environment source, isolated profile layout, socket-path constraint, and the recorded evidence.

- Use a separate temporary profile for the initial startup test; do not close the original client to discover whether Wayland can start.
- Obtain desktop variables from the logged-in session or verified user service environment. In the recorded client, `/proc/MAIN_PID/environ` omitted even HOME and the display variables.
- Keep every temporary profile, log, helper, and runtime temporary directory under the task's original workspace `tmp/`. Check the Chromium singleton socket path length before launch.
- A successful launch is only a startup test. Require actual dragging in the user's normal client before declaring the workaround effective.
- Explain that restarting closes the current window, and honor authorization already given. Signal only the verified main PID, gracefully.
- If an automatic restart fails, inspect the log before retrying. Correct the failed prerequisite and preflight it separately; do not loop over unverified restarts or promise fallback recovery before checking its environment.

## Persist only the verified workaround

After native Wayland and user drag-and-drop both succeed, inspect which configuration the normal menu launcher actually reads.

In the validated user wrapper, `~/.local/bin/chatgpt` reads `~/.config/chatgpt-flags.conf`, one argument per non-comment line. Add:

~~~text
--ozone-platform=wayland
~~~

Use that path only after verifying the wrapper supports it. Preserve all other flags. Back up an existing file to the task's `tmp/` before editing; if a backend flag conflicts, replace only that flag. If there is no supported flags file, use a reversible user-level launcher adjustment after inspecting its existing behavior; do not edit package files.

Verify the file contents and menu `Exec=` chain. On the next authorized normal menu launch, verify the active backend and dragging again. Saving a flag alone does not prove that a future menu launch has been tested.

## Rollback and scope

Remove only the Wayland flag introduced by this repair, or restore the backed-up configuration when it contains no subsequent user edits. An authorized restart is needed to change the active backend. Do not delete the entire flags file if it now has other settings.

No cache clearing, reinstall, system-wide environment changes, new clipboard manager, or unrelated signal-handler changes are required for the validated fix. Report user-confirmed behavior separately from process/log evidence.

Dependencies: installed Linux client; procps and Python 3 for diagnosis/test startup; systemd user environment on the validated GNOME system; wl-clipboard and optionally xclip for MIME inspection. No additional Python packages are needed.
