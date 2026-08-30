#!/usr/bin/env bash
# VCS X-2025.06 generates C that GCC 16 rejects for implicit declarations.
# Install as ~/.local/libexec/synopsys-vcs/gcc; do not place it in global PATH.
exec /usr/bin/gcc -Wno-implicit-function-declaration "$@"
