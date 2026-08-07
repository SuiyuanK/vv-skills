# 排查过程记录

本文记录一次真实排查：Synopsys license 配置已写入 `.zshrc`/`.bashrc`，但 `lmstat` 报连接失败，最终定位到三层根因并修复。供后续遇到类似问题时对照。

## 初始症状

用户在 `~/.zshrc` 里配置了：

```bash
export SNPSLMD_LICENSE_FILE=27080@vv-ubuntu
export SCL_HOME=/opt/eda/Synopsys/scl/2024.06
export PATH=$PATH:$SCL_HOME/linux64/bin
export VCS_ARCH_OVERRIDE=linux
```

但运行：
```bash
lmstat -c $SNPSLMD_LICENSE_FILE
```
报：
```
Error getting status: Cannot connect to license server system. (-15,570:115 "Operation now in progress")
```

## 诊断步骤与发现

### 1) 先确认"配置有没有加载、工具在不在 PATH"

```bash
echo "$SNPSLMD_LICENSE_FILE $SCL_HOME $VCS_ARCH_OVERRIDE"
command -v lmstat lmutil snpslmd lmgrd
```
- 如果 `echo` 出来的值和 `.zshrc` 不一致（比如当前 shell 显示 `27000@vv-ubuntu` 而文件写 `27080`）→ 说明当前交互 shell 没加载 `.zshrc`（可能是非交互或由 IDE/别名层启动），需 `source ~/.zshrc` 或新开终端。
- 工具在 PATH 里能找到 → 工具链 OK。

### 2) 核心疑点：端口不一致

对比环境变量端口 与 license 文件 `SERVER` 行端口：

```bash
grep -E "^SERVER" /opt/eda/Synopsys/scl/2024.06/admin/license/synopsys.lic
# SERVER vv-ubuntu 644ed7097462 27000   <- 端口是 27000
```
`.zshrc` 里写的是 `27080`，而 server 监听 `27000` → **端口不匹配**。改成 `27000@vv-ubuntu` 后与 license 对齐。

> 小坑：当前 shell 里 `SNPSLMD_LICENSE_FILE` 显示 `27000` 而文件写 `27080`，这种不一致多见于非交互 shell 用了全局默认值或别处 export；以 `~/.zshrc` 为准并重新加载即可。

### 3) hostid 校验

```bash
lmutil lmhostid
# FlexNet host ID of this machine is "7413eaff5776 644ed7097462"
```
license `SERVER` 行的 hostid `644ed7097462` 在列 → 匹配，license 文件对本机有效。

### 4) `/usr/tmp` 缺失 → lmgrd 起不来

手动前台启动 lmgrd，日志停在：
```
(lmgrd) SLOG: Summary LOG statistics is enabled.
(lmgrd) Can't make directory /usr/tmp/.flexlm, errno: 2(No such file or directory)
(lmgrd) Failed to open the TCP port number in the license.
```
`/usr/tmp` 不存在且 `/usr` 不可写（root 所有）。用 `strings` 验证 lmgrd 硬编码了这个路径：
```bash
strings .../linux64/bin/lmgrd | grep -i flexlm   # -> /usr/tmp/.flexlm
```
**结论**：`/usr/tmp/.flexlm` 是编译期写死的，没有环境变量可改。必须创建 `/usr/tmp`。

修复：
```bash
sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp
```
创建后（`drwxrwxrwt root root`），lmgrd 能成功创建 `/usr/tmp/.flexlm`。

### 5) lmgrd daemonize 与 systemd `Type=simple` 冲突

- 手动后台 `&` 启动 lmgrd 能正常常驻（27000 监听、`lmstat` UP）。
- 但用 systemd **`Type=simple`** 启动，服务立刻 `inactive (dead)`，即使实际守护进程被 reparent 到 systemd user manager（PID 观察：lmgrd 守护进程 ppid 是 systemd user manager 4419）。
- 根因：`lmgrd` 默认 **daemonize**（fork 出守护进程后父进程退出），systemd 认为主进程退出即服务死亡。
- 尝试 `Type=forking` 时又遇到 `Failed to open the TCP port number in the license` + 退出码 35（端口/重启时序问题）。
- **最终方案**：给 lmgrd 加 **`-z`**（前台运行，不 daemonize）+ systemd `Type=simple`：
  ```
  lmgrd -z -c ...synopsys.lic -l ...lmgrd.log
  ```
  服务进入 `active (running)`，Main PID 就是 lmgrd，systemd 正确跟踪，27000 监听。

## 最终配置

`~/.config/systemd/user/synopsys-lic.service`（`Type=simple` + `-z`，见 SKILL.md）。启用：

```bash
export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user daemon-reload
systemctl --user enable synopsys-lic.service
loginctl enable-linger vv
systemctl --user start synopsys-lic.service
```

验证输出：
```
Active: active (running)
Main PID: ... (lmgrd)
lmstat: vv-ubuntu: license server UP (MASTER) v11.19.6
        snpslmd: UP v11.19.6
```

## 关键命令行速查

| 目的 | 命令 |
|---|---|
| 看环境变量 / 工具 | `echo $SNPSLMD_LICENSE_FILE` ; `command -v lmgrd` |
| 看 license SERVER 行 | `grep ^SERVER synopsys.lic` |
| hostid | `lmutil lmhostid` |
| 建 /usr/tmp | `sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp` |
| lmgrd 前台启动 | `lmgrd -z -c synopsys.lic -l lmgrd.log` |
| 验证服务器 | `lmutil lmstat -c 27000@vv-ubuntu` |
| 服务自启确认 | `systemctl --user is-enabled synopsys-lic.service` ; `loginctl show-user vv -p Linger` |
