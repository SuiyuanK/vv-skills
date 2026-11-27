---
name: chatgpt-arch-deb-updater
description: Build or update OpenAI's official ChatGPT/Codex Desktop Linux amd64 deb as a clean Arch Linux or CachyOS package with explicit dependencies and makepkg. Use when the AUR or distribution package lags the official release, when installing a local official chatgpt_amd64.deb, or when debtap produces invalid dependencies, ownership, or package metadata.
---

# ChatGPT Arch Deb Updater

Use the bundled builder instead of debtap. It validates the official Debian package, maps Debian runtime dependencies to Arch packages explicitly, and delegates `.PKGINFO`, `.BUILDINFO`, `.MTREE`, ownership, and compression to `makepkg` under fakeroot.

## Scope and safety

- Support Arch Linux or CachyOS on x86_64 and only an official `chatgpt` `amd64` Debian package.
- Run the builder as the ordinary user. Never run `makepkg` or the builder with `sudo`.
- Keep all downloads, build trees, logs, and generated packages under the task workspace root's `./tmp/`. Set `CHATGPT_ARCH_WORKSPACE` when the shell working directory is not that root.
- Do not install, patch, update, or repair debtap. Do not hand-edit or retain stale `.PKGINFO`, `.INSTALL`, or `.MTREE` files.
- Do not install optional dependencies automatically. `pipewire-pulse` and `pulseaudio` are alternative audio servers; do not install both.
- Building does not authorize system installation. Run `yay -U` only when the user asked to install/update the application or approves the exact generated package.
- Do not stop or restart ChatGPT/Codex automatically. Tell the user that a running process continues using the old executable until the app is restarted.

## Preflight

Confirm the platform and current package state:

```bash
uname -m
pacman -Q chatgpt 2>/dev/null || true
pacman -Qdt 2>/dev/null || true
```

The builder requires `bash`, `curl` for automatic download, `bsdtar` from `libarchive`, `makepkg` and `vercmp` from `pacman`, `gzip`, `gawk`, `grep`, `findutils`, and core GNU utilities. Explain missing dependencies and obtain confirmation before installing anything.

## Build

From the user's workspace root, build the latest release listed in the official HTTPS repository index:

```bash
CHATGPT_ARCH_WORKSPACE="$PWD" \
  /home/vv/.cc-switch/skills/chatgpt-arch-deb-updater/scripts/auto-deb-install.sh
```

Or build a user-supplied official deb:

```bash
CHATGPT_ARCH_WORKSPACE="$PWD" \
  /home/vv/.cc-switch/skills/chatgpt-arch-deb-updater/scripts/auto-deb-install.sh /absolute/path/chatgpt_amd64.deb
```

If the canonical skill directory differs on another machine, resolve the active CC Switch skill path instead of copying this Linux path blindly.

The builder must:

1. fetch the official amd64 `Packages` index over HTTPS, select the highest version with `vercmp`, and download its fixed URL to a unique `.part` file or reflink-copy the supplied deb;
2. require exactly one `control.tar.*` and one `data.tar.*`;
3. require `Package: chatgpt`, `Architecture: amd64`, a valid version, and exactly one official index entry matching version, byte size, and SHA-256; stop on mismatch or if a local older deb is absent from the current index;
4. pass the verified deb SHA-256 and the local launcher SHA-256 to `makepkg`;
5. extract only the Debian payload, remove Debian-only lintian metadata, and install the bundled copyright file in the Arch license directory;
6. install the literal-argument launcher, generate a package through fakeroot, require the executable, launcher, desktop entry and install hook, then verify `.PKGINFO` identity, a valid compressed `.MTREE`, and numeric UID/GID 0 for every archive entry;
7. save the result under `./tmp/chatgpt-packages/<version>.<unique-id>/` without overwriting an older package, together with the official index, exact builder/templates and `build-record.txt` containing source URL, UTC time, hashes and Git commit.

Index matching relies on HTTPS and the official repository. It is **not** repository signature verification. Package metadata alone cannot establish a local deb's origin. Do not silently fall back to self-computed hashes when verification fails. Build records preserve exact script snapshots because the recorded Git commit can precede uncommitted changes.

## Runtime integration

The package retains the official application payload but replaces `codex-launcher` with `scripts/chatgpt-launcher.sh`. It reads `${XDG_CONFIG_HOME:-$HOME/.config}/chatgpt-flags.conf`: one literal argument per line; whitespace, CRLF, empty lines and full-line comments are handled. No shell evaluation, expansion or quote removal occurs. Do not quote an entire argument. Configured arguments precede command-line arguments. No flags file is created automatically and no sandbox-disabling flags are injected.

The AppArmor hook respects `/etc/apparmor.d/disable/chatgpt`, requires ABI 4.0, warns about `.pacnew`, and skips unloading a profile known to be absent. It loads the bundled user-namespace compatibility profile, not a comprehensive application confinement policy.

Runtime dependencies include `libglvnd` (official deb `libgl1`) and `libpulse` (audio client library). Keep `gcc-libs` for its Arch runtime dependency aggregation; verify current package ownership before changing to split packages. Optional dependencies explain Secret Service, PipeWire/portal, GTK 4 and Plasma integration. Never automatically install a portal backend or alternative audio server.

For dependency changes, inspect official deb `Depends`, ELF `NEEDED` via `readelf` when available, and `pacman -Qo` for resolved libraries. Include dynamically loaded graphics/audio libraries; checking only the main ELF misses those. `readelf` is an audit tool, not a builder dependency.

Run `python3 scripts/test-behavior.py` with `TMPDIR` set to a unique directory beneath the task workspace `tmp` to check literal arguments and the disabled-AppArmor path. Python is only a validation dependency. Also run one real build and inspect its record; do not install merely to validate the skill.

## Install and verify

When installation is authorized, show the exact package first and run:

```bash
yay -U '/absolute/path/chatgpt-version-release-x86_64.pkg.tar.zst'
pacman -Qkk chatgpt
```

Run this verification in the user's real host terminal, not inside an agent sandbox or user namespace that remaps UID/GID 0 to 65534. Such a sandbox can falsely show every `root:root` package file as `nobody:nobody` and make `pacman -Qkk` report all files altered. When execution context is uncertain, compare `stat` and `pacman -Qkk` once outside the sandbox before diagnosing package corruption.

Success requires the host-side `pacman -Qkk chatgpt` to report zero altered files. Also inspect:

```bash
pacman -Qi chatgpt
```

Confirm the expected version, `LicenseRef-OpenAI`, explicit Arch dependencies, optional dependencies, and `Install Script: Yes`. Treat nonzero altered-file counts, `nobody:nobody` package files, missing metadata, or a stale `.MTREE` as a failed build/install rather than declaring success.
