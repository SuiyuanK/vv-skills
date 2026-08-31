# GCC 13 for MATLAB R2025b without changing the system GCC

Use this reference when the rolling distribution's GCC is newer than MATLAB
R2025b supports, or when building/installing the parallel `gcc13` package
fails.

## 1. Confirm the requirement and current state

Check the current MathWorks supported-compiler table rather than relying on an
old remembered range:

- <https://www.mathworks.com/support/requirements/supported-compilers-linux.html>

Then inspect the host:

```bash
gcc --version | head -1
gcc-13 --version | head -1
command -v matlab
readlink -f "$(command -v matlab)"
grep -E '^(CFLAGS|CXXFLAGS|LDFLAGS|MAKEFLAGS)=' /etc/makepkg.conf
```

R2025b was verified with GCC/G++ 13. The goal is parallel installation:
`/usr/bin/gcc` remains the system compiler and `/usr/bin/gcc-13` is exposed
only inside the MATLAB process.

Prefer a signed repository package when a trusted configured repository offers
the required version. Otherwise inspect the AUR PKGBUILD before building.

## 2. Bootstrap comparison failure

The observed AUR PKGBUILD used `--enable-bootstrap` and
`--with-build-config=bootstrap-lto`, with global makepkg flags passed as
`BOOT_CFLAGS` and `BOOT_LDFLAGS`. A host build using aggressive settings such
as `-march=native -O3`, extra linker hardening, and high parallelism failed with
many stage2/stage3 `*.o differs` lines.

Do not disable bootstrap or ignore `compare`. Rebuild in a clean chroot so the
host's `/etc/makepkg.conf` does not determine compiler reproducibility:

```bash
sudo pacman -S --needed devtools
mkdir -p "$PWD/tmp/gcc13-clean"
git clone https://aur.archlinux.org/gcc13.git "$PWD/tmp/gcc13-clean/gcc13"
cd "$PWD/tmp/gcc13-clean/gcc13"
extra-x86_64-build
```

`extra-x86_64-build` normally keeps its chroot under `/var/lib/archbuild`; tell
the user before running it because this is outside the workspace and consumes
several GiB.

Interpret the retained tree correctly:

- `.bad_compare` plus listed differences means bootstrap comparison failed.
- a `compare` stamp with no `.bad_compare` means comparison passed; an error
  later under `all-target-*` is a different failure.
- parallel output often hides the first error. Incrementally rerun the existing
  target with `make -j1 bootstrap` inside the retained chroot to expose it.

## 3. `linux/scc.h` removed from current Linux API headers

The verified clean build passed comparison and then failed in final
`libsanitizer` construction:

```text
sanitizer_platform_limits_posix.cpp: fatal error: linux/scc.h:
No such file or directory
make: ... all-target-libsanitizer ... Error 2
```

Linux removed this obsolete header in 2026. GCC upstream fixed libsanitizer by
removing the include and the unused `struct_scc_modem`/`struct_scc_stat` size
definitions. Use the supplied upstream-derived patch:

```text
assets/libsanitizer-linux-scc.patch
```

Upstream references:

- Linux removal: <https://github.com/torvalds/linux/commit/64edfa65062dc4509ba75978116b2f6d392346f5>
- LLVM fix: <https://github.com/llvm/llvm-project/commit/3dc4fd6dd41100f051a63642f449b16324389c96>
- GCC backport: <https://gcc.gnu.org/g:85a9c52605db1c075f379c915f3bac19b527f629>

### Preferred reproducible route

Copy the patch beside the PKGBUILD, add it to `source`, update checksums with
`updpkgsums`, and apply it from `prepare()` at the GCC source root:

```bash
patch -Np1 < "$srcdir/libsanitizer-linux-scc.patch"
```

Review the generated PKGBUILD diff, then run a new clean-chroot build. Do not
modify the installed Linux API headers and do not fabricate a replacement
`/usr/include/linux/scc.h`.

### Incremental recovery of an already expensive build

