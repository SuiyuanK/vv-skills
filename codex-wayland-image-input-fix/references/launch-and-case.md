# Launch procedure and validated case

## Desktop environment and temporary paths

Use the original task workspace as WORKSPACE even if later commands change directory. The snippets below assume Python 3 and an existing systemd user desktop session. They create only task-owned files beneath WORKSPACE/tmp.

Before launching:
- Verify HOME, XDG_RUNTIME_DIR, WAYLAND_DISPLAY, DISPLAY (for X11 fallback), and DBUS_SESSION_BUS_ADDRESS from the real desktop session.
- Confirm the Wayland socket exists and is accessible. A socket existing is a prerequisite, not proof that the client can initialize.
- Do not source `systemctl --user show-environment` with shell eval, print its full contents, or serialize secrets into helper arguments/logs.
- Preserve any required, verified version-specific launcher behavior; the isolated example uses the direct executable and is unsuitable if bypassing the wrapper drops a required fix.

Chromium creates a singleton socket like:

~~~text
TMPDIR/org.chromium.Chromium.XXXXXX/SingletonSocket
~~~

Linux AF_UNIX pathnames must fit within 107 bytes plus the terminator. Measure the full path in bytes, leaving room for the generated suffix. Use the workspace's direct `tmp/` as TMPDIR if nested task folders make it too long. Keep profiles and logs in their own unique subdirectory. If even this cannot fit, stop the launch and explain the constraint; do not use system /tmp or an external short-path workaround without user direction.

## Independent startup preflight

Adapt the executable after checking the installation. Export WORKSPACE to the original task root and TMPDIR to its existing/created tmp directory before invoking a shell heredoc, so shell intermediates also stay there.

~~~bash
export WORKSPACE="/absolute/original/workspace"
mkdir -p "$WORKSPACE/tmp"
export TMPDIR="$WORKSPACE/tmp"
python3 - <<'PY'
import os
import shlex
import subprocess
import tempfile
import time
from pathlib import Path

root = Path(os.environ["WORKSPACE"]).resolve() / "tmp"
binary = Path("/usr/lib/chatgpt/ChatGPT")  # replace after discovery
assert binary.is_file()
candidate = root / "org.chromium.Chromium.XXXXXX" / "SingletonSocket"
assert len(os.fsencode(candidate)) < 108, "Chromium singleton socket path too long"

raw = subprocess.check_output(
    ["systemctl", "--user", "show-environment"], text=True
)
env = {}
for line in raw.splitlines():
    fields = shlex.split(line)
    if len(fields) == 1 and "=" in fields[0]:
        key, value = fields[0].split("=", 1)
        env[key] = value

required = ("HOME", "DISPLAY", "WAYLAND_DISPLAY",
            "XDG_RUNTIME_DIR", "DBUS_SESSION_BUS_ADDRESS")
assert all(env.get(key) for key in required), "Incomplete desktop environment"
display = Path(env["WAYLAND_DISPLAY"])
socket = display if display.is_absolute() else Path(env["XDG_RUNTIME_DIR"]) / display
assert socket.is_socket(), "Wayland socket unavailable"

case = Path(tempfile.mkdtemp(prefix="", dir=root))
env.update(
    TMPDIR=str(root), TMP=str(root), TEMP=str(root),
    CODEX_ELECTRON_USER_DATA_PATH=str(case / "profile"),
    CODEX_HOME=str(case / "codex"),
)
with (case / "startup.log").open("ab", buffering=0) as log:
    process = subprocess.Popen(
        [str(binary), "--ozone-platform=wayland",
         "--user-data-dir=" + str(case / "profile")],
        env=env, cwd=env["HOME"], stdin=subprocess.DEVNULL,
        stdout=log, stderr=log, start_new_session=True,
    )
time.sleep(5)
print("Test PID:", process.pid, "exit status:", process.poll())
print("Test directory:", case)
PY
~~~

The installed build was inspected to confirm `CODEX_ELECTRON_USER_DATA_PATH` controls its profile; recheck this on a different build. An isolated profile may show sign-in and does not validate the user's actual account/session. Do not copy account tokens into the test profile or require a new login just for this startup check.

Require the test process to remain alive and its GPU/renderer to show `--ozone-platform=wayland`. Close only the test instance when finished. A successful spawn or five-second poll alone is insufficient.

For the normal-session restart, obtain the same verified desktop environment, omit both isolation variables and the temporary `--user-data-dir`, retain the original user profile, and supply `--ozone-platform=wayland`. Keep TMPDIR at the short workspace tmp path. A deferred helper must survive the original application's exit and log to workspace tmp. Validate its environment and any fallback launch before terminating the original client. Never reuse a recorded PID without identifying it again.

Alternatively, once the user exits Codex, have them launch the verified executable/compatible wrapper from a terminal belonging to the desktop session with the Wayland flag and short TMPDIR. Do not close the current session merely to record or validate this skill.

## Case evidence: 2026-10-13

Validated on CachyOS, GNOME Wayland:
- `chatgpt-desktop-bin 26.1007.21434-1`; executable `/usr/lib/chatgpt/ChatGPT`.
- `loupe 51.0-1.1`, `wl-clipboard 1:2.3.0-1.1`, `xclip 0.13-6.1`.
- Before: file-manager Ctrl+C/paste attached images; file-manager dragging into Codex did nothing, including with Shift. GPU/renderer used `--ozone-platform=x11`.
- Loupe copying: keeping the viewer open allowed attachment; exiting before paste left only a text path. Live clipboard advertised portal file-transfer formats and URI list, not necessarily PNG.
- First automatic restart: excessively nested TMPDIR caused `FATAL ... Socket path too long`. Native launch and X11 fallback both failed.
- Second attempt: copying the main process environment from /proc omitted display, HOME, runtime and bus variables. Wayland reported invalid XDG_RUNTIME_DIR and could not initialize; fallback reported missing DISPLAY. This was a faulty restart helper, not a proven client Wayland failure.
- Corrected preflight: a short TMPDIR and desktop user-service environment launched an independent Wayland profile successfully. GPU process confirmed the backend.
- Corrected normal launch: the real client ran with `--ozone-platform=wayland`, and the user confirmed dragging worked.
- Persistence: the already installed user wrapper read `~/.config/chatgpt-flags.conf`; the Wayland flag was saved there and the launcher chain checked. A subsequent menu launch was not tested in this session.

These are observed compatibility results for this setup, not a claim that every XWayland client has broken dragging or that native Wayland fixes viewer-close clipboard retention.

## Supporting references

- [OpenAI image inputs](https://learn.chatgpt.com/docs/image-inputs): general image attachment guidance; Shift dragging did not resolve this local case.
- [Loupe copy implementation](https://gnome.pages.gitlab.gnome.org/loupe/doc/src/loupe/widgets/image_view.rs.html): copy sets the current page content provider on the clipboard.
