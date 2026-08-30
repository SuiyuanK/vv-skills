#!/usr/bin/env bash
# =============================================================================
# fix_spyglass_linux7.sh — 修复 SpyGlass X-2025.06 在 Linux 内核 7 上的
#   "ERROR(perl): Unknown platform: Linux-7.0.0-..." 启动失败
#
# 根因：SpyGlass 的 perl 包装脚本等 3 个脚本里 case 只匹配 Linux-2*~Linux-6*，
#       内核 7 掉进 *) 分支报 Unknown。
# 作用：给 3 个脚本的内核判断加 Linux-7*（改前自动备份为 *.linux7.orig）。
# 用法：bash fix_spyglass_linux7.sh [SpyGlass 根目录]
#       默认 /opt/EDA/Synopsys/spyglass/X-2025.06
# 幂等：重复执行会跳过已修复的文件。
# =============================================================================
set -euo pipefail

SG_ROOT="${1:-/opt/EDA/Synopsys/spyglass/X-2025.06}"
if [ -d "$SG_ROOT/SPYGLASS_HOME" ]; then
  SG_HOME="$SG_ROOT/SPYGLASS_HOME"
elif [ -d "$SG_ROOT/bin" ] && [ -d "$SG_ROOT/lib" ]; then
  SG_HOME="$SG_ROOT"
else
  echo "[ERR] 找不到 SpyGlass SPYGLASS_HOME: $SG_ROOT" >&2
  exit 1
fi

say() { echo "[*] $*"; }
ok()  { echo "[OK] $*"; }
warn(){ echo "[!] $*"; }

# fix_file <相对路径> <sed 匹配模式> <sed 替换>
fix_file() {
  local rel="$1" pat="$2" rep="$3"
  local f="$SG_HOME/$rel"
  if [ ! -f "$f" ]; then echo "[ERR] 必需文件不存在: $f" >&2; exit 1; fi
  if grep -q 'Linux-7\*' "$f"; then ok "已修复，跳过: $rel"; return; fi
  cp -a "$f" "$f.linux7.orig"
  say "已备份: $f.linux7.orig"
  sed -i "s/$pat/$rep/" "$f"
  if grep -q 'Linux-7\*' "$f"; then
    ok "已修复: $rel"
  else
    echo "[ERR] 修复失败(已备份 .linux7.orig): $rel" >&2
    exit 1
  fi
}

say "SPYGLASS_HOME: $SG_HOME"

# 1. perl 包装脚本：Linux-5* | Linux-6*)  → 加 | Linux-7*
fix_file "lib/multi-perl/bin/perl" \
  'Linux-5\* | Linux-6\*)' \
  'Linux-5* | Linux-6* | Linux-7*)'

# 2. spygenlib：只到 Linux-4*，补全 5/6/7
fix_file "bin/spygenlib" \
  'Linux-3\* | Linux-4\*)' \
  'Linux-3* | Linux-4* | Linux-5* | Linux-6* | Linux-7*)'

# 3. standard-environment.sh：Linux-6*)  → 加 | Linux-7*
fix_file "lib/SpyGlass/standard-environment.sh" \
  'Linux-6\*)' \
  'Linux-6* | Linux-7*)'

for required in \
  "$SG_HOME/lib/multi-perl/bin/perl" \
  "$SG_HOME/bin/spygenlib" \
  "$SG_HOME/lib/SpyGlass/standard-environment.sh"; do
  grep -q 'Linux-7\*' "$required" || { echo "[ERR] 验证失败: $required" >&2; exit 1; }
done

say "完成。验证：$SG_HOME/lib/multi-perl/bin/perl -v 应输出 perl 版本。"