Use only when the clean build tree is retained, the bootstrap comparison stamp
is successful, and the first real error is the missing SCC header. Patch the
retained GCC source, then reuse the existing makepkg tree. Rediscover the
actual chroot and build-user names; the following were verified examples:

```bash
sudo arch-nspawn /var/lib/archbuild/extra-x86_64/vv \
  /bin/su - builduser -c "
sed -i \
  -e '\\@#include <linux/scc.h>@d' \
  -e '/struct_scc_modem_sz =/d' \
  -e '/struct_scc_stat_sz =/d' \
  /build/gcc13/src/gcc/libsanitizer/sanitizer_common/sanitizer_platform_limits_posix.cpp
"
```

The Arch `arch-nspawn` wrapper accepts its own options before the chroot path;
`systemd-nspawn` options such as `--bind` must come after that path. The
retained `/build/gcc13` is a makepkg build directory and does not itself hold
the original PKGBUILD. Remount the host package directory as `/startdir` and
`/pkgdest`:

```bash
sudo arch-nspawn /var/lib/archbuild/extra-x86_64/vv \
  --bind="$PWD:/startdir" --bind="$PWD:/pkgdest" \
  /bin/su - builduser -c \
  'cd /startdir && makepkg --noextract --noprepare --nocheck'
```

This recovery intentionally skips the package check function. Compensate with
archive inspection, version checks, and real compiler/MEX tests. If the build
tree, patch state, or compare result is uncertain, use the reproducible route
instead.

## 4. Install split packages and verify parallelism

Inspect archives before installation:

```bash
pacman -Qip ./gcc13-*.pkg.tar.zst
bsdtar -tf ./gcc13-*.pkg.tar.zst >/dev/null
```

For C/C++ MEX, install the matching `gcc13` and `gcc13-libs` packages. Install
`gcc13-fortran` and `gcc13-debug` only when requested. Never mix versions from
different builds.

Verify:

```bash
pacman -Q gcc13 gcc13-libs
gcc --version | head -1
gcc-13 --version | head -1
g++-13 --version | head -1
```

The first line must remain the rolling system GCC; suffixed commands must show
13.x.

## 5. Make every normal MATLAB entry use GCC 13 only

Resolve and preserve the true MATLAB binary before creating a shadowing
wrapper. A wrapper named `~/.local/bin/matlab` must execute an absolute real
binary such as `/opt/EDA/MATLAB/bin/matlab`, never call `matlab` recursively.

The wrapper should:

1. verify `gcc-13`, `g++-13`, `gfortran-13`, and `cpp-13` as needed;
2. create a private directory such as
   `${XDG_DATA_HOME:-$HOME/.local/share}/matlab-gcc13/bin`;
3. link suffixed compilers there under the generic names;
4. prepend only that directory to the wrapper process's `PATH`; and
5. `exec` the absolute real MATLAB binary with `"$@"`.

Ensure `~/.local/bin` precedes `/usr/local/bin` for the user's shell. Do not add
the compiler shim directory itself to shell startup files.

For GUI launch, create a user-local `.desktop` entry whose `Exec=` is the
absolute wrapper path. Prefer `~/.local/share/applications`; optionally create a
trusted executable desktop copy when the user explicitly wants an icon. Do not
edit MathWorks' system desktop file.

Normal scripts that inherit the user's PATH can call `matlab`. Scripts,
systemd units, or cron jobs that replace PATH should call the wrapper by
absolute path.

## 6. Verify from inside MATLAB, then test MEX

First prove the wrapper's process environment:

```bash
~/.local/bin/matlab -batch \
  "system('gcc -dumpfullversion'); system('g++ -dumpfullversion'); system('gfortran -dumpfullversion');"
```

Then configure compilers deliberately:

```matlab
mex -setup C
mex -setup C++
mex -setup FORTRAN
mex.getCompilerConfigurations('C','Selected')
mex.getCompilerConfigurations('C++','Selected')
```

Finish by compiling and executing a small C or C++ MEX module in an isolated
workspace directory. Keep the ordinary shell's `gcc --version` check in the
same verification report to prove unrelated EDA tools remain on system GCC.
