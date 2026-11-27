#!/usr/bin/env bash

set -Eeuo pipefail

readonly SYSTEM_DESKTOP="/usr/share/applications/chatgpt.desktop"
readonly SYSTEM_LAUNCHER="/usr/bin/chatgpt"
readonly TEMP_ROOT="/home/vv/TMP/tmp"
readonly CHROME_DESKTOP="google-chrome.desktop"

die() {
  printf '错误：%s\n' "$*" >&2
  exit 1
}

if ((EUID == 0)); then
  die "请以普通用户运行，不要使用 sudo"
fi

readonly USER_HOME="${HOME:?无法确定用户主目录}"
readonly USER_BIN="$USER_HOME/.local/bin"
readonly USER_APPS="$USER_HOME/.local/share/applications"
readonly WRAPPER="$USER_BIN/chatgpt-html-fix"
readonly USER_DESKTOP="$USER_APPS/chatgpt.desktop"

[[ -x "$SYSTEM_LAUNCHER" ]] || die "找不到 Codex/ChatGPT 启动命令：$SYSTEM_LAUNCHER"
[[ -f "$SYSTEM_DESKTOP" ]] || die "找不到系统桌面启动器：$SYSTEM_DESKTOP"
command -v xdg-mime >/dev/null || die "找不到 xdg-mime"
command -v update-desktop-database >/dev/null || die "找不到 update-desktop-database"

mkdir -p "$TEMP_ROOT" "$USER_BIN" "$USER_APPS"
work_dir="$(mktemp -d --tmpdir="$TEMP_ROOT" codex-html-fix.XXXXXXXX)"
cleanup() {
  rm -rf -- "$work_dir"
}
trap cleanup EXIT

cat >"$work_dir/chatgpt-html-fix" <<'EOF'
#!/usr/bin/env bash

set -u

readonly CHROME_DESKTOP="google-chrome.desktop"

# Codex 启动时可能重新注册 MIME。后台检查 15 秒，发现 HTML
# 默认程序被改变就立即恢复 Chrome。
(
  for ((attempt = 1; attempt <= 15; attempt++)); do
    sleep 1
    current="$(xdg-mime query default text/html 2>/dev/null || true)"
    if [[ "$current" != "$CHROME_DESKTOP" ]]; then
      xdg-mime default "$CHROME_DESKTOP" text/html
    fi
  done
) >/dev/null 2>&1 &

exec /usr/bin/chatgpt "$@"
EOF

awk -v wrapper="$WRAPPER" '
  BEGIN { replaced = 0 }
  /^Exec=/ && replaced == 0 {
    print "Exec=" wrapper " %U"
    replaced = 1
    next
  }
  { print }
  END {
    if (replaced == 0) exit 2
    print "X-Codex-Html-Fix=true"
  }
' "$SYSTEM_DESKTOP" >"$work_dir/chatgpt.desktop" \
  || die "生成用户级桌面启动器失败"

if [[ -f "$USER_DESKTOP" ]] && ! grep -qx 'X-Codex-Html-Fix=true' "$USER_DESKTOP"; then
  backup="$USER_DESKTOP.backup-$(date +%Y%m%d-%H%M%S)"
  cp -a -- "$USER_DESKTOP" "$backup"
  printf '已备份原用户启动器：%s\n' "$backup"
fi

install -m 0755 -- "$work_dir/chatgpt-html-fix" "$WRAPPER"
install -m 0644 -- "$work_dir/chatgpt.desktop" "$USER_DESKTOP"
update-desktop-database "$USER_APPS"

xdg-mime default "$CHROME_DESKTOP" text/html

actual_exec="$(awk -F= '/^Exec=/{print substr($0, 6); exit}' "$USER_DESKTOP")"
actual_mime="$(xdg-mime query default text/html 2>/dev/null || true)"

[[ "$actual_exec" == "$WRAPPER %U" ]] || die "桌面启动器验证失败：$actual_exec"
[[ "$actual_mime" == "$CHROME_DESKTOP" ]] || die "HTML 默认程序验证失败：$actual_mime"

printf '\n配置完成。\n'
printf '包装启动器：%s\n' "$WRAPPER"
printf '桌面启动器：%s\n' "$USER_DESKTOP"
printf 'HTML 默认程序：%s\n' "$actual_mime"
printf '\n请从任务栏取消固定旧图标，再从应用菜单重新固定 ChatGPT/Codex。\n'
