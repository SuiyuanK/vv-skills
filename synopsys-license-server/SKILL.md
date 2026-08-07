---
name: synopsys-license-server
description: >-
  Diagnose and fix a Synopsys (VCS/Verdi/DC etc.) license setup where the
  environment is configured (.zshrc/.bashrc export SNPSLMD_LICENSE_FILE,
  SCL_HOME, PATH) but lmstat reports "Cannot connect to license server
  system. (-15,570:115 'Operation now in progress')", or lmgrd exits with
  "Can't make directory /usr/tmp/.flexlm", or the systemd license service
  immediately dies. Covers port mismatch, missing /usr/tmp, the lmgrd -z
  foreground flag, hostid check, and systemd user-service auto-start.
  Use when VCS/DVE/DC cannot obtain a license on a local or remote
  license server.
---

# Synopsys License 配置未生效 修复（VCS/Verdi/DC）

## 适用场景 (When to use)

- Synopsys 工具（VCS、Verdi、Design Compiler 等）**配置已写入 `~/.zshrc` / `~/.bashrc`**（`SNPSLMD_LICENSE_FILE`、`SCL_HOME`、`PATH` 等已 export），但运行 `lmstat -c $SNPSLMD_LICENSE_FILE` 报：
  ```
  Cannot connect to license server system. (-15,570:115 "Operation now in progress")
  ```
- `lmgrd` 启动即退出，日志报：
  ```
  (lmgrd) Can't make directory /usr/tmp/.flexlm, errno: 2(No such file or directory)
  ```
- 装了 Synopsys license 服务器但本机/客户端连不上 license，或重启后 license 服务不在了。
- 想为 license 服务配置 **systemd 开机自启动**，但服务 `active` 一下立刻变 `dead`。

## 症状 (Symptoms)

1. `lmstat -c $SNPSLMD_LICENSE_FILE` → `-15,570:115 "Operation now in progress"`（连不上服务器）。
2. `lmgrd -c synopsys.lic -l lmgrd.log` 跑几秒就退出，`.flexlm` 相关日志报 `Can't make directory /usr/tmp/.flexlm`。
3. systemd 用 `Type=simple` 启动 lmgrd 后状态是 `inactive (dead)` / `activating (auto-restart)`，进程和 27000 端口都没了。
4. 直接跑 `lmutil lmstat -a` 也报同样连接错误。

## 根因 (Root cause)

一个"配置没生效"通常有 **三层根因**，逐层排查：

### ① 环境变量端口 ≠ license 文件端口（最容易被忽略）
- `.zshrc` 里可能要 `export SNPSLMD_LICENSE_FILE=27080@vv-ubuntu`，而 license 文件的 `SERVER` 行写的是：
  ```
  SERVER vv-ubuntu <hostid> 27000
  ```
- 端口不一致 → 客户端去连 27080，而服务器监听 27000 → 连不上。
- **修复**：让两者端口一致（要么改 `.zshrc` 里的端口，要么改 `SERVER` 行端口）。

### ② `/usr/tmp` 目录缺失（lmgrd 硬编码依赖）
- `lmgrd` 把运行状态临时目录**硬编码**为 `/usr/tmp/.flexlm`（二进制字符串里写死，**无环境变量可改**）。
- 很多 Linux 发行版没有 `/usr/tmp` 目录，且 `/usr` 通常 root 所有、普通用户不可写 → lmgrd 报 `Can't make directory /usr/tmp/.flexlm` 并退出。
- 这是 **Synopsys Linux 部署的标准前置步骤**。
- **修复**（需 sudo，因为 `/usr` 不可写）：
  ```bash
  sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp
  ```

### ③ lmgrd 默认 daemonize，与 systemd `Type=simple` 冲突
- `lmgrd` **默认把自己放到后台**（fork 出守护进程后父进程退出）。
- systemd `Type=simple` 认为主进程退出即服务死亡 → 立刻判 `dead`，即使实际守护进程还在跑（或整个服务被清理）。
- 日志往往在 `SLOG: Summary LOG statistics is enabled.` 之后戛然而止。
- **修复**：给 lmgrd 加 **`-z`** 让它**前台运行**，配合 `Type=simple`，systemd 就能正确跟踪。

## 修复 (Fix)

直接跑本 skill 附带的**幂等脚本**（可重复执行）：

```bash
bash scripts/setup_synopsys_license.sh
```

脚本做以下事情：
1. 校验 **hostid**：`lmutil lmhostid` 列出的 hostid 是否包含 license `SERVER` 行的 hostid（`644ed7097462` 之类）。
2. 检测 `/usr/tmp` 缺失 → 打印 `sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp` 让用户执行（脚本不静默 sudo）。
3. 打印/核对 `SNPSLMD_LICENSE_FILE` 端口 与 license `SERVER` 行端口是否一致（默认 27000）。
4. 生成 systemd 用户服务单元（`-z` + `Type=simple`）到 `~/.config/systemd/user/synopsys-lic.service`，`daemon-reload` → `enable` → `loginctl enable-linger` → `start`。
5. 用 `lmutil lmstat -c 27000@vv-ubuntu` 验证 `license server UP (MASTER)` / `snpslmd UP`。

