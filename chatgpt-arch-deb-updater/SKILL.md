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

The builder requires `bash`, `curl` for automatic download, `bsdtar` from `libarchive`, `makepkg` from `pacman`, `gzip`, `gawk`, `grep`, `findutils`, and core GNU utilities. Explain missing dependencies and obtain confirmation before installing anything.

## Build

From the user's workspace root, build the latest official release:

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

1. download to a unique `.part` file or reflink-copy the supplied deb;
2. require exactly one `control.tar.*` and one `data.tar.*`;
3. require `Package: chatgpt`, `Architecture: amd64`, and a valid version;
4. compute and pass the deb SHA-256 to `makepkg`;
5. extract only the Debian payload, remove Debian-only lintian metadata, and install the bundled copyright file in the Arch license directory;
6. generate a package through fakeroot, then verify `.PKGINFO` identity, a valid compressed `.MTREE`, and numeric UID/GID 0 for every archive entry;
7. save the result under `./tmp/chatgpt-packages/<version>.<unique-id>/` without overwriting an older package.

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
