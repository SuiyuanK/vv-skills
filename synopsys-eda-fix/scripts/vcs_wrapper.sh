#!/usr/bin/env bash
# VCS X-2025.06 wrapper for modern Linux linkers, GCC 16, and optional KDB libs.
set -u

export VCS_HOME="${VCS_HOME:-/opt/EDA/Synopsys/vcs/X-2025.06}"
export VCS_ARCH_OVERRIDE="${VCS_ARCH_OVERRIDE:-linux}"

need_verdi_compat=0
for arg in "$@"; do
    case "$arg" in
        -kdb|-kdb=*|-debug_acc*|-debug_access*) need_verdi_compat=1 ;;
    esac
done

if [ "$need_verdi_compat" = "1" ]; then
    VERDI_HOME="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}"
    export LD_LIBRARY_PATH="/opt/EDA/Synopsys/.compat/verdi:$VERDI_HOME/platform/LINUXAMD64/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/plugins:${LD_LIBRARY_PATH:-}"
fi

vcs_gcc_dir="${VCS_GCC_WRAPPER_DIR:-$HOME/.local/libexec/synopsys-vcs}"
if [ -x "$vcs_gcc_dir/gcc" ]; then
    export PATH="$vcs_gcc_dir:$PATH"
fi

original_args=("$@")
final_args=()
has_ldflags=0

while [ "$#" -gt 0 ]; do
    case "$1" in
        -LDFLAGS)
            if [ "$#" -lt 2 ]; then
                exec "$VCS_HOME/bin/vcs" "${original_args[@]}"
            fi
            ldflags="$2"
            if [[ "$ldflags" != *--no-as-needed* ]]; then
                ldflags="$ldflags -Wl,--no-as-needed"
            fi
            final_args+=("-LDFLAGS" "$ldflags")
            has_ldflags=1
            shift 2
            ;;
        -LDFLAGS=*)
            ldflags="${1#-LDFLAGS=}"
            if [[ "$ldflags" != *--no-as-needed* ]]; then
                ldflags="$ldflags -Wl,--no-as-needed"
            fi
            final_args+=("-LDFLAGS" "$ldflags")
            has_ldflags=1
            shift
            ;;
        *)
            final_args+=("$1")
            shift
            ;;
    esac
done

if [ "$has_ldflags" = "0" ]; then
    final_args+=("-LDFLAGS" "-Wl,--no-as-needed")
fi

exec "$VCS_HOME/bin/vcs" "${final_args[@]}"
