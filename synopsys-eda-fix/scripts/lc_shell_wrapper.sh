#!/usr/bin/env bash
# =============================================================================
# lc_shell_wrapper.sh — LC 旧 krb5 兼容与退出清理 segfault 的窄化处理
#
# 背景：LC X-2025.06 在 glibc 2.39 (Ubuntu 24.04 / Mint 22.3) 上，read_lib/
#       write_lib 完成后、退出清理阶段会 segfault（Error code=11）。.db 产出
#       是完整正确的，只是退出码为 139/1 且刷一堆 stack trace / fatal 报错。
# 作用：预加载 Verdi 自带旧 krb5；只有成功横幅之后出现已知退出崩溃时才返回 0。
# 用法：bash lc_shell_wrapper.sh [-f 脚本.tcl] [其它 lc_shell 参数]
# 建议：装到 ~/.local/bin/lc_shell 并在 .zshrc 加
#         alias lc_shell='~/.local/bin/lc_shell'
#       （原 PATH 里 LC 的 bin 排在 ~/.local/bin 前，不加别名会命中真身）。
# =============================================================================
set -u

export SYNOPSYS_LC_ROOT="${SYNOPSYS_LC_ROOT:-/opt/EDA/Synopsys/lc/X-2025.06}"
export PATH="$SYNOPSYS_LC_ROOT/bin:$PATH"

KB="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}/platform/LINUXAMD64/lib/Qt5/lib/depends/krb5"
lc_preload="${LD_PRELOAD:-}"
lc_library_path="${LD_LIBRARY_PATH:-}"
if [ -f "$KB/libkrb5.so.3" ]; then
    lc_preload="$KB/libkrb5.so.3:$KB/libk5crypto.so.3:$KB/libgssapi_krb5.so.2:$KB/libkrb5support.so.0${lc_preload:+:$lc_preload}"
    lc_library_path="$KB${lc_library_path:+:$lc_library_path}"
fi

tmp_base="${TMPDIR:-${XDG_RUNTIME_DIR:-/tmp}}"
log="$(mktemp "$tmp_base/lc_shell_wrap.XXXXXX")" || exit 1
trap 'rm -f "$log"' EXIT

# 只让 LC 子进程加载旧 krb5；不可 export 给系统 tee/sed/grep。
env LD_PRELOAD="$lc_preload" LD_LIBRARY_PATH="$lc_library_path" \
    "$SYNOPSYS_LC_ROOT/bin/lc_shell" "$@" 2>&1 | tee "$log" | sed \
    -e '/Thank you for using Library Compiler/,$d' \
    -e '/Segmentation fault/,$d' \
    -e '/^SNPSee_/,$d' \
    -e '/The tool has just encountered a fatal error/,$d'
rc=${PIPESTATUS[0]}

thanks_line="$(grep -nF 'Thank you for using Library Compiler.' "$log" | tail -n 1 | cut -d: -f1)"
crash_line="$(grep -nE 'Fatal: Internal system error|Segmentation fault|^SNPSee_|The tool has just encountered a fatal error' "$log" | tail -n 1 | cut -d: -f1)"

known_exit_crash=0
case "$rc" in
    1|134|139)
        if [[ "$thanks_line" =~ ^[0-9]+$ ]] && [[ "$crash_line" =~ ^[0-9]+$ ]] && [ "$crash_line" -gt "$thanks_line" ]; then
            known_exit_crash=1
        fi
        ;;
esac

if [ "$known_exit_crash" = "1" ] && [ -n "${LC_EXPECT_OUTPUTS:-}" ]; then
    old_ifs="$IFS"
    IFS=':'
    for output in $LC_EXPECT_OUTPUTS; do
        if [ ! -s "$output" ]; then
            printf 'lc_shell wrapper: expected output missing or empty: %s\n' "$output" >&2
            known_exit_crash=0
        fi
    done
    IFS="$old_ifs"
fi

if [ "$known_exit_crash" = "1" ]; then
    printf 'lc_shell wrapper: normalized known post-success cleanup crash (raw rc=%s)\n' "$rc" >&2
    rc=0
fi
exit "$rc"
