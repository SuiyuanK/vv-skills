---
name: matlab-cachyos-fix
description: >-
  Diagnose and fix MATLAB R2025b on x86_64 CachyOS/Arch Linux, including
  installer lc_init/GnuTLS/leancrypto SIGSEGV, download or extraction failures,
  GCC 13 AUR bootstrap failures after Linux removed linux/scc.h, and a
  MATLAB-only GCC 13 wrapper for MEX that leaves the system GCC unchanged,
  plus GNOME menu/Dock integration, external-browser launch failures caused by
  allocator inheritance, and glibc smallbin corruption on shutdown. Use for
  these specific MATLAB installer, MEX compiler, launcher, icon, browser, or
  teardown symptoms on an Arch-family host; rediscover paths and versions
  before applying fixes.
---

# MATLAB R2025b on CachyOS / Arch

This skill covers three independent failure domains:

1. the MathWorks installer crashes or fails while downloading/extracting; and
2. MATLAB is installed, but R2025b needs a supported GCC for MEX while the
   rolling system compiler is newer; and
3. MATLAB works from a terminal, but GNOME menu launch, Dock icon matching,
   external-browser handoff, or shutdown fails on a newer glibc.

Identify the phase before changing anything. Do not apply the installer
workaround to a compiler problem, or rebuild GCC to explain an incomplete
MATLAB download.

## Scope and invariants

- Verified platform: x86_64 CachyOS/Arch, glibc 2.44, MATLAB R2025b, Linux 7.x.
- Rediscover the installer directory, MATLAB real executable, Linux API header
  package, current GCC, AUR PKGBUILD revision, chroot name, and desktop entry.
  Paths in the references are examples from one verified host.
- Never downgrade or replace system GnuTLS/glibc to make the installer run.
- Never replace `/usr/bin/gcc`, use `update-alternatives` globally, or put a
  generic `gcc` shim in a directory that affects unrelated EDA tools.
- Do not bypass GCC's stage2/stage3 bootstrap comparison. A compiler that fails
  the comparison is not suitable for MATLAB/MEX.
- Prefer user-local wrappers and desktop overrides. Obtain authorization before
  package installation, `/etc` edits, chroot creation, or vendor-tree changes.
- Put temporary logs, chroots, downloads, and intermediate output under the
  calling workspace's `./tmp/` when the tool permits it. Do not delete failed
  installer or compiler build trees until the result is verified.

## Route by symptom

### Installer SIGSEGV, extraction error, or timeout

Read [references/installer.md](references/installer.md). Confirm the crash stack
or download log before using `LD_PRELOAD` or retrying.

### GCC 13 installation, bootstrap failure, MEX, or persistent launcher

Read [references/gcc13-mex.md](references/gcc13-mex.md). This includes the
`linux/scc.h` compatibility patch at
[`assets/libsanitizer-linux-scc.patch`](assets/libsanitizer-linux-scc.patch),
clean-chroot and incremental-resume paths, split-package installation, and the
MATLAB-only wrapper.

### GNOME menu, Dock icon, external browser, or shutdown fails

Read [references/desktop-glibc.md](references/desktop-glibc.md). Keep menu
launch, window matching, and allocator diagnosis separate: each has a
different runtime identity and verification method.

## Completion criteria

Do not report success from package presence or exit code alone. Verify the
relevant outcome:

- Installation: the target contains an executable `bin/matlab` and valid
  version metadata, then MATLAB starts successfully.
- Compiler: the system shell still reports the intended rolling GCC, while a
  MATLAB batch launched through the wrapper reports GCC, G++, and optionally
  GFortran 13.
- MEX: configure C/C++ deliberately and compile and execute a small real MEX
  module; do not stop at `mex -setup` output.
- Desktop launch: the user-local desktop entry reaches the same wrapper used by
  the shell, opens a real GUI from GNOME, and validates without errors.
- Dock icon: use `$gnome-xwayland-dock-icon-fix` for the shared `WM_CLASS` and
  launcher workflow, plus the MATLAB-specific exceptions in the desktop
  reference; then close and reopen MATLAB to verify the official icon.
- Shutdown: after any allocator workaround, prove the alternate allocator is
  loaded inside MATLAB, then close a real GUI and confirm no smallbin error,
  crash dump, or orphaned backend remains.
- External browser: keep the alternate allocator inside MATLAB while proving
  the browser child does not inherit it; require a real account-link click and
  no new browser coredump, because `web(...,'-browser')` status 0 alone is not
  sufficient.
- Health: for a broader request, use isolated `TMPDIR` and `MATLAB_PREFDIR` and
  test numeric work, headless graphics, Simulink loading, and compiler state.

Record exact versions, paths, commands, exit codes, and remaining warnings.
Distinguish verified results from recommended next steps.
