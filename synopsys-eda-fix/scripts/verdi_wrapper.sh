#!/usr/bin/env bash
# Verdi wrapper for Synopsys X-2025.06 on CachyOS/Arch and Mint/Ubuntu.
# Keep all old-ABI and Fontconfig compatibility changes process-local.
set -u

export VERDI_HOME="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}"
export LD_LIBRARY_PATH="/opt/EDA/Synopsys/.compat/verdi:$VERDI_HOME/platform/LINUXAMD64/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/plugins:${LD_LIBRARY_PATH:-}"

system_fontconfig=""
for candidate in /usr/lib/libfontconfig.so.1 /usr/lib/x86_64-linux-gnu/libfontconfig.so.1; do
    if [[ -r "$candidate" ]]; then
        system_fontconfig="$candidate"
        break
    fi
done
if [[ -n "$system_fontconfig" && ":${LD_PRELOAD:-}:" != *":$system_fontconfig:"* ]]; then
    export LD_PRELOAD="$system_fontconfig${LD_PRELOAD:+:$LD_PRELOAD}"
fi

exec "$VERDI_HOME/bin/verdi" "$@"
