#!/usr/bin/env bash
# =============================================================================
# setup_synopsys_license.sh — Synopsys FlexLM license 服务器配置与开机自启
#
# 幂等脚本，可重复执行。作用：
#   1. 校验 hostid 是否匹配 license 文件 SERVER 行
#   2. 检测 /usr/tmp 是否缺失（lmgrd 硬编码依赖 /usr/tmp/.flexlm）
#   3. 核对 SNPSLMD_LICENSE_FILE 端口 与 license SERVER 行端口是否一致
#   4. 生成并启用 systemd 用户服务（lmgrd -z 前台）+ enable-linger 开机自启
#   5. 用 lmstat 验证 license server UP
#
# 可用环境变量覆盖默认路径：
#   SYN_LICENSE_FILE   license 文件路径（默认见下）
#   SCL_BIN            SCL 工具目录（默认见下）
#   SERVER_PORT        期望的 license 端口（默认从 license SERVER 行读取）
# =============================================================================
set -euo pipefail

# ---- 默认路径（可按需覆盖）--------------------------------------------------
LICENSE_FILE="${SYN_LICENSE_FILE:-/opt/eda/Synopsys/scl/2024.06/admin/license/synopsys.lic}"
SCL_BIN="${SCL_BIN:-/opt/eda/Synopsys/scl/2024.06/linux64/bin}"
LOG_FILE="$(dirname "$LICENSE_FILE")/../logs/lmgrd.log"
LOG_FILE="$(cd "$(dirname "$LOG_FILE")" && pwd)/lmgrd.log"
SERVICE_NAME="synopsys-lic.service"
SERVICE_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
SERVICE_FILE="$SERVICE_DIR/$SERVICE_NAME"

c_red='\033[0;31m'; c_grn='\033[0;32m'; c_yel='\033[1;33m'; c_cyn='\033[0;36m'; c_nc='\033[0m'
say()  { printf "${c_cyn}[*]${c_nc} %s\n" "$*"; }
ok()   { printf "${c_grn}[OK]${c_nc} %s\n" "$*"; }
warn() { printf "${c_yel}[!]${c_nc} %s\n" "$*"; }
die()  { printf "${c_red}[ERR]${c_nc} %s\n" "$*" >&2; exit 1; }

# ---- 0. 前置检查 ------------------------------------------------------------
[ -f "$LICENSE_FILE" ] || die "找不到 license 文件: $LICENSE_FILE"
[ -x "$SCL_BIN/lmgrd" ] || die "找不到 lmgrd: $SCL_BIN/lmgrd"
which lmutil >/dev/null 2>&1 || PATH="$SCL_BIN:$PATH"
[ -x "$SCL_BIN/lmutil" ] || die "找不到 lmutil: $SCL_BIN/lmutil"

say "license 文件: $LICENSE_FILE"
say "SCL 工具目录: $SCL_BIN"
mkdir -p "$(dirname "$LOG_FILE")"

# ---- 1. hostid 校验 ---------------------------------------------------------
SERVER_LINE=$(grep -E '^SERVER ' "$LICENSE_FILE" | head -1 | tr -d '\r')
[ -n "$SERVER_LINE" ] || die "license 文件里没有 SERVER 行"
LIC_HOSTID=$(echo "$SERVER_LINE" | awk '{print $3}')
MASTER_HOST=$(echo "$SERVER_LINE" | awk '{print $2}')
LIC_PORT=$(echo "$SERVER_LINE" | awk '{print $4}')
say "license SERVER: $MASTER_HOST  hostid=$LIC_HOSTID  port=$LIC_PORT"

REAL_HOSTID=$( "$SCL_BIN/lmutil" lmhostid 2>/dev/null | grep -oE '[0-9a-fA-F]{12}' | head -1 || true )
if [ -n "$REAL_HOSTID" ] && [ "$REAL_HOSTID" != "$LIC_HOSTID" ]; then
  for hid in $( "$SCL_BIN/lmutil" lmhostid 2>/dev/null | grep -oE '[0-9a-fA-F]{12}' ); do
    if [ "$hid" = "$LIC_HOSTID" ]; then REAL_HOSTID="$LIC_HOSTID"; break; fi
  done
fi
if [ "$REAL_HOSTID" != "$LIC_HOSTID" ]; then
  warn "hostid 不匹配！license 期望 $LIC_HOSTID，本机 hostid: $( "$SCL_BIN/lmutil" lmhostid 2>/dev/null | head -1 )"
  warn "请在正确的主机上生成匹配的 license，否则 lmgrd 无法启动。"
  die "hostid 校验未通过。"
fi
ok "hostid 匹配 ($LIC_HOSTID)"

