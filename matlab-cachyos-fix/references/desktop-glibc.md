# MATLAB R2025b GNOME launcher, browser handoff, Dock icon, and glibc teardown

Use this reference when terminal launch works but GNOME menu launch does not,
the running MATLAB window has a generic blue icon, an account link does not
open the browser, or closing MATLAB prints `free(): chunks in smallbin
corrupted` / `malloc(): smallbin double linked list corrupted`.

Treat these as separate problems. A working menu does not prove window-icon
matching, and a correct icon does not prove clean shutdown.

## 1. Rediscover the current runtime

Do not copy paths or class names from an earlier MATLAB update. Check the
session, wrapper, real executable, generated ServiceHost entries, and tools:

```bash
printf 'session=%s desktop=%s display=%s\n' \
  "$XDG_SESSION_TYPE" "$XDG_CURRENT_DESKTOP" "$DISPLAY"
command -v matlab script xprop desktop-file-validate update-desktop-database
readlink -f "$(command -v matlab)"
ldd --version | head -1
pacman -Q gperftools 2>/dev/null || true
find "$HOME/.local/share/applications" -maxdepth 1 -type f \
  -iname '*matlab*.desktop' -print
```

Read every candidate's `Name`, `Exec`, `Icon`, `NoDisplay`, and
`StartupWMClass`. MathWorks ServiceHost can generate hidden URI handlers such
as `mw-matlab.desktop`; do not assume that file is the user's visible launcher.
Match the visible launcher to its real `Exec=` and wrapper.

Dependencies used by the verified workflow:

- `script` from util-linux for a private pseudo-terminal;
- `xprop` from xorg-xprop for the mapped XWayland window class;
- desktop-file-utils for validation and cache refresh; and
- optional `libtcmalloc_minimal.so` from gperftools for the allocator
  workaround.

Do not install missing packages or modify launchers without authorization.

## 2. GNOME menu launch when terminal launch works

First establish the distinction:

- `matlab` from an interactive terminal opens the full GUI; and
- the desktop entry either does nothing or creates a process that exits without
  a window.

MathWorks documents `-desktop` for launch without a controlling terminal, so
test it first. On the verified CachyOS host, `-desktop` still exited silently,
while a real terminal worked. A user-local pseudo-terminal helper fixed only
the menu path without changing command-line or script behavior.

Verify the mechanism before using it:

```bash
script -qefc 'test -t 0 && printf PTY_OK' /dev/null
```

Example helper, with paths rediscovered for the current user:

```bash
#!/usr/bin/env bash
set -e

matlab_wrapper="$HOME/.local/bin/matlab"
[[ -x "$matlab_wrapper" ]] || exit 1

exec /usr/bin/script --quiet --flush --return \
  --command "exec $matlab_wrapper" /dev/null
```

Put the helper under a user-local executable directory such as
`~/.local/libexec/`, and point only the visible desktop entry's `Exec=` to it.
The helper must call the same MATLAB-only GCC wrapper as the shell. Do not set
`Terminal=true` or hard-code a particular terminal emulator when a private PTY
is sufficient.

Validate the helper with `bash -n`, validate the desktop file, refresh the user
desktop database, and perform a real menu click. Process presence alone is not
success; require a visible usable MATLAB window.

## 3. glibc smallbin corruption during GUI shutdown

The verified R2025b Update 6 host used glibc 2.44. Closing the GUI intermittently
printed:

```text
free(): chunks in smallbin corrupted
malloc(): smallbin double linked list corrupted
MATLAB is exiting because of fatal error
```

Crash dumps reached MathWorks teardown code such as
`libmwsearch_path_impl.so`, file-provider code, and Agent/ServiceHost
serialization or transport code before glibc aborted. Similar R2025b/R2026a
GUI-shutdown failures have been reported with glibc 2.43:

- <https://www.mathworks.com/matlabcentral/discussions/general/887876-matlab-crash-on-ubuntu-26-04-free-chunks-in-smallbin-corrupted/2624589>

Before changing the allocator:

1. inspect the newest `matlab_crash_dump.*` stack;
2. inspect live process environments for `LD_PRELOAD`, `MATLABPATH`, and EDA
   variables;
3. inspect `/proc/PID/maps` for the actual libc, libstdc++, and libgcc; and
4. distinguish a repeatable MathWorks teardown signature from unrelated MEX or
   third-party binary corruption.

On the verified host, MATLAB loaded its own `libstdc++.so.6.0.30` and
`libgcc_s.so.1` plus system glibc 2.44; ordinary instances did not load
Synopsys/Vivado C++ runtimes. One Codex-launched diagnostic instance inherited
a Vivado `MATLABPATH`, demonstrating why the real terminal/login environment
must be inspected, but clean instances still reproduced the shutdown failure.

### Optional MATLAB-only tcmalloc workaround

This is a community workaround, not a MathWorks-supported fix. Explain that it
replaces MATLAB's allocator and obtain authorization before enabling it. Never
set `LD_PRELOAD` globally, in shell startup files, or for unrelated EDA tools.

