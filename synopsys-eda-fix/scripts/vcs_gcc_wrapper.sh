#!/usr/bin/env bash
# Dispatch generic compiler names to the parallel GCC 13 toolchain, only when
# this file is installed in the VCS-private PATH directory. Install this file
# as "gcc" and symlink the other supported names to it. Never place these
# generic names in ~/.local/bin or another global PATH directory.
set -e

case "${0##*/}" in
    gcc|cc)       compiler=/usr/bin/gcc-13 ;;
    g++|c++)      compiler=/usr/bin/g++-13 ;;
    cpp)          compiler=/usr/bin/cpp-13 ;;
    gcc-ar)       compiler=/usr/bin/gcc-ar-13 ;;
    gcc-nm)       compiler=/usr/bin/gcc-nm-13 ;;
    gcc-ranlib)   compiler=/usr/bin/gcc-ranlib-13 ;;
    *)
        printf 'vcs-gcc13: unsupported compiler entry name: %s\n' "${0##*/}" >&2
        exit 2
        ;;
esac

if [[ ! -x "$compiler" ]]; then
    printf 'vcs-gcc13: required compiler not found: %s\n' "$compiler" >&2
    exit 1
fi

exec "$compiler" "$@"
