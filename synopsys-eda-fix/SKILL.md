---
name: synopsys-eda-fix
description: >-
  Diagnose and fix Synopsys X-2025.06 EDA tools (VCS, Verdi, DC/syn, LC,
  SpyGlass, SCL 2025.03) on Linux Mint 22.3 (Ubuntu 24.04 base, glibc 2.39)
  with Linux kernel 7.0.0. Covers the vendor-script shebang fix (230 scripts to
  #!/bin/bash -h while /bin/sh stays dash), VCS --as-needed linker undefined-reference crash,
  SpyGlass "Unknown platform Linux-7" detection failure, LC exit segfault
  (glibc 2.39 malloc interposition), Verdi verdi_supp post-install failure,
  and FlexLM lmgrd/snpslmd license setup (/usr/tmp, CRLF, systemd). Use when
  a Synopsys tool crashes, fails to launch, or can't obtain a license on this
  system.
---

# Synopsys X-2025.06 EDA 工具在 Mint 22.3 / 内核 7 上的修复

## 适用范围

- x86_64，Linux Mint 22.3（Ubuntu 24.04 底，glibc 2.39），Linux 内核 **7.0.0**。
- Synopsys **X-2025.06**：VCS、Verdi、DC(syn)、LC、SpyGlass、SCL 2025.03。
- 安装根：`/opt/EDA/Synopsys/`。

> 其它发行版/内核/版本不要模糊套用。核心难点是：这些工具是在较老的 RHEL 上编译的，
> 跑在「新 glibc 2.39 + 内核 7」上会有 wrapper Bashism、内核版本识别不全、内存分配器
> 不兼容三类问题。
> 注：License（第 7 节）与 Verdi 老 ABI 依赖（第 8 节）在 **CachyOS（Arch，`/bin/sh -> bash`）**
> 上亦按同样流程验证通过（内核同为 7.x）。

## 修复总览（速查）

| 工具 | 症状 | 修复 |
|---|---|---|
| 全部 | `#!/bin/sh -h` 脚本报 `Illegal option -h` | 改脚本 shebang 为 `#!/bin/bash -h` |
| 全部 | `snps_platform: 无法执行` | 装 `csh` |
| VCS | 链接 `undefined reference to vfs_fopen/snps_mem_*` | `-LDFLAGS "-Wl,--no-as-needed"` |
| VCS | 启动刷「语法错误」OS 检测噪音 | `VCS_ARCH_OVERRIDE=linux` |
| Verdi | `verdi_supp` post_install 报 home 不对 | 补跑 post_install 加 `-verdi_home` |
| LC | 退出时 segfault（工作已完成） | 包装脚本屏蔽报错 + 返回 0 |
| SpyGlass | `Unknown platform: Linux-7.0.0-…` | 3 个脚本内核判断加 `Linux-7*` |
| 全部 | license 连不上 / 服务起不来 | lmgrd 必须 `-c <licfile>`（不带会死循环）+ `/usr/tmp` + CRLF + `Type=simple`+`-z` |

---

## 1. 通用前置

### 1.1 改脚本 shebang 为 `#!/bin/bash -h`（最重要，一次修好 230 个脚本）

Synopsys 有约 **230 个脚本** shebang 写成 `#!/bin/sh -h`，其中 `-h` 是 bash 专有参数。
Mint/Ubuntu 的 `/bin/sh` 默认是 dash，dash 不认 `-h` → 直接 `Illegal option -h` 退出。

**修正方案：不改系统 `/bin/sh`（保持 dash），把这 230 个脚本首行统一改为
`#!/bin/bash -h`**，直接经 bash 解释，完全绕开 `/bin/sh` 指向哪种 shell。
这样不动系统默认 shell，不影响其它软件的依赖语义，也便于整套流程在其他机器/CI 上复现。

**批量修改**（脚本目录属主为当前用户，无需 sudo；改前先备份清单 tar）：
```bash
grep -rl '^#! */bin/sh *-h' /opt/EDA/Synopsys/ | while read f; do
  mode=$(stat -c %a "$f")
  sed -i '1s|^#!.*|#!/bin/bash -h|' "$f"
  chmod "$mode" "$f"
done
```

230 个文件分布在：`vcs/*/bin`（含 dpo/cso/vcfca/auxx/seq 共 71）、
`verdi/*/platform/verdi_supp/*/bin`（67，含 linux/linux64）、
`ufe_optional_spyglass-vcs/*/SPYGLASS_HOME/lib/multi-vcst/*`（76，vcs-mx/hector/auxx/seq）。
vcs/verdi/spyglass 三套的 bin 都要覆盖，不然 `vcs -id`、`verdi_supp` post_install 仍会报
`Illegal option -h`。

除上述 230 个 `#!/bin/sh -h` 外，还有约 **39 个 `#!/bin/sh`（不带 -h）的脚本实际用了
bash 特性**（`[[`、`==` 等），它们同样依赖 `/bin/sh` 是 bash，也要统一改为
`#!/bin/bash -h`。典型：verdi `bin/.wrapper`（`verdi` 入口是指向其的软链）、
spyglass `bin/spyglass`、`spyglass_main`、`scmbrowser`、`spyon`、`ugo`、
`scm_process_new`、`kdb_only_indp.sh` 等。

判定要点：

- `dash -n`（静态语法检查）抓不到 `[[`——dash 把它当普通命令，语法合法、运行时才报
  `/bin/sh: NN: [[: not found`。别只信 dash -n。
- 可靠判法：`dash -n` 失败 **且** `bash -n` 通过 → 真 bash 脚本（37/39）；
  运行时报 `[[: not found` 的入口（spyglass 两套 `bin/spyglass`）直接补。
- tcllib `tk8.4/.../configure`、Tcl demo 等 **两者都不通过**（不是 shell 语法），不要改。

`verdi` 入口是软链（`bin/verdi -> .wrapper`），改 `.wrapper` 一层即可覆盖。

验证：
```bash
ls -l /bin/sh        # 应仍是 -> dash（系统默认，不用改）
grep -rl '^#! */bin/sh *-h' /opt/EDA/Synopsys/ | wc -l   # 应为 0
```

### 1.2 装 csh（`snps_platform` 是 csh 脚本）

dc_shell / lc_shell 启动时会调 `snps_platform`（`#!/bin/csh -f`），缺 csh 会报
`snps_platform: 无法执行：找不到需要的文件`（非致命，但建议装）：
```bash
sudo apt install csh
```

### 1.3 不需要的包（避免白装）

- `lsb-core`、`libncurses5`（提供 libncurses.so.5）在 Ubuntu 24.04 已移除；但 LC **自带**
  `libncurses.so.5`/`libtinfo.so.5`（在 `lc/…/shlib/` 下，ldd 能解析到），VCS/DC 根本不依赖 ncurses，
  所以**不需要**系统装这两个包。

---

## 2. VCS

### 2.1 链接崩溃（undefined reference）—— `--as-needed` 问题

编译报：
```
/usr/bin/ld: …/libvcsnew.so: undefined reference to `vfs_fopen'
/usr/bin/ld: …/libvcsnew.so: undefined reference to `snps_mem_realloc'
```
**根因**：Ubuntu/Mint 链接器默认 `--as-needed`，而 VCS 生成的链接命令把**定义**这些符号的
`-lsnpsmalloc -lvfs` 排在**引用**它们的 `-lvcsnew` **之前**，前面两个库被提前丢弃。

**修复**：给 vcs 传 `-LDFLAGS "-Wl,--no-as-needed"`（**必须空格形式**，`=` 形式 vcs 不认）：
```bash
vcs -full64 -sverilog -LDFLAGS "-Wl,--no-as-needed" -o simv xxx.v
```
永久化（`.zshrc` 别名）：
```zsh
alias vcs='vcs -LDFLAGS "-Wl,--no-as-needed"'
```

### 2.2 OS 检测噪音

VCS 不认 Mint（只认 Ubuntu/Debian/SUSE/RHEL），启动刷「语法错误」警告。加：
```zsh
export VCS_ARCH_OVERRIDE=linux
```
强制走通用 `linux` 目标（x86_64 下 `-full64` 映射到 `linux64`），跳过 OS 探测。

### 2.2.5 别名会被 `make` 绕过——必须让 wrapper 在 PATH 上

**坑（已踩）**：别名对它生效的**交互式终端**有效，但 `make` 等**不做别名展开**的程序
按 `PATH` 查找 `vcs`。默认 PATH 里 `/opt/EDA/Synopsys/vcs/X-2025.06/bin` 在各 Synopsys
同名目录之前，会命中真身 `/…/vcs/bin/vcs`，绕过 wrapper → 复现 `--as-needed` 链接崩溃。

修法：把 wrapper 脚本（`~/.local/bin/vcs`）放到 PATH **最前面**。由于 zsh 里各 Synopsys
工具会把自身 bin `/prepend`，必须**在 PATH 断言之后**再前置一次 `~/.local/bin`。实际做法
是把它放在 `~/.zshrc` **最末尾**的「最终 PATH 断言」块里，保证任何后续插入都不推翻：

```zsh
# 放在 ~/.zshrc 最末尾（source 完 oh-my-zsh 及各 EDA 之后）
export PATH="$HOME/.local/bin:$PATH"
```

这样 `~/.local/bin` 总是排第一，连 `make` 也命中 wrapper。`~/.local/bin/vcs` 内容同前
（见下）；LC 的 `~/.local/bin/lc_shell` wrapper 同理。

**验证**：新开 zsh，`unalias vcs; for d in $(echo $PATH|tr ':' $'\n'); do [ -e "$d/vcs" ] && { echo $d; break; }; done`
应输出 `~/.local/bin/vcs`（不是 `/opt/…/vcs/bin/vcs`）。

### 2.3 完整 VCS 环境变量

```zsh
export VCS_ARCH_OVERRIDE=linux
export VCS_HOME=/opt/EDA/Synopsys/vcs/X-2025.06
export PATH=$VCS_HOME/bin:$PATH
# 别名只管交互式；make 等按 PATH 直取 vcs。务必把 wrapper 放 PATH 首位（见 2.2）。
alias vcs='vcs -LDFLAGS "-Wl,--no-as-needed"'
```
（alias `=vcs 'vcs ...'` 旧写法仍然有用，但它只解决交互式。若只要 wrapper 全场景生效，
改用它做：`alias vcs='~/.local/bin/vcs'` + PATH 前置 wrapper。）

---

## 3. Verdi

### 3.1 verdi_supp post_install 失败

Verdi 本身干净；但 `verdi_supp`（Verdi 补充包）安装时 post_install 脚本因 `-verdi_home`
为空 + `vcs -id` 拿不到版本而失败，报 `The Verdi Supplementary home is not correct`。
后果：`verdi_supp` 没被移进 `verdi/platform/`，也没建软链。

**修复**（等 VCS、Verdi、license 都就位后补跑）：
```bash
cd /opt/EDA/Synopsys/verdi_supp/X-2025.06/etc
bash ./post_install.sh \
  -r "/opt/EDA/Synopsys/vcs/X-2025.06" \
  -plat "aarch64 linux64 linux" \
  -install_verdi_supp "Yes" \
  -verdi_home "/opt/EDA/Synopsys/verdi/X-2025.06"
```
成功标志：`[VERDI SUPPLEMENTARY INSTALL] Completed !!!`。脚本会把 `verdi_supp` 整体移进
`verdi/platform/verdi_supp` 并在 aarch64/linux64/linux 三个平台建 `vcs` 软链（正常行为）。

> 注意：若 `vcs -id` 报 `/bin/sh: 0: Illegal option -h`，说明还有脚本没改成
> `#!/bin/bash -h`，按 1.1 补齐即可。

---

## 4. DC (syn) / Design Compiler

无需额外修复（做 1.1 的 shebang 修正和 1.2 的 csh 后即可用）。
`dc_shell -f script.tcl` 批处理 `read_file -format verilog` + `elaborate` + `link` 正常。
唯一无害噪音：`cat: /etc/upstream-release: 是一个目录`（Mint 上该路径是目录，脚本
`cat /etc/*-release` 撞到，不影响）。用现代 `read_file -format verilog`，别用旧 `read_verilog`。

---

## 5. LC / Library Compiler —— 退出 segfault（glibc 2.39）

**症状**：`read_lib` + `write_lib` 都成功、`.db` 正确产出，但退出时：
```
Fatal: Internal system error, cannot recover.
Error code=11  (SIGSEGV)
```
（有时是 `Segmentation fault … Bad read from 0x0` + stack trace，多种格式、非确定。）

**根因**（gdb 确认）：崩溃在 `exit()` 的 atexit 清理处理器里（LC 自己的混淆函数），是
glibc 2.39 改了 malloc/free 符号插桩，与 LC 的自定义分配器 `snpsmalloc` 不兼容。换系统
libstdc++ 无用（只是 139→1），无干净公开解法。

**务实修复**：用包装脚本屏蔽报错 + 返回 0（`.db` 产出不受影响）。见 `scripts/lc_shell_wrapper.sh`，
装到 `~/.local/bin/lc_shell`，并在 `.zshrc` 加 `alias lc_shell='~/.local/bin/lc_shell'`
（因为原 PATH 里 LC 的 bin 排在 `~/.local/bin` 前，不加别名会命中真身）。

---

## 6. SpyGlass —— Unknown platform Linux-7

**症状**：`spyglass` 启动即报：
```
ERROR(perl): Unknown platform: Linux-7.0.0-28-generic
spyglass: INTERNAL-ERROR … Perl 5 installation … could not be validated
```
**根因**：SpyGlass 的 perl 包装脚本（及另外两个脚本）里 `case "$PLAT" in Linux-2*|…|Linux-6*)`
**没有 `Linux-7*`**，内核 7 掉进 `*)` 分支报 Unknown。

**修复**：内核判断加 `Linux-7*`（改前先备份）。**两套安装都要改**：
独立版 `/opt/EDA/Synopsys/spyglass/X-2025.06/SPYGLASS_HOME/` 与 UFE 集成版
`/opt/EDA/Synopsys/ufe_optional_spyglass-vcs/X-2025.06/SPYGLASS_HOME/`——
UFE 版就是 `.zshrc` 里 `spyglass with optional VCS/UFE integration` 用的那套，
只补独立版时 `spyglass -version` 仍报「SPYGLASS_HOME was not intuited correctly /
Perl 5 installation could not be validated」。
1. `{SPYGLASS_HOME}/lib/multi-perl/bin/perl`（UFE 版路径，SKILL 旧文写的 `perl/bin/perl` 是相对布局）：`Linux-2* | … | Linux-6*)` → 末尾加 ` | Linux-7*`
2. `{SPYGLASS_HOME}/bin/spygenlib`：`Linux-2* | Linux-3* | Linux-4*)` → 补全到 ` | Linux-7*)`
3. `{SPYGLASS_HOME}/lib/SpyGlass/standard-environment.sh`：`Linux-6*)` → `Linux-6* | Linux-7*)`

可直接跑 `scripts/fix_spyglass_linux7.sh`（自动备份 + 修改 + 验证）。

> bash 脚本不受影响：第 1.1 步已把 vendor 脚本统一为 `#!/bin/bash -h`，
> `/bin/sh` 保持 dash 也不会再踩 `Illegal option -h`。

---

## 7. License（lmgrd / snpslmd）

常见根因，逐层排查（先下面 1-3，再 7.4）：

1. **`/usr/tmp` 缺失**（lmgrd 硬编码依赖 `/usr/tmp/.flexlm`）：
   ```bash
   sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp
   ```
2. **license 文件 CRLF 行尾**（Windows 生成，`SERVER` 行端口带 `\r` 导致解析失败）：
   ```bash
   sudo sed -i 's/\r$//' /opt/EDA/Synopsys/synopsys.lic
   ```
3. **端口一致**：`SNPSLMD_LICENSE_FILE` 里的端口必须等于 license `SERVER` 行端口。

环境变量（客户端配置，正确没问题）：
```zsh
export SNPSLMD_LICENSE_FILE=27080@vv-mint
export LM_LICENSE_FILE=/opt/EDA/Synopsys/synopsys.lic
export SCL_HOME=/opt/EDA/Synopsys/scl/2025.03
```

### 7.4 lmgrd 启动必须带 `-c <licfile>`（最隐蔽的坑，已踩）

**症状**：scl 的 license server 启动后 snpslmd 每 ~10 秒退出一次，日志出现：
```
(snpslmd) Error getting server information.
(snpslmd) Error opening the license file, 27080@vv-cachyos
(lmgrd) snpslmd exited with status 1 signal = 17
(lmgrd) manager (lmgrd) will attempt to re-start the vendor daemon.
(lmgrd) ... restarts ~10 次后放弃: Please correct problem and restart daemons
```
`lmutil lmstat` 显示 `license server UP (MASTER)` 但 `snpslmd: Cannot connect …`,
或 `-7,10015 No socket connection…`。

**根因**：若只写 `lmgrd -l <log>` 而不加 `-c`，lmgrd 靠 `LM_LICENSE_FILE` 找到 license 文件，
但 vendor daemon `snpslmd` 启动时继承 shell 环境里的
`SNPSLMD_LICENSE_FILE=27080@vv-cachyos`（server 引用形式），把该**字符串当 license 文件路径**去
打开 → `Error opening the license file, 27080@vv-cachyos` → 崩溃循环。

**修复**：启动必须带 `-c`（lmgrd 会把真实路径传给 snpslmd，进程参数会出现
`-c :/opt/…/synopsys.lic:`），手动启动时再加 `env -u` 双保险：
```bash
env -u SNPSLMD_LICENSE_FILE -u LM_LICENSE_FILE \
  /opt/EDA/Synopsys/scl/2025.03/linux64/bin/lmgrd \
  -c /opt/EDA/Synopsys/synopsys.lic \
  -l /opt/EDA/Synopsys/synopsys_licnese.log
```
> 注意：`SNPSLMD_LICENSE_FILE=27080@host`、`LM_LICENSE_FILE=<file>` 作为**客户端**连接配置是对的，
> 错在它们出现在**启动 lmgrd 的进程**环境里（systemd 环境干净则天然无此问题）。

### 7.5 systemd 开机自启（Type=simple + -z，实测）

本机 lmgrd 是**前台运行、不自行 daemonize**，`Type=forking` 会在 `TimeoutSec` 后被 systemd
把 lmgrd 一起杀光。因此必须 `Type=simple`，脚本里 lmgrd 加 `-z`：

`/opt/EDA/Synopsys/synopsys_script.sh`：
```bash
#!/bin/bash
/opt/EDA/Synopsys/scl/2025.03/linux64/bin/lmgrd -z -c /opt/EDA/Synopsys/synopsys.lic -l /opt/EDA/Synopsys/synopsys_licnese.log
```

`/etc/systemd/system/synopsyslm.service`：
```ini
[Unit]
Description=Synopsys Licensing Service
After=network.target

[Service]
Type=simple
User=vv
ExecStart=/opt/EDA/Synopsys/synopsys_script.sh
Restart=on-failure
RestartSec=5
TimeoutSec=30

[Install]
WantedBy=multi-user.target
```
```bash
sudo systemctl daemon-reload && sudo systemctl enable synopsyslm.service
sudo systemctl start synopsyslm.service
```

### 7.6 hostid：双网卡机器取哪个 MAC

`lmutil lmhostid` 可能返回双 hostid（如 `""7413eaff5776 644ed7097462""`，wlan0+eno1）。
license `SERVER` 行填写任意一个匹配的 MAC 即可（snpslmd SLOG 会打印
`HostID node-locked in license file` 与 `HostID of the License Server` 做对照，命中之一即通过）。
MAC 获取：`ip link` 或 `cat /sys/class/net/*/address`。

### 7.7 平台差异备忘

skill 主要验证环境是 Mint 22.3（`/bin/sh -> dash`），而这一节的实际复现机器是
**CachyOS（Arch）**：`/bin/sh -> bash`，License 部分行为一致（无需 1.1 shebang 修复，
`#!/bin/sh -h` 在 bash 下合法）；差异仅在于 CachyOS 缺老 ABI 系统库（见第 8 节 Verdi compat）。

---

## 8. Verdi（CachyOS 缺老 ABI 系统库）—— compat 目录方案

**症状**：`verdi -id` / Verdi 启动报
`error while loading shared libraries: libxml2.so.2: cannot open shared object file`、
`libselinux.so.1`、`libnuma.so.1`、`libpng12.so.0`、`libssl.so.1.1` 等。

**根因**：CachyOS/Arch 的库 ABI 比 RHEL 新：libxml2 是 `.so.16`（需 `.so.2`）、OpenSSL 3
（需 1.1）、系统无 libpng12、旧 Qt5 子模块（Qml/Charts/WebEngine 等由 Verdi 自带，不在话下）。
其中 `libnuma.so.1` 与 `libselinux.so.1` 用包安装即可：
```bash
sudo pacman -S numactl libselinux
```
其余老 ABI 库在 Synopsys 树内自带，建本地 compat 目录放软链（避免整目录塞 Verdi 老 libstdc++
与系统 tbb 冲突 CXXABI_1.3.15）：
```bash
V=/opt/EDA/Synopsys/verdi/X-2025.06; C=/opt/EDA/Synopsys/.compat/verdi; mkdir -p $C
ln -sf $V/platform/LINUXAMD64/lib/Qt5/lib/depends/xslt/libxml2.so.2  $C/libxml2.so.2
ln -sf $V/platform/LINUXAMD64/lib/Qt5/lib/depends/ssl/libssl.so.1.1    $C/libssl.so.1.1
ln -sf $V/platform/LINUXAMD64/lib/Qt5/lib/depends/ssl/libcrypto.so.1.1 $C/libcrypto.so.1.1
ln -sf $V/platform/LINUXAMD64/lib/zebu/libRtxStable.so                 $C/libRtxStable.so
ln -sf $V/etc/lib/libstdc++/linux64/libpng12.so.0                      $C/libpng12.so.0
```
**推荐做法：wrapper 脚本 `~/.local/bin/verdi`**（只在启动 verdi 时注入，不污染全局 Qt5）：
```bash
#!/usr/bin/env bash
set -u
export VERDI_HOME="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}"
export LD_LIBRARY_PATH="/opt/EDA/Synopsys/.compat/verdi:$VERDI_HOME/platform/LINUXAMD64/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/plugins:$LD_LIBRARY_PATH"
exec "$VERDI_HOME/bin/verdi" "$@"
```
装好后 `.zshrc` 需要末尾「最终 PATH 断言」`export PATH="$HOME/.local/bin:$PATH"` 排在
`$VERDI_HOME/bin` 的 prepend 之后（否则命中真身）——与 2.2.5 的 vcs 同理。

> ⚠️ 不要用全局 `export LD_LIBRARY_PATH=...Qt5/lib...`：Verdi 自带 Qt5 5.15.11 会把系统
> Qt5 5.15.19 遮蔽，影响同终端启动的其他 Qt 应用。
> 注意不要加 `etc/lib/libstdc++/linux64` 整目录（老 libstdc++ 会覆盖系统新版本，导致
> 系统 tbb 报 `version CXXABI_1.3.15 not found`）。

验证：`ldd $VERDI_HOME/platform/LINUXAMD64/bin/Novas` 无 `not found`；
`verdi -id` 能打印 `Product version = Verdi_X-2025.06`（注意它可能挂起输出版本后 Ctrl-C）。

---

## 验证

```bash
# /bin/sh 应为系统默认 dash（本方案不改系统 shell）
ls -l /bin/sh                              # -> dash
# 不应再有 /bin/sh -h 的脚本残留
grep -rl '^#! */bin/sh *-h' /opt/EDA/Synopsys/ | wc -l   # 应为 0

# VCS 端到端
cat > /tmp/t.v <<'EOF'
module t; initial begin $display("VCS OK"); $finish; end endmodule
EOF
vcs -full64 -sverilog -o simv t.v && ./simv          # 应打印 "VCS OK"，退出 0

# Verdi
verdi -batch -version 2>&1 | grep 'Version X-2025.06'   # GUI 型命令：打印版本后进程挂起不退出属正常，看到版本行即可 Ctrl-C

# DC
dc_shell -f /dev/stdin <<'EOF'   # 或写 .tcl 文件
read_file -format verilog xxx.v
elaborate xxx
link
exit
EOF

# LC（用包装脚本，退出码应为 0）
lc_shell -f xxx.tcl && echo "exit=$?"

# SpyGlass
spyglass -version | grep 'SpyGlass Predictive Analyzer'

# License
lmutil lmstat -c 27080@vv-mint   # license server UP / snpslmd UP
```

---

## 参考文件

- `scripts/fix_spyglass_linux7.sh` — SpyGlass 内核判断修复（备份+改+验证）
- `scripts/lc_shell_wrapper.sh` — LC 退出崩溃包装脚本
- `reference/zshrc.example` — 实测机器的完整 `~/.zshrc` EDA 工具链配置参考
  （Synopsys 六套工具 env/alias、最终 PATH 断言与 wrapper 的关系、Xilinx 段可忽略），
  主机为 CachyOS，主机名 `vv-cachyos`，license 端口 27080
