#!/usr/bin/env bash
#
# Vivado 2025.2.1 @ Ubuntu 26.04 修复脚本
#
# 问题背景:
#   Xilinx 的 ldlibpath.sh 只识别 Ubuntu 18/20/22/24，不识别 26.04，
#   导致 libncurses.so.5 / libtinfo.so.5（存放在 lib/lnx64.o/Ubuntu/24/ 里）
#   永远不会被加进动态库搜索路径。后果是安装器最后一步
#   "Generating installed device list"（派生 vivado -mode batch 跑 xlpartinfo.tcl）
#   因 Tcl 初始化失败而挂死，installed_devices.txt 永远生成不出来。
#
# 修复原理:
#   把这两个库复制到"始终在搜索路径里"的 lib/lnx64.o/ 根级。
#   - 对已安装的产品: 根级在 Vivado 启动时通过 LD_LIBRARY_PATH 总能被找到。
#   - 对安装器目录:   安装器派生 vivado 时 LD_LIBRARY_PATH 自带安装器的
#                     lib/lnx64.o，重装多少次都不受影响，且安装器目录不会被清空。
#
# 用法:
#   直接运行即可（幂等，重复执行无害）:
#     ./vivado_fix_ncurses.sh
#   可通过环境变量覆盖路径（比如装到了别处）:
#     XILINX_INSTALL_ROOT=/your/root ./vivado_fix_ncurses.sh
#
# 幂等性: 已存在且 md5 一致时跳过，不会重复覆盖。

set -euo pipefail

# ---------------------------------------------------------------------------
# 可覆盖的路径（默认值）
# ---------------------------------------------------------------------------
INSTALL_ROOT="${XILINX_INSTALL_ROOT:-/opt/eda/Xilinx/2025.2.1}"
INSTALLER_DIR="${XILINX_INSTALLER_DIR:-/home/vv/Desktop/FPGAs_AdaptiveSoCs_Unified_SDI_2025.2.1_0320_0604}"
BACKUP_DIR="${BACKUP_DIR:-$(cd "$(dirname "$0")" && pwd)}"

# 需要复制的库
LIBS="libncurses.so.5 libtinfo.so.5"

# 三个已安装产品
PRODUCTS=(Vivado Vitis PDM)

# ---------------------------------------------------------------------------
# 函数: 找一个可用的源库文件（按优先级）
# ---------------------------------------------------------------------------
find_source() {
    local lib="$1"
    local candidates=(
        "$INSTALL_ROOT/Vivado/lib/lnx64.o/Ubuntu/24/$lib"
        "$INSTALLER_DIR/lib/lnx64.o/Ubuntu/24/$lib"
        "$BACKUP_DIR/$lib"
    )
    for c in "${candidates[@]}"; do
        if [ -f "$c" ]; then
            echo "$c"
            return 0
        fi
    done
    echo ""
}

# ---------------------------------------------------------------------------
# 函数: 把库复制到指定 lib 根级（幂等）
# ---------------------------------------------------------------------------
install_to() {
    local dest_dir="$1"          # 目标 lib/lnx64.o 根级目录
    local ok=0
    if [ ! -d "$dest_dir" ]; then
        echo "  [跳过] 目录不存在: $dest_dir"
        return 0
    fi
    for lib in $LIBS; do
        local src
        src="$(find_source "$lib")"
        if [ -z "$src" ]; then
            echo "  [失败] 找不到源库 $lib（检查路径或把两个 .so 放到脚本同目录）"
            ok=1
            continue
        fi
        local dst="$dest_dir/$lib"
        if [ -f "$dst" ] && [ "$(md5sum "$src" | awk '{print $1}')" = "$(md5sum "$dst" | awk '{print $1}')" ]; then
            echo "  [OK] $lib 已存在且一致"
        else
            cp -v "$src" "$dst"
        fi
    done
    return "$ok"
}

# ---------------------------------------------------------------------------
# 1) 修复已安装的三个产品
# ---------------------------------------------------------------------------
echo "== 1) 修复已安装产品 (lib/lnx64.o 根级) =="
for p in "${PRODUCTS[@]}"; do
    echo "-- $p"
    install_to "$INSTALL_ROOT/$p/lib/lnx64.o"
done

# ---------------------------------------------------------------------------
# 2) 修复安装器目录（保证以后重装不卡）
# ---------------------------------------------------------------------------
echo "== 2) 修复安装器目录 =="
install_to "$INSTALLER_DIR/lib/lnx64.o"

# ---------------------------------------------------------------------------
# 3) 若 installed_devices.txt 缺失/为空，尝试重新生成
# ---------------------------------------------------------------------------
PARTS_FILE="$INSTALL_ROOT/Vivado/data/parts/installed_devices.txt"
if [ ! -s "$PARTS_FILE" ]; then
    echo "== 3) installed_devices.txt 缺失，尝试重新生成 =="
    VIVADO_BIN="$INSTALL_ROOT/Vivado/bin/vivado"
    if [ -x "$VIVADO_BIN" ]; then
        timeout 600 "$VIVADO_BIN" -nolog -nojournal -mode batch \
            -source "$INSTALL_ROOT/Vivado/scripts/sysgen/tcl/xlpartinfo.tcl" \
            -tclargs "$PARTS_FILE" >/dev/null 2>&1 \
            && echo "  已生成: $PARTS_FILE" \
            || echo "  [警告] 生成失败，可手动重跑"
    else
        echo "  [跳过] 未找到 vivado 可执行文件"
    fi
else
    echo "== 3) installed_devices.txt 已存在，跳过 =="
fi

# ---------------------------------------------------------------------------
# 汇总
# ---------------------------------------------------------------------------
echo
echo "== 验证 =="
for p in "${PRODUCTS[@]}"; do
    d="$INSTALL_ROOT/$p/lib/lnx64.o"
    [ -d "$d" ] && echo "  $d/libncurses.so.5 -> $(ls -la "$d/libncurses.so.5" 2>/dev/null | awk '{print $5}') B  $(md5sum "$d/libncurses.so.5" 2>/dev/null | cut -c1-8)"
done
echo "  $INSTALLER_DIR/lib/lnx64.o/libncurses.so.5 -> $(ls -la "$INSTALLER_DIR/lib/lnx64.o/libncurses.so.5" 2>/dev/null | awk '{print $5}') B"
echo
echo "修复完成。若这是刚跑完安装器后执行的，可用以下命令验证 Vivado 正常启动:"
echo "  $INSTALL_ROOT/Vivado/bin/vivado -version"
