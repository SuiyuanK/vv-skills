#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   auto-deb-install.sh             # download the latest official deb
#   auto-deb-install.sh ./x.deb     # build from a local official deb
#
# This builds only. It does not install the generated package.

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly WORKSPACE_ROOT="$(realpath "${CHATGPT_ARCH_WORKSPACE:-$PWD}")"
readonly WORKBASE="$WORKSPACE_ROOT/tmp"
readonly DOWNLOAD_URL="https://persistent.oaistatic.com/codex-app-prod/linux/deb/latest/chatgpt_amd64.deb"
readonly PKGBUILD_TEMPLATE="$SCRIPT_DIR/PKGBUILD.chatgpt"
readonly INSTALL_TEMPLATE="$SCRIPT_DIR/chatgpt.install"

if (( EUID == 0 )); then
  echo "Error: run this builder as an ordinary user; makepkg uses fakeroot." >&2
  echo "Usage: $0 [deb-file]" >&2
  exit 1
fi

if (( $# > 1 )); then
  echo "Usage: $0 [deb-file]" >&2
  exit 1
fi

required=(bsdtar makepkg sha256sum realpath awk grep gzip find mktemp)
if (( $# == 0 )); then
  required+=(curl)
fi
for cmd in "${required[@]}"; do
  command -v "$cmd" >/dev/null 2>&1 || {
    echo "Error: missing command: $cmd" >&2
    exit 1
  }
done

[[ -r "$PKGBUILD_TEMPLATE" ]] || {
  echo "Error: missing PKGBUILD template: $PKGBUILD_TEMPLATE" >&2
  exit 1
}
[[ -r "$INSTALL_TEMPLATE" ]] || {
  echo "Error: missing install hook: $INSTALL_TEMPLATE" >&2
  exit 1
}

mkdir -p "$WORKBASE"
STAGE="$(mktemp -d "$WORKBASE/chatgpt-build.XXXXXXXX")"
cleanup() {
  if [[ -n ${STAGE:-} && $STAGE == "$WORKBASE"/chatgpt-build.* && -d $STAGE ]]; then
    rm -rf -- "$STAGE"
  fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

DEB="$STAGE/chatgpt.deb"
if (( $# == 0 )); then
  echo "[1/5] Downloading the latest official OpenAI deb..."
  curl \
    --fail \
    --location \
    --retry 3 \
    --retry-all-errors \
    --connect-timeout 20 \
    --output "$DEB.part" \
    "$DOWNLOAD_URL"
  mv -- "$DEB.part" "$DEB"
else
  SOURCE_DEB="$(realpath "$1")"
  [[ -f "$SOURCE_DEB" && -r "$SOURCE_DEB" ]] || {
    echo "Error: deb file does not exist or is unreadable: $1" >&2
    exit 1
  }
  echo "[1/5] Using local deb: $SOURCE_DEB"
  cp --reflink=auto -- "$SOURCE_DEB" "$DEB"
fi

echo "[2/5] Validating Debian package structure and metadata..."
mapfile -t control_members < <(bsdtar -tf "$DEB" | grep -E '^control\.tar\.[A-Za-z0-9]+$' || true)
mapfile -t data_members < <(bsdtar -tf "$DEB" | grep -E '^data\.tar\.[A-Za-z0-9]+$' || true)
if (( ${#control_members[@]} != 1 || ${#data_members[@]} != 1 )); then
  echo "Error: file is not a complete Debian binary package." >&2
  exit 1
fi

CONTROL="$(bsdtar -xOf "$DEB" "${control_members[0]}" | bsdtar -xOf - ./control)"
deb_package="$(awk -F ': ' '$1 == "Package" { print $2; exit }' <<<"$CONTROL")"
deb_version="$(awk -F ': ' '$1 == "Version" { print $2; exit }' <<<"$CONTROL")"
deb_arch="$(awk -F ': ' '$1 == "Architecture" { print $2; exit }' <<<"$CONTROL")"

if [[ $deb_package != chatgpt || $deb_arch != amd64 || -z $deb_version ]]; then
  echo "Error: expected chatgpt/amd64, got ${deb_package:-unknown}/${deb_arch:-unknown}." >&2
  exit 1
fi

pkgver="${deb_version//:/_}"
pkgver="${pkgver//-/.}"
if [[ $pkgver =~ [[:space:]/] || -z $pkgver ]]; then
  echo "Error: cannot convert Debian version: $deb_version" >&2
  exit 1
fi

deb_sha256="$(sha256sum "$DEB" | awk '{print $1}')"
echo "      Version: $deb_version"
echo "      SHA-256: $deb_sha256"

echo "[3/5] Preparing makepkg workspace..."
cp -- "$PKGBUILD_TEMPLATE" "$STAGE/PKGBUILD"
cp -- "$INSTALL_TEMPLATE" "$STAGE/chatgpt.install"
mkdir -p "$STAGE/makepkg-tmp" "$STAGE/pkgdest"

echo "[4/5] Building the Arch package with makepkg..."
(
  cd "$STAGE"
  export CHATGPT_PKGVER="$pkgver"
  export CHATGPT_DEB_SHA256="$deb_sha256"
  export PKGDEST="$STAGE/pkgdest"
  export TMPDIR="$STAGE/makepkg-tmp"
  makepkg --cleanbuild --clean --force --noconfirm
)

mapfile -t built_packages < <(find "$STAGE/pkgdest" -maxdepth 1 -type f -name 'chatgpt-*.pkg.tar.*' -print)
if (( ${#built_packages[@]} != 1 )); then
  echo "Error: makepkg generated ${#built_packages[@]} package files; expected one." >&2
  exit 1
fi

echo "[5/5] Verifying and saving the package..."
PKG="${built_packages[0]}"
PKGINFO="$(bsdtar -xOf "$PKG" .PKGINFO)"
grep -qx 'pkgname = chatgpt' <<<"$PKGINFO"
grep -qx "pkgver = $pkgver-1" <<<"$PKGINFO"
grep -qx 'arch = x86_64' <<<"$PKGINFO"
bsdtar -xOf "$PKG" .MTREE | gzip -t
if ! bsdtar --numeric-owner -tvf "$PKG" |
  awk '{ if ($3 != 0 || $4 != 0) bad = 1 } END { exit bad }'; then
  echo "Error: generated package contains non-root UID/GID entries." >&2
  exit 1
fi

PACKAGE_ROOT="$WORKBASE/chatgpt-packages"
mkdir -p "$PACKAGE_ROOT"
FINAL_DIR="$(mktemp -d "$PACKAGE_ROOT/${pkgver}.XXXXXXXX")"
FINAL_PKG="$FINAL_DIR/$(basename "$PKG")"
cp -- "$PKG" "$FINAL_PKG"

echo
echo "Build complete: $FINAL_PKG"
if command -v pacman >/dev/null 2>&1 && pacman -Q chatgpt >/dev/null 2>&1; then
  installed_version="$(pacman -Q chatgpt | awk '{print $2}')"
  echo "Currently installed: chatgpt $installed_version"
fi
echo "Install command: yay -U '$FINAL_PKG'"
echo "Post-install check: pacman -Qkk chatgpt"
