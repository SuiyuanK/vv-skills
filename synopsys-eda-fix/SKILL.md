---
name: synopsys-eda-fix
description: >-
  Diagnose and fix Synopsys X-2025.06 EDA tools (VCS, Verdi, DC/syn, LC,
  SpyGlass, SCL 2025.03) on Linux Mint 22.3 (Ubuntu 24.04 base, glibc 2.39)
  with Linux kernel 7.0.0. Covers the /bin/sh→bash shebang fix for 230
  vendor scripts, VCS --as-needed linker undefined-reference crash,
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

## 修复总览（速查）

| 工具 | 症状 | 修复 |
|---|---|---|
| 全部 | `#!/bin/sh -h` 脚本报 `Illegal option -h` | `/bin/sh → bash` |
| 全部 | `snps_platform: 无法执行` | 装 `csh` |
| VCS | 链接 `undefined reference to vfs_fopen/snps_mem_*` | `-LDFLAGS "-Wl,--no-as-needed"` |
| VCS | 启动刷「语法错误」OS 检测噪音 | `VCS_ARCH_OVERRIDE=linux` |
| Verdi | `verdi_supp` post_install 报 home 不对 | 补跑 post_install 加 `-verdi_home` |
| LC | 退出时 segfault（工作已完成） | 包装脚本屏蔽报错 + 返回 0 |
| SpyGlass | `Unknown platform: Linux-7.0.0-…` | 3 个脚本内核判断加 `Linux-7*` |
| 全部 | license 连不上 / 服务起不来 | lmgrd `/usr/tmp` + CRLF + systemd |

---

## 1. 通用前置

### 1.1 让 `/bin/sh` 指向 bash（最重要，一次修好 230 个脚本）

Synopsys 有约 **230 个脚本** shebang 写成 `#!/bin/sh -h`，其中 `-h` 是 bash 专有参数。
Mint/Ubuntu 的 `/bin/sh` 是 dash，dash 不认 `-h` → 直接 `Illegal option -h` 退出。

**非交互方式强制改**（推荐，避免交互对话框默认「是」不改）：
```bash
echo "dash dash/sh boolean false" | sudo debconf-set-selections
sudo dpkg-reconfigure -f noninteractive dash
ls -l /bin/sh        # 必须变成 -> /bin/bash
```
兜底（若上面没变）：
```bash
sudo ln -sf /bin/bash /bin/sh
```

验证：`ls -l /bin/sh` 应指向 `bash`。

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

> 注意：若 `vcs -id` 报 `/bin/sh: 0: Illegal option -h`，先做第 1.1 步。

---

## 4. DC (syn) / Design Compiler

无需额外修复（做 1.1 的 `/bin/sh→bash` 和 1.2 的 csh 后即可用）。
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

**修复**：3 个文件的内核判断加 `Linux-7*`（改前先备份）：
1. `perl/bin/perl`：`Linux-5* | Linux-6*)` → `Linux-5* | Linux-6* | Linux-7*)`
2. `SPYGLASS_HOME/bin/spygenlib`：`Linux-3* | Linux-4*)` → 补全到 `Linux-7*)`
3. `SPYGLASS_HOME/lib/SpyGlass/standard-environment.sh`：`Linux-6*)` → `Linux-6* | Linux-7*)`

可直接跑 `scripts/fix_spyglass_linux7.sh`（自动备份 + 修改 + 验证）。

> bash shebang 不用改：因为第 1.1 步已把 `/bin/sh` 指向 bash。

---

## 7. License（lmgrd / snpslmd）

三个常见根因，逐层排查：

1. **`/usr/tmp` 缺失**（lmgrd 硬编码依赖 `/usr/tmp/.flexlm`）：
   ```bash
   sudo mkdir -p /usr/tmp && sudo chmod 1777 /usr/tmp
   ```
2. **license 文件 CRLF 行尾**（Windows 生成，`SERVER` 行端口带 `\r` 导致解析失败）：
   ```bash
   sudo sed -i 's/\r$//' /opt/EDA/Synopsys/synopsys.lic
   ```
3. **端口一致**：`SNPSLMD_LICENSE_FILE` 里的端口必须等于 license `SERVER` 行端口。

环境变量：
```zsh
export SNPSLMD_LICENSE_FILE=27080@vv-mint
export LM_LICENSE_FILE=/opt/EDA/Synopsys/synopsys.lic
export SCL_HOME=/opt/EDA/Synopsys/scl/2025.03
```

**systemd 开机自启**：脚本 `synopsys_script.sh` 用 `lmgrd -c … -l …`（无 `-z`），配
`Type=forking`；或按原 license skill 用 `-z` + `Type=simple`。两者都行，关键是
`/usr/tmp` 必须已建、license 无 CRLF。

---

## 验证

```bash
# VCS 端到端
cat > /tmp/t.v <<'EOF'
module t; initial begin $display("VCS OK"); $finish; end endmodule
EOF
vcs -full64 -sverilog -o simv t.v && ./simv          # 应打印 "VCS OK"，退出 0

# Verdi
verdi -version | grep 'Version X-2025.06'

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
