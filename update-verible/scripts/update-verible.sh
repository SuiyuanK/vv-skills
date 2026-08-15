#!/usr/bin/env bash

set -Eeuo pipefail

readonly REPOSITORY_URL="https://github.com/chipsalliance/verible.git"
readonly GITHUB_ROOT="https://github.com"
readonly EXPANDED_ASSETS_ROOT="https://github.com/chipsalliance/verible/releases/expanded_assets"
readonly INSTALL_DIR="/home/vv/.local/bin"
readonly BACKUP_ROOT="/home/vv/.local/share/verible-backups"
readonly TEMP_ROOT="/home/vv/TMP/tmp"
stage_dir=""

die() {
  printf '错误：%s\n' "$*" >&2
  exit 1
}

cleanup() {
  if [[ -n "$stage_dir" && -d "$stage_dir" ]]; then
    rm -rf -- "$stage_dir"
  fi
}
trap cleanup EXIT

usage() {
  cat <<'EOF'
Verible 安装与备份管理工具

用法：
  update-verible.sh

启动后通过菜单选择：
  1. 升级或重装 Verible
  2. 查看现有备份
  3. 清理旧备份
  4. 退出
EOF
}

choose_release() {
  local page=0 page_size=20 total start end index choice choice_num

  total="${#release_tags[@]}"
  ((total > 0)) || die "没有读取到 Verible Release"
  [[ -t 0 ]] || die "当前不是交互终端，请使用 upgrade <版本标签> 指定 Release"

  while true; do
    start=$((page * page_size))
    end=$((start + page_size))
    ((end > total)) && end="$total"

    printf '\nVerible Release（共 %d 个，第 %d/%d 页）：\n' \
      "$total" "$((page + 1))" "$(((total + page_size - 1) / page_size))"
    for ((index = start; index < end; index++)); do
      printf '  %4d) %s\n' "$((index + 1))" "${release_tags[index]}"
    done
    printf '\n输入序号选择；n 下一页；p 上一页；q 退出。\n'
    read -r -p '请选择：' choice

    case "$choice" in
      n|N)
        ((end < total)) && page=$((page + 1))
        ;;
      p|P)
        ((page > 0)) && page=$((page - 1))
        ;;
      q|Q)
        printf '已取消。\n'
        exit 0
        ;;
      ''|*[!0-9]*)
        printf '无效输入。\n' >&2
        ;;
      *)
        choice_num=$((10#$choice))
        if ((choice_num >= 1 && choice_num <= total)); then
          selected_release="${release_tags[choice_num - 1]}"
          return 0
        fi
        printf '序号超出范围。\n' >&2
        ;;
    esac
  done
}

get_backups() {
  local name
  backups=()
  [[ -d "$BACKUP_ROOT" ]] || return 0

  while IFS= read -r name; do
    backups+=("$BACKUP_ROOT/$name")
  done < <(
    find "$BACKUP_ROOT" -mindepth 1 -maxdepth 1 -type d \
      -regextype posix-extended -regex '.*/[0-9]{8}-[0-9]{6}' \
      -printf '%f\n' | sort -r
  )
}

list_backups() {
  local backup
  get_backups

  if ((${#backups[@]} == 0)); then
    printf '没有 Verible 备份。\n备份目录：%s\n' "$BACKUP_ROOT"
    return 0
  fi

  printf '现有 Verible 备份（新到旧）：\n'
  for backup in "${backups[@]}"; do
    printf '  %-15s  %s\n' "$(du -sh -- "$backup" | cut -f1)" "$backup"
  done
  printf '共 %d 份。\n' "${#backups[@]}"
}

clean_backups() {
  local keep="${1:-3}"
  local assume_yes="${2:-}"
  local answer backup
  local -a to_delete

  [[ "$keep" =~ ^[0-9]+$ ]] || die "保留数量必须是大于或等于 0 的整数"
  [[ -z "$assume_yes" || "$assume_yes" == "--yes" ]] || die "未知参数：$assume_yes"

  get_backups
  if ((${#backups[@]} <= keep)); then
    printf '无需清理：当前有 %d 份备份，设置保留 %d 份。\n' "${#backups[@]}" "$keep"
    return 0
  fi

  to_delete=("${backups[@]:keep}")
  printf '将保留最近 %d 份，并删除以下 %d 份旧备份：\n' "$keep" "${#to_delete[@]}"
  for backup in "${to_delete[@]}"; do
    printf '  %s  %s\n' "$(du -sh -- "$backup" | cut -f1)" "$backup"
  done

  if [[ "$assume_yes" != "--yes" ]]; then
    read -r -p '确认删除？请输入 y 继续：[y/N] ' answer
    [[ "$answer" == "y" || "$answer" == "Y" ]] || {
      printf '已取消，未删除任何备份。\n'
      return 0
    }
  fi

  for backup in "${to_delete[@]}"; do
    [[ "$backup" == "$BACKUP_ROOT"/[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]-[0-9][0-9][0-9][0-9][0-9][0-9] ]] \
      || die "拒绝删除不符合命名规则的目录：$backup"
    rm -rf -- "$backup"
  done

  printf '清理完成，删除了 %d 份旧备份。\n' "${#to_delete[@]}"
}

upgrade_verible() {
  local force=""
  local selected_release asset_path asset_name asset_url package part_file
  local current_version source_bin backup_dir binary answer
  local -a release_tags release_assets matching_assets roots new_binaries existing

  [[ "$(uname -m)" == "x86_64" ]] || die "本脚本只适用于 x86_64，当前架构为 $(uname -m)"
  command -v curl >/dev/null || die "找不到 curl 命令"
  command -v git >/dev/null || die "找不到 git 命令"
  command -v tar >/dev/null || die "找不到 tar 命令"
  command -v install >/dev/null || die "找不到 install 命令"

  mkdir -p "$TEMP_ROOT"
  stage_dir="$(mktemp -d --tmpdir="$TEMP_ROOT" verible-update.XXXXXXXX)"

  printf '正在读取 Verible 官方 Release 列表……\n'
  mapfile -t release_tags < <(
    git ls-remote --tags --refs "$REPOSITORY_URL" 'v0.0-*-g*' \
      | awk -F/ '{print $3}' \
      | sort -t- -k2,2nr -k3,3r -u
  )
  ((${#release_tags[@]} > 0)) || die "无法读取官方 Release 列表"

  choose_release

  current_version=""
  if [[ -x "$INSTALL_DIR/verible-verilog-lint" ]]; then
    current_version="$("$INSTALL_DIR/verible-verilog-lint" --version 2>/dev/null \
      | awk '$1 == "Version" {print $2; exit}')"
  fi

  printf '已安装版本：%s\n' "${current_version:-未安装}"
  printf '选择的 Release：%s\n' "$selected_release"

  if [[ "$current_version" == "$selected_release" ]]; then
    read -r -p '当前已经是所选版本，是否强制重装？[y/N] ' answer
    if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
      force="--force"
    else
      printf '已取消重装。\n'
      return 0
    fi
  fi

  printf '正在核对该 Release 的实际资产名称……\n'
  mapfile -t release_assets < <(
    curl -fsSL --retry 3 --connect-timeout 15 \
      "$EXPANDED_ASSETS_ROOT/$selected_release" \
      | grep -o 'href="[^"]*/download/[^"]*"' \
      | sed 's/^href="//; s/"$//'
  )
  ((${#release_assets[@]} > 0)) || die "该标签没有可读取的 GitHub Release 资产"

  printf '官方 Release 资产：\n'
  matching_assets=()
  for asset_path in "${release_assets[@]}"; do
    asset_name="${asset_path##*/}"
    printf '  %s\n' "$asset_name"
    [[ "$asset_name" == *-linux-static-x86_64.tar.gz ]] && matching_assets+=("$asset_path")
  done
  ((${#matching_assets[@]} == 1)) \
    || die "应恰好匹配一个 Linux x86_64 静态包，实际为 ${#matching_assets[@]} 个"

  asset_path="${matching_assets[0]}"
  asset_name="${asset_path##*/}"
  asset_url="$GITHUB_ROOT$asset_path"
  package="$stage_dir/$asset_name"
  part_file="$package.part"

  printf '正在从官方 GitHub 下载：\n  %s\n' "$asset_url"
  curl -fL --retry 3 --retry-delay 2 --connect-timeout 15 \
    --progress-bar -o "$part_file" "$asset_url" \
    || die "下载安装包失败"
  mv -- "$part_file" "$package"

  tar -tzf "$package" >/dev/null || die "压缩包损坏或格式不正确"

  if tar -tzf "$package" | grep -Eq '(^/|(^|/)\.\.(/|$))'; then
    die "压缩包包含不安全路径，已停止"
  fi

  mapfile -t roots < <(tar -tzf "$package" | awk -F/ 'NF {print $1}' | sort -u)
  ((${#roots[@]} == 1)) || die "压缩包应只有一个顶层目录"

  tar -xzf "$package" -C "$stage_dir"
  source_bin="$stage_dir/${roots[0]}/bin"
  [[ -d "$source_bin" ]] || die "压缩包中缺少 bin 目录"
  [[ -x "$source_bin/verible-verilog-lint" ]] || die "压缩包中缺少 verible-verilog-lint"

  mapfile -d '' new_binaries < <(find "$source_bin" -maxdepth 1 -type f -name 'verible-*' -print0 | sort -z)
  ((${#new_binaries[@]} > 0)) || die "没有找到 Verible 可执行文件"

  printf '新版本信息：\n'
  "$source_bin/verible-verilog-lint" --version

  shopt -s nullglob
  mkdir -p "$INSTALL_DIR" "$BACKUP_ROOT"
  existing=("$INSTALL_DIR"/verible-*)
  if ((${#existing[@]} > 0)); then
    backup_dir="$BACKUP_ROOT/$(date +%Y%m%d-%H%M%S)"
    mkdir -p "$backup_dir"
    cp -a -- "${existing[@]}" "$backup_dir/"
    printf '旧版本备份：%s\n' "$backup_dir"
  fi

  for binary in "${new_binaries[@]}"; do
    install -m 0755 -- "$binary" "$INSTALL_DIR/$(basename "$binary")"
  done

  printf '\n升级完成，共安装 %d 个命令。\n' "${#new_binaries[@]}"
  printf '当前版本：\n'
  "$INSTALL_DIR/verible-verilog-lint" --version
  printf '命令位置：%s\n' "$INSTALL_DIR/verible-verilog-lint"
}

interactive_clean_backups() {
  local keep

  read -r -p '要保留最近几份备份？[默认 3] ' keep
  keep="${keep:-3}"
  [[ "$keep" =~ ^[0-9]+$ ]] || {
    printf '输入无效：请输入大于或等于 0 的整数。\n' >&2
    return 0
  }
  clean_backups "$keep"
}

pause_menu() {
  printf '\n'
  read -r -p '按 Enter 返回主菜单……' _
}

main_menu() {
  local choice

  while true; do
    printf '\nVerible 安装与备份管理工具\n'
    printf '  1) 升级或重装 Verible\n'
    printf '  2) 查看现有备份\n'
    printf '  3) 清理旧备份\n'
    printf '  4) 退出\n\n'

    read -r -p '请选择：[1-4] ' choice || {
      printf '\n已退出。\n'
      return 0
    }

    case "$choice" in
      1)
        upgrade_verible
        pause_menu
        ;;
      2)
        list_backups
        pause_menu
        ;;
      3)
        interactive_clean_backups
        pause_menu
        ;;
      4|q|Q)
        printf '已退出。\n'
        return 0
        ;;
      *)
        printf '无效选择，请输入 1、2、3 或 4。\n' >&2
        ;;
    esac
  done
}

if (($# > 0)); then
  case "$1" in
    -h|--help|help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      die "全交互模式不接受命令行参数"
      ;;
  esac
fi

main_menu