# ---- 2. /usr/tmp 检测（lmgrd 硬编码 /usr/tmp/.flexlm）-----------------------
if [ ! -d /usr/tmp ]; then
  warn "/usr/tmp 不存在（lmgrd 硬编码用 /usr/tmp/.flexlm，无环境变量可改）"
  warn "请以 root 执行下面命令后重跑本脚本："
  echo
  printf "   ${c_yel}sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp${c_nc}\n"
  echo
  exit 2
fi
[ -d /usr/tmp/.flexlm ] || mkdir -p /usr/tmp/.flexlm 2>/dev/null || true
ok "/usr/tmp 已就绪"

# ---- 3. 端口核对 ------------------------------------------------------------
EXPECT_PORT="${SERVER_PORT:-$LIC_PORT}"
CUR_ENV_PORT=""
if [ -n "${SNPSLMD_LICENSE_FILE:-}" ]; then
  CUR_ENV_PORT=$(echo "$SNPSLMD_LICENSE_FILE" | sed -E 's/^([0-9]+)@.*/\1/')
fi
if [ -n "$CUR_ENV_PORT" ] && [ "$CUR_ENV_PORT" != "$EXPECT_PORT" ]; then
  warn "端口不一致：SNPSLMD_LICENSE_FILE=$SNPSLMD_LICENSE_FILE (端口 $CUR_ENV_PORT) vs license SERVER 端口 $EXPECT_PORT"
  warn "请把 shell 配置改成: export SNPSLMD_LICENSE_FILE=${EXPECT_PORT}@${MASTER_HOST}"
  die "请先修正端口后重跑。"
fi
ok "端口一致 ($EXPECT_PORT)"

# ---- 4. systemd 用户服务 + 开机自启 ----------------------------------------
mkdir -p "$SERVICE_DIR"
ADMIN_DIR="$(dirname "$(dirname "$LICENSE_FILE")")"   # .../admin，绝对且不含 ..
say "写入 systemd 用户服务: $SERVICE_FILE"
cat > "$SERVICE_FILE" <<EOF
[Unit]
Description=Synopsys FlexLM license server (lmgrd)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=$ADMIN_DIR
Environment=SNPSLMD_LICENSE_FILE=${EXPECT_PORT}@${MASTER_HOST}
ExecStart=$SCL_BIN/lmgrd -z -c $LICENSE_FILE -l $LOG_FILE
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
EOF

export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
systemctl --user daemon-reload
systemctl --user enable "$SERVICE_NAME" >/dev/null 2>&1
ok "systemctl --user enable ($SERVICE_NAME)"
if ! loginctl show-user "$(whoami)" -p Linger 2>/dev/null | grep -qi "Linger=yes"; then
  if loginctl enable-linger "$(whoami)" 2>/dev/null; then
    ok "enable-linger (未登录也启动)"
  else
    warn "enable-linger 需要 polkit/root，开机后需手动登录一次才会自启。"
  fi
fi

# 停掉可能以旧方式运行的手动 lmgrd 实例，再交给 systemd
pkill -x lmgrd 2>/dev/null || true
pkill -x snpslmd 2>/dev/null || true
sleep 1

systemctl --user restart "$SERVICE_NAME" >/dev/null 2>&1 || systemctl --user start "$SERVICE_NAME" >/dev/null 2>&1

# 等待稳定
for i in 1 2 3 4 5 6 7 8; do
  sleep 1
  if systemctl --user is-active "$SERVICE_NAME" | grep -q active; then break; fi
done
ACT=$(systemctl --user is-active "$SERVICE_NAME")
if [ "$ACT" != "active" ]; then
  die "服务未进入 active（当前: $ACT）。请查看: journalctl --user -u $SERVICE_NAME -n 50"
fi
ok "服务 active (running)"
systemctl --user is-enabled "$SERVICE_NAME" >/dev/null 2>&1 && ok "开机自启已启用 (enabled)"

# ---- 5. lmstat 验证 ---------------------------------------------------------
sleep 2
echo
say "=== lmstat 验证 ==="
"$SCL_BIN/lmutil" lmstat -c "${EXPECT_PORT}@${MASTER_HOST}" 2>&1 | grep -E "license server UP|snpslmd.*UP|SERVER" || {
  warn "lmstat 未显示 UP，请检查: journalctl --user -u $SERVICE_NAME -n 50"
  echo "日志文件: $LOG_FILE"
  exit 3
}
ok "License 服务器正常（$(grep -E 'license server UP' <("$SCL_BIN/lmutil" lmstat -c "${EXPECT_PORT}@${MASTER_HOST}" 2>/dev/null) | head -1)）"

echo
say "完成。日常命令："
echo "  systemctl --user status $SERVICE_NAME"
echo "  lmutil lmstat -c ${EXPECT_PORT}@${MASTER_HOST}"
