# MATLAB R2025b installer on CachyOS / Arch

Use this reference only for installer startup, download, extraction, or partial
installation failures.

## 1. Establish the failure class

Inspect rather than guessing from the GUI dialog:

```bash
uname -m
grep -E '^(ID|ID_LIKE|VERSION_ID)=' /etc/os-release
findmnt /tmp
df -h /tmp .
coredumpctl info MathWorksProductInstaller
```

Check the original installer archive independently when one exists. A valid
archive plus a reproducible `lc_init` crash means extraction of the original
download is not the root cause.

On the verified host, the decisive stack was:

```text
libmwinstall_activationwsclientimpl.so -> lc_init -> libgnutls.so.30
```

Arch's `libgnutls.so.30` loads `libleancrypto.so.1`, which exports another
`lc_init`. This symbol collision caused SIGSEGV before normal installer work.
It was not caused by Wayland, `xhost`, `sudo`, or a corrupt installer ZIP.

Confirm the relationship on the current host before applying the workaround:

```bash
ldd /usr/lib/libgnutls.so.30 | grep leancrypto
nm -D /usr/lib/libleancrypto.so.1 | grep -w lc_init
```

## 2. Process-local workaround

Use the system library only for the installer process:

```bash
env LD_PRELOAD=/usr/lib/libleancrypto.so.1 ./install
```

If the chosen target requires root:

```bash
sudo -H env LD_PRELOAD=/usr/lib/libleancrypto.so.1 ./install
```

Prefer a normal-user install when the target is writable. Do not replace,
downgrade, or globally preload GnuTLS/leancrypto.

## 3. Download and extraction failures after startup

If the preloaded installer reaches login/product selection but later reports
an extraction error, inspect its root log first. On the verified case,
`Request timed out` occurred before:

```text
archive_read_open_filename(): Unrecognized archive format
```

That sequence meant an encrypted component download was incomplete; it did not
prove the original installer archive was corrupt.

Do not run a roughly 25 GB all-products install through a 16 GB `/tmp` tmpfs.
Use a disk-backed directory under the active workspace and preserve the same
process-local preload:

```bash
mkdir -p "$PWD/tmp/matlab-r2025b-install"
env TMPDIR="$PWD/tmp/matlab-r2025b-install" \
    LD_PRELOAD=/usr/lib/libleancrypto.so.1 \
    ./install
```

Product size, free space, and target path must be rechecked for every retry.

## 4. Partial target handling

A large target directory is not evidence of a working installation. Require at
least the real launcher and version metadata, then start MATLAB. If either is
missing, preserve or rename the partial directory before retrying; do not merge
new content into an unexplained failed tree and do not delete evidence without
authorization.

After a successful install, resolve the true executable rather than assuming a
path:

```bash
command -v matlab
readlink -f "$(command -v matlab)"
```
