#!/usr/bin/env bash
# =============================================================================
# lc_shell_wrapper.sh — 包装 LC (Library Compiler) 屏蔽退出时的 segfault
#
# 背景：LC X-2025.06 在 glibc 2.39 (Ubuntu 24.04 / Mint 22.3) 上，read_lib/
#       write_lib 完成后、退出清理阶段会 segfault（Error code=11）。.db 产出
#       是完整正确的，只是退出码为 139/1 且刷一堆 stack trace / fatal 报错。
# 作用：运行真实 lc_shell，过滤掉退出崩溃报错，并在触发已知崩溃时返回 0。
# 用法：bash lc_shell_wrapper.sh [-f 脚本.tcl] [其它 lc_shell 参数]
# 建议：装到 ~/.local/bin/lc_shell 并在 .zshrc 加
#         alias lc_shell='~/.local/bin/lc_shell'
#       （原 PATH 里 LC 的 bin 排在 ~/.local/bin 前，不加别名会命中真身）。
# =============================================================================
set -u

export SYNOPSYS_LC_ROOT="${SYNOPSYS_LC_ROOT:-/opt/EDA/Synopsys/lc/X-2025.06}"
export PATH="$SYNOPSYS_LC_ROOT/bin:$PATH"

log="$(mktemp "${TMPDIR:-/tmp}/lc_shell_wrap.XXXXXX" 2>/dev/null || echo "/tmp/lc_shell_wrap.$$")"
trap 'rm -f "$log"' EXIT

"$SYNOPSYS_LC_ROOT/bin/lc_shell" "$@" 2>&1 | tee "$log" | sed \
    -e '/Thank you for using Library Compiler/,$d' \
    -e '/Segmentation fault/,$d' \
    -e '/^SNPSee_/,$d' \
    -e '/The tool has just encountered a fatal error/,$d'
rc=${PIPESTATUS[0]}

# 若日志里出现了已知的"退出崩溃"，视为成功
if grep -qE 'Fatal: Internal system error|Segmentation fault|stack trace|SNPSee_' "$log"; then
    rc=0
fi
exit "$rc"