When gperftools is already installed and the real library resolves, add it only
at the final MATLAB exec in the existing wrapper:

```bash
tcmalloc_lib=/usr/lib/libtcmalloc_minimal.so.4
[[ -r "$tcmalloc_lib" ]] || exit 1

if [[ -n "${LD_PRELOAD:-}" ]]; then
    matlab_preload="$tcmalloc_lib:$LD_PRELOAD"
else
    matlab_preload="$tcmalloc_lib"
fi

exec env LD_PRELOAD="$matlab_preload" "$matlab_bin" "$@"
```

Keep a reversible copy of the previous wrapper. First use isolated `TMPDIR`
and `MATLAB_PREFDIR` directories under the calling workspace and prove the
allocator is loaded from inside MATLAB:

```matlab
maps = fileread('/proc/self/maps');
assert(contains(maps,'libtcmalloc_minimal.so'));
disp('TCMALLOC_LOADED_OK');
```

Require batch exit code 0, then test a real GUI close. Check that no new crash
dump appears and that the session backend exits. Do not terminate stale MATLAB
backends without explicit authorization because inaccessible sessions can
still contain unsaved state.

## 4. Account or help link does not open the external browser

First verify the system handlers instead of assuming MIME ownership is broken:

```bash
xdg-settings get default-web-browser
xdg-mime query default x-scheme-handler/http
xdg-mime query default x-scheme-handler/https
gio mime x-scheme-handler/https
```

Then reproduce through MATLAB itself with an isolated `TMPDIR` and
`MATLAB_PREFDIR`. Print both the allocator and resolved opener before calling
`web`:

```matlab
fprintf('LD_PRELOAD=%s\n',getenv('LD_PRELOAD'));
system('command -v xdg-open');
status = web('https://www.mathworks.com/','-browser');
fprintf('WEB_STATUS=%d\n',status);
```

Do not accept `WEB_STATUS=0` as proof that a browser survived. On the verified
host, MATLAB returned 0 while systemd-coredump recorded a new Chrome process
dumping core with its top frames in `libtcmalloc_minimal.so.4`. MATLAB's
process-local `LD_PRELOAD` had propagated through `xdg-open` into Chrome.

Keep tcmalloc loaded in MATLAB to preserve the teardown workaround, but strip
it at the external-browser boundary. Install an `xdg-open` shim only inside the
MATLAB wrapper's private PATH directory, alongside its GCC shims:

```bash
#!/usr/bin/env bash

unset LD_PRELOAD
exec /usr/bin/xdg-open "$@"
```

Make the shim executable and have the MATLAB wrapper prepend that private
directory before launching MATLAB. Use an absolute `/usr/bin/xdg-open` in the
shim to avoid recursion. Do not replace the system `xdg-open`, globally unset
`LD_PRELOAD`, or force a browser with a global `BROWSER` variable. Keep a
reversible copy of the wrapper before editing it.

Fully exit and reopen MATLAB because an existing process retains its old PATH.
Repeat the isolated test and require all of the following:

- MATLAB still reports the intended `libtcmalloc_minimal.so` preload;
- `command -v xdg-open` inside MATLAB resolves to the private shim;
- the requested page visibly opens in the user's configured browser;
- no newer browser coredump appears; and
- the real account/help link opens successfully after a GUI restart.

The verified post-fix test kept tcmalloc inside MATLAB, resolved `xdg-open` to
the private shim, returned `WEB_STATUS=0`, and produced no new Chrome coredump.

## 5. Generic blue icon after MATLAB opens

Use `$gnome-xwayland-dock-icon-fix` for the shared launcher discovery,
host-session `xprop` measurement, user-level `StartupWMClass` edit, database
refresh, and close/reopen verification. Keep only these MATLAB-specific facts
in this workflow:

Do not infer `StartupWMClass` from:

- the visible title (`MATLAB R2025b`);
- the helper executable (`MATLABWindow`);
- ServiceHost's `--application-id`; or
- the generated hidden `mw-matlab.desktop` URI handler.

Those guesses were tested and did not fix the running icon. Adding the official
PNG to MathWorks' hidden `mw-matlab.desktop` URI handler also did not fix
grouping. Match the visible launcher that calls the PTY helper and MATLAB-only
wrapper.

Wait until the full main window is mapped. The verified R2025b Update 6 main
window reported:

```text
WM_CLASS(STRING) = "Matlab-GLEE", "MATLAB R2025b Update 6"
```

Use the second string as the class. Preserve the working `Exec=` and official
`Icon=` while setting the visible launcher's measured value:

```ini
Icon=/current/MATLAB/bin/glnxa64/cef_resources/matlab_icon.png
StartupWMClass=MATLAB R2025b Update 6
```

Do not hard-code this value for another update: the class contains the update
number. After applying the generic workflow, also verify that menu launch still
uses the PTY helper and MATLAB-only GCC wrapper.