### 手动等价命令（不想用脚本时）

**Step 1 — 先确认 hostid 匹配**（不匹配则 license 服务器起不来）：
```bash
lmutil lmhostid
# 应看到 license 文件 SERVER 行里的 hostid（如 644ed7097462）
```

**Step 2 — 确保 `/usr/tmp` 存在**（缺则 lmgrd 必失败）：
```bash
sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp
```

**Step 3 — 手动前台启动（验证能否跑起来）**：
```bash
cd /opt/eda/Synopsys/scl/2024.06/admin
nohup ./linux64/bin/lmgrd -z -c \
  /opt/eda/Synopsys/scl/2024.06/admin/license/synopsys.lic \
  -l /opt/eda/Synopsys/scl/2024.06/admin/logs/lmgrd.log >/dev/null 2>&1 &
```

**Step 4 — 配置 systemd 开机自启**（`~/.config/systemd/user/synopsys-lic.service`）：
```ini
[Unit]
Description=Synopsys FlexLM license server (lmgrd)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/eda/Synopsys/scl/2024.06/admin
Environment=SNPSLMD_LICENSE_FILE=27000@vv-ubuntu
ExecStart=/opt/eda/Synopsys/scl/2024.06/linux64/bin/lmgrd -z -c /opt/eda/Synopsys/scl/2024.06/admin/license/synopsys.lic -l /opt/eda/Synopsys/scl/2024.06/admin/logs/lmgrd.log
Restart=on-failure
RestartSec=3

[Install]
WantedBy=default.target
```
然后：
```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user daemon-reload
systemctl --user enable synopsys-lic.service   # 开机自启
loginctl enable-linger $(whoami)               # 未登录也启动（linger）
systemctl --user start synopsys-lic.service
```

## 验证 (Verification)

```bash
# 1. 服务在跑、255 监听
systemctl --user status synopsys-lic.service      # Active: active (running)
ss -ltn | grep 27000                              # LISTEN

# 2. license 服务器确认 UP
lmutil lmstat -c 27000@vv-ubuntu
# 期望： vv-ubuntu: license server UP (MASTER) v11.19.x
#         snpslmd: UP v11.19.x

# 3. 开机自启确认
systemctl --user is-enabled synopsys-lic.service  # enabled
loginctl show-user vv -p Linger                   # Linger=yes

# 4. 客户端不再报 -15,570
lmstat -c $SNPSLMD_LICENSE_FILE
# 不再出现 "Cannot connect to license server system. (-15,570:115 ...)"
```

## 注意事项 (Notes)

- **端口一致性第一**：`SNPSLMD_LICENSE_FILE` 里的端口必须等于 `SERVER` 行端口。两者都要核。
- **`/usr/tmp` 是硬前置**：缺它 lmgrd 一定失败；且 `/usr` 不可写，必须 sudo。创建后设 `1777`（sticky，同 `/tmp`）。
- **`-z` 是 systemd 平稳运行的关键**：不加 `-z`，systemd `Type=simple` 会因 lmgrd daemonize 判服务死亡。同样，用 `Type=forking` 可能遇到 `Failed to open the TCP port number in the license`（端口/时序问题），`-z` + `Type=simple` 最稳。
- **开机自启用 systemd 用户服务 + linger**：能在你尚未登录（登录界面）时就启动服务。
- **`restart` 的小时序坑**：`systemctl --user restart` 时旧实例刚停、端口可能处于 `TIME_WAIT`，短暂显示 `activating` 属正常，`Restart=on-failure` 会自动重试到 `running`；冷启动无此现象。
- **hostid mismatch**：若 `lmutil lmhostid` 里没有 license `SERVER` 行的 hostid，需在该机器上重新生成/获取匹配的 license，否则 `lmgrd` 起不来。
- **license 文件可能是 CRLF 行尾**：`.lic` 常由 Windows 生成、带 `\r\n`。用 `grep/awk` 解析 `SERVER`/`INCREMENT` 行时末尾会带 `\r`（如端口 `27000\r`），导致字符串比较/脚本判断出错。脚本里已用 `tr -d '\r'` 处理；手写脚本时留意（用 `cat -A` 或 `xxd` 检查）。
- **systemd 单元 `WorkingDirectory` 必须规范化**：不能含 `..`（systemd 报 `path is not normalized` 直接拒启动）。脚本已用 `dirname` 解析出绝对路径。

## 参考文件

- `scripts/setup_synopsys_license.sh` — 幂等安装/自启配置脚本
- `references/diagnosis.md` — 完整排查过程记录（症状、根因、诊断命令、验证方法）
