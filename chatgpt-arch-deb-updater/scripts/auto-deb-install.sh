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
readonly REPOSITORY_URL="https://persistent.oaistatic.com/codex-app-prod/linux/deb"
readonly INDEX_URL="$REPOSITORY_URL/dists/stable/main/binary-amd64/Packages"
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

required=(bsdtar makepkg sha256sum realpath awk grep gzip find mktemp curl stat uname date cp vercmp)
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

[[ $(uname -m) == x86_64 ]] || { echo "Error: x86_64 host required" >&2; exit 1; }
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

export TMPDIR="$STAGE"
DEB="$STAGE/chatgpt.deb"
# The index is fetched over HTTPS; this is not repository signature verification.
curl --fail --location --proto '=https' --proto-redir '=https' --retry 3 --connect-timeout 20 \
  --output "$STAGE/Packages" "$INDEX_URL"
awk 'BEGIN { RS=""; FS="\n" }
{ delete f; for(i=1;i<=NF;i++) { n=index($i,": "); if(n) f[substr($i,1,n-1)]=substr($i,n+2) }
  if(f["Package"]=="chatgpt" && f["Architecture"]=="amd64")
    print f["Version"] "\t" f["Filename"] "\t" f["SHA256"] "\t" f["Size"]
}' "$STAGE/Packages" > "$STAGE/releases.tsv"
[[ -s $STAGE/releases.tsv ]] || { echo 'Error: no amd64 chatgpt in official index' >&2; exit 1; }
source_kind=local
if (( $# == 0 )); then
  source_kind=download
  # Do not assume index ordering when several versions are published.
  selected_version=''
  while IFS=$'\t' read -r version filename digest size; do
    if [[ -z $selected_version ]] || (( $(vercmp "$version" "$selected_version") > 0 )); then
      selected_version=$version
      selected_filename=$filename
    fi
  done < "$STAGE/releases.tsv"
  [[ $selected_filename == pool/main/c/chatgpt/chatgpt_*_amd64.deb && $selected_filename != *..* ]] || exit 1
  source_url="$REPOSITORY_URL/$selected_filename"
  echo "[1/5] Downloading $selected_version from the official repository..."
  curl --fail --location --proto '=https' --proto-redir '=https' --retry 3 --connect-timeout 20 \
    --output "$DEB.part" "$source_url"
  mv -- "$DEB.part" "$DEB"
else
  SOURCE_DEB="$(realpath "$1")"
  [[ -f $SOURCE_DEB && -r $SOURCE_DEB ]] || { echo 'Error: unreadable deb' >&2; exit 1; }
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
match_count=0
while IFS=$'\t' read -r version filename digest size; do
  if [[ $version == "$deb_version" && $digest == "$deb_sha256" && $size == "$(stat -c %s "$DEB")" ]]; then
    [[ $filename == pool/main/c/chatgpt/chatgpt_*_amd64.deb && $filename != *..* ]] || exit 1
    source_url="$REPOSITORY_URL/$filename"
    match_count=$((match_count + 1))
  fi
done < "$STAGE/releases.tsv"
[[ $match_count == 1 ]] || {
  echo 'Error: deb does not uniquely match official index version/size/SHA-256; refusing build.' >&2
  exit 1
}
echo "      Version: $deb_version"
echo "      SHA-256: $deb_sha256"

echo "[3/5] Preparing makepkg workspace..."
cp -- "$PKGBUILD_TEMPLATE" "$STAGE/PKGBUILD"
cp -- "$INSTALL_TEMPLATE" "$STAGE/chatgpt.install"
cp -- "$SCRIPT_DIR/chatgpt-launcher.sh" "$STAGE/chatgpt-launcher.sh"
cp -- "$0" "$STAGE/builder.sh"
launcher_sha256=$(sha256sum "$STAGE/chatgpt-launcher.sh" | awk '{print $1}')
mkdir -p "$STAGE/makepkg-tmp" "$STAGE/pkgdest"

echo "[4/5] Building the Arch package with makepkg..."
(
  cd "$STAGE"
  export CHATGPT_PKGVER="$pkgver"
  export CHATGPT_DEB_SHA256="$deb_sha256"
  export CHATGPT_LAUNCHER_SHA256="$launcher_sha256"
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
grep -qx "pkgver = $pkgver-2" <<<"$PKGINFO"
grep -qx 'arch = x86_64' <<<"$PKGINFO"
bsdtar -xOf "$PKG" .MTREE | gzip -t
if ! bsdtar --numeric-owner -tvf "$PKG" |
  awk '{ if ($3 != 0 || $4 != 0) bad = 1 } END { exit bad }'; then
  echo "Error: generated package contains non-root UID/GID entries." >&2
  exit 1
fi

bsdtar -tf "$PKG" > "$STAGE/package-files.txt"
for member in usr/lib/chatgpt/ChatGPT usr/lib/chatgpt/codex-launcher usr/share/applications/chatgpt.desktop .INSTALL; do
  grep -Fxq "$member" "$STAGE/package-files.txt" || { echo "Error: missing $member" >&2; exit 1; }
done
PACKAGE_ROOT="$WORKBASE/chatgpt-packages"
mkdir -p "$PACKAGE_ROOT"
FINAL_DIR="$(mktemp -d "$PACKAGE_ROOT/${pkgver}.XXXXXXXX")"
FINAL_PKG="$FINAL_DIR/$(basename "$PKG")"
cp -- "$PKG" "$FINAL_PKG"
cp -- "$STAGE/Packages" "$STAGE/PKGBUILD" "$STAGE/chatgpt.install" "$STAGE/chatgpt-launcher.sh" "$STAGE/builder.sh" "$FINAL_DIR/"
{
  printf 'built_at_utc=%s\nsource_kind=%s\nindex_url=%s\nsource_url=%s\ndeb_version=%s\ndeb_sha256=%s\nverification=https-index-sha256-size-version; no signature verification\n' \
    "$(date -u +%FT%TZ)" "$source_kind" "$INDEX_URL" "$source_url" "$deb_version" "$deb_sha256"
  printf 'builder_git_commit=%s\n' "$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || echo unavailable)"
  printf 'Builder snapshots below are authoritative even with uncommitted changes.\n'
  sha256sum "$FINAL_DIR/PKGBUILD" "$FINAL_DIR/chatgpt.install" "$FINAL_DIR/chatgpt-launcher.sh" "$FINAL_DIR/builder.sh" "$FINAL_PKG"
} > "$FINAL_DIR/build-record.txt"

echo
echo "Build complete: $FINAL_PKG"
if command -v pacman >/dev/null 2>&1 && pacman -Q chatgpt >/dev/null 2>&1; then
  installed_version="$(pacman -Q chatgpt | awk '{print $2}')"
  echo "Currently installed: chatgpt $installed_version"
fi
echo "Install command: yay -U '$FINAL_PKG'"
echo "Post-install check: pacman -Qkk chatgpt"
