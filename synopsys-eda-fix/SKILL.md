---
name: synopsys-eda-fix
description: >-
  Diagnose and fix Synopsys X-2025.06 EDA tools (VCS, Verdi, DC/syn, LC,
  SpyGlass, SCL 2025.03) on Linux Mint 22.3 (Ubuntu 24.04 base, glibc 2.39)
  and CachyOS/Arch (glibc 2.44) with Linux kernel 7.x. Covers the vendor-script shebang fix (230 scripts to
  #!/bin/bash -h without changing the distro's /bin/sh), VCS --as-needed linker undefined-reference crash,
  SpyGlass "Unknown platform Linux-7" detection failure and SNPSMEM/nss_resolve
  startup SIGSEGV, LC exit segfault (glibc 2.39 malloc interposition), Verdi verdi_supp post-install failure
  and old bundled Fontconfig warnings on CachyOS,
  and FlexLM lmgrd/snpslmd license setup (/usr/tmp, CRLF, systemd). Use when
  a Synopsys tool crashes, fails to launch, or can't obtain a license on this
  system.
---

# Synopsys X-2025.06 EDA 工具在 Mint 22.3、CachyOS / 内核 7 上的修复

## 适用范围

- x86_64，Linux Mint 22.3（Ubuntu 24.04 底，glibc 2.39），Linux 内核 **7.0.0**。
- x86_64，CachyOS（Arch 系，glibc 2.44），Linux 内核 **7.2.x**；SpyGlass、License 与
  Verdi/VCS 老 ABI 问题已在此环境实测。
- Synopsys **X-2025.06**：VCS、Verdi、DC(syn)、LC、SpyGlass、SCL 2025.03。
- 安装根：`/opt/EDA/Synopsys/`。

> 其它发行版/内核/版本不要模糊套用。核心难点是：这些工具是在较老的 RHEL 上编译的，
> 跑在「新 glibc 2.39/2.44 + 内核 7」上会有 wrapper Bashism、内核版本识别不全、内存分配器
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
| Verdi | `xsi:nil` / `invalid constant` Fontconfig 告警 | wrapper 仅对 Verdi 预加载系统 `libfontconfig.so.1` |
| LC | 旧 krb5 符号缺失；成功后的退出清理 segfault | 进程级预加载旧 krb5；严格识别后归一化 |
| SpyGlass | `Unknown platform: Linux-7.0.0-…` | 3 个脚本内核判断加 `Linux-7*` |
| SpyGlass | glibc 2.44 启动 `check.Linux4` SIGSEGV/139 | 用户级 `.spyglass.setup` 改用 `runtime`（jemalloc） |
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
永久化使用 `scripts/vcs_wrapper.sh`；它会保留并合并用户已有的 `-LDFLAGS`，避免用户传入
其它链接参数时重新丢失 `--no-as-needed`。

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

这样 `~/.local/bin` 位于 Synopsys bin 之前，连 `make` 也命中 wrapper；LC 的
`~/.local/bin/lc_shell` wrapper 同理。允许其它明确需要更高优先级的用户目录排在它之前，
判断标准是 wrapper 必须早于 vendor bin，而不是机械要求 PATH 第一个元素。

**验证**：新开 zsh，`unalias vcs; for d in $(echo $PATH|tr ':' $'\n'); do [ -e "$d/vcs" ] && { echo $d; break; }; done`
应输出 `~/.local/bin/vcs`（不是 `/opt/…/vcs/bin/vcs`）。

### 2.3 完整 VCS 环境变量

```zsh
export VCS_ARCH_OVERRIDE=linux
export VCS_HOME=/opt/EDA/Synopsys/vcs/X-2025.06
export PATH=$VCS_HOME/bin:$PATH
# wrapper 安装到 ~/.local/bin/vcs，并确保 ~/.local/bin 早于 $VCS_HOME/bin。
alias vcs='~/.local/bin/vcs'
```

### 2.4 CachyOS/Arch 增补（已踩）

- **`dc`（bc 包）缺失**：vcs 脚本自定义 `DC` 环境变量用于 `RecordTime`（`1h2m3.4s`→秒），缺了报
  `vcs: line 7088: dc: 未找到命令`。**修复**：`sudo pacman -S bc`（bc+dc 同包）。
- **`/usr/bin/time` 缺失**（time 包）：`vcs: line 14529: /usr/bin/time: No such file or directory`。
  **修复**：`sudo pacman -S time`。
- **gcc 16 把隐式函数声明升级为 error**：`rmapats.c:20:9: error: implicit declaration of function
  'vcs_simpSetEBlkEvtID'`。VCS 内部 Makefile 的 `CC_CG=gcc` 按 PATH 解析（不用 `VCS_CC`，所以
  `-CFLAGS`/`-cc`/`VCS_CC` 都绕不过 rmapats.o 这条规则）。**不要**把 gcc wrapper 放入
  `~/.local/bin` 全局 shadow；安装到 `~/.local/libexec/synopsys-vcs/gcc`，仅由 VCS wrapper
  给子进程临时前置 PATH：
  ```bash
  #!/usr/bin/env bash
  exec /usr/bin/gcc -Wno-implicit-function-declaration "$@"
  ```
  端到端验证：`vcs -full64 -sverilog -o simv t.v && ./simv` 输出 `VCS OK`；
  运行时有 ASLR 提示（`-no_save` 或无副作用，正常）。
- **`-kdb`/`-debug_acc`（Verdi 集成）必须带 Verdi compat 路径**（已踩）：
  `Verdi KDB elaboration failed` + `Process 'vcs1fe' is exiting with non-zero
  status -1`（增量缓存不清时误报增量错误，先 `rm -rf simv* csrc *.daidir` 再试）。
  根因同第 8 节：vcs1fe/KDB 流程 dlopen Verdi 老 ABI 库（libxml2.so.2 等）。
  `~/.local/bin/vcs` 只在检测到 `-kdb`、`-debug_acc*` 或 `-debug_access*` 时注入
  compat+Qt5+platform lib，普通 VCS 编译不携带 Verdi Qt 环境。

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

**务实修复**：用 `scripts/lc_shell_wrapper.sh` 识别已知的退出清理崩溃。不能只看到
`Segmentation fault`/`stack trace` 就返回 0；当前 wrapper 仅在“原始退出非零、已打印
`Thank you for using Library Compiler.`、崩溃标志位于成功横幅之后”同时成立时归一化。
调用方还可用冒号分隔的 `LC_EXPECT_OUTPUTS` 要求本次目标文件存在且非空。

将 wrapper
装到 `~/.local/bin/lc_shell`，并在 `.zshrc` 加 `alias lc_shell='~/.local/bin/lc_shell'`
（因为原 PATH 里 LC 的 bin 排在 `~/.local/bin` 前，不加别名会命中真身）。

### 5.1 CachyOS/Arch 增补：LC 需要旧版 krb5（已踩）

**症状**：`lc_shell` 启动报
```
lc2_shell_exec: symbol lookup error: /lib64/libkrb5.so.3: undefined symbol:
krb5int_c_deprecated_enctype, version k5crypto_3_MIT
```
**根因**：`lc2_shell_exec` 的 **RPATH 硬编码（旧 RPATH 优先级高于 LD_LIBRARY_PATH）**
且包含 `/lib64`，Arch 系统 krb5 3.x 删除了 `krb5int_c_deprecated_enctype` 老符号；
`LD_LIBRARY_PATH` 指向老库无效（RPATH 优先），必须用 **LD_PRELOAD** 加载老 krb5
（Verdi 自带 `/…/platform/LINUXAMD64/lib/Qt5/lib/depends/krb5`，含 libkrb5.so.3 1.x 全套）。
已在 `~/.local/bin/lc_shell` wrapper 中固化：
```bash
KB="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}/platform/LINUXAMD64/lib/Qt5/lib/depends/krb5"
lc_preload="$KB/libkrb5.so.3:$KB/libk5crypto.so.3:$KB/libgssapi_krb5.so.2:$KB/libkrb5support.so.0${LD_PRELOAD:+:$LD_PRELOAD}"
env LD_PRELOAD="$lc_preload" LD_LIBRARY_PATH="$KB${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}" \
    "$SYNOPSYS_LC_ROOT/bin/lc_shell" "$@"
```
这里必须用进程级 `env`，不要全局 `export`：旧 krb5 若被同一日志管道里的系统
`tee`、`sed`、`grep` 继承，可能使这些现代程序崩溃并反向造成 LC 异常退出。

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

### 6.1 CachyOS/Arch：glibc 2.44 启动段 SIGSEGV（已根治）

**症状**（两套安装一致）：`spyglass -version` 先打印 `SpyGlass Predictive Analyzer`,
随后 `standard-environment.sh: line 1329: Segmentation fault (core dumped) …/obj/check.Linux4`
+ `SpyGlass Exit Code 139`。

**coredump 定位**（systemd-coredump + gdb）：
```
malloc_usable_size () from /usr/lib64/libc.so.6
  ← _nss_resolve_gethostbyname3_r ← gethostbyname ← libNPI.so anrep_init（构造器）
```

#### 根因闭环

安装目录的 `$SPYGLASS_HOME/.spyglass.setup` 默认写有：

```text
OPTIMIZE_PERF = snpsmem
```

启动链是：

```text
.spyglass.setup
  → spyconfig.pl 自动追加 --snpsmem
  → spyglass_main 设置 SPYGLASS_USE_SNPSMEM=yes
  → standard-environment.sh 设置 LD_PRELOAD=libreplacemalloc.so
  → libNPI.so 的 ELF 构造器 anrep_init 调 gethostbyname("")
  → nsswitch 的 resolve 后端进入 libnss_resolve.so
  → libnss_resolve 调 malloc_usable_size()
  → SIGSEGV
```

`nm -D`/`readelf -Ws` 已确认：`libreplacemalloc.so` 只导出 `malloc`、`free`、`calloc`、
`realloc`，**没有导出 `malloc_usable_size`**；调用因此落到 glibc 自己的实现，后者按 glibc
堆布局解析 SNPSMEM 返回的指针并崩溃。SpyGlass 自带的 `libsgjemalloc-Linux4.so` 和
`libsgptmalloc-Linux4.so` 均导出 `malloc_usable_size`。

原来的两个“排除实验”不能排除 SNPSMEM：

- 在外部 `unset SPYGLASS_USE_SNPSMEM SPYGLASS_LD_PRELOAD` 后运行，安装配置仍会重新追加
  `--snpsmem` 并注入 `libreplacemalloc.so`；应以 core 中最终环境为准。
- 移走 `libsgjemalloc-Linux4.so` 不影响当前崩溃，因为默认实际加载的是
  `libreplacemalloc.so`。

`obj/check.Linux4` 带齐库路径直接运行正常，是因为它绕开了 vendor wrapper 的 SNPSMEM
注入。`anrep_init` 位于动态加载器初始化阶段、早于 `main()`，所以这不是 `-version`
专属路径：正常 `lint/lint_rtl` 只要加载 `libNPI.so` 也必经，必须修复。

#### 推荐修复：用户级切换到 jemalloc

优先使用用户级配置，同时覆盖独立版和 UFE 版，不改 `/opt` 或系统 NSS。先检查
`~/.spyglass.setup`；若不存在则创建，若已存在则只修改或加入这一项，保留其它设置：

```text
-- Use SpyGlass's bundled jemalloc on modern glibc.
OPTIMIZE_PERF = runtime
```

部分 VC SpyGlass 集成流程会设置 `LINT_VCUM`，此时 `spyconfig.pl` 跳过 HOME 与 CWD 配置。
为覆盖该入口，再建立独立 customer 配置（内容同上），并在 shell 环境设置：

```zsh
export SPYGLASS_CUSTOMER_CONFIG_FILE="$HOME/.config/synopsys/spyglass-modern-glibc.setup"
```

customer 配置在安装配置之后读取，即使定义了 `LINT_VCUM` 也生效。普通流程中项目目录
`.spyglass.setup` 仍有更高优先级；若项目明确改回 `snpsmem`，必须先审查并纠正项目配置。

SpyGlass 内部映射为：`runtime → jemalloc`、`memory → ptmalloc`、`snpsmem → libreplacemalloc.so`、
`tcmalloc → tcmalloc`。本机 `runtime` 已验证；若大型工程出现 jemalloc 特有问题，可再测试
`memory`。工程目录的 `.spyglass.setup` 优先级高于用户配置，验证时同时检查三层：

```bash
rg -n '^OPTIMIZE_PERF' \
  "$SPYGLASS_HOME/.spyglass.setup" \
  "$HOME/.spyglass.setup" \
  ./.spyglass.setup 2>/dev/null
```

#### 验证与实测结果

先禁用本次测试的 core 并验证信息命令：

```bash
ulimit -c 0
spyglass -version
echo "$?"
```

成功标准：打印 `Version X-2025.06`，退出 0，不再出现 SIGSEGV/139。不要只测版本；还应使用
现有项目运行真实 goal，并确认 design read、elaboration、rule checking、报告生成和退出码。

2026-08-30 在 CachyOS、glibc 2.44、kernel 7.2.2、UFE SpyGlass X-2025.06 上实测：

- `spyglass -version`：退出 0，无新 core。
- `syn_fifo/fifo.v`，GuideWare `latest/block/initial_rtl`，goal `lint/lint_rtl`：270 条规则完成，
  design read/elaboration/synthesis/report 全部完成，退出 0，无新 core；结果为 0 error、
  3 warnings、2 infos。

#### 回滚与不推荐方案

回滚时删除本次专用 customer 配置并取消 `SPYGLASS_CUSTOMER_CONFIG_FILE`；若
`~/.spyglass.setup` 是专为本问题新建的也可删除，若文件原先存在则只恢复
`OPTIMIZE_PERF` 原值，不要覆盖其它用户配置。

不推荐为此删除 `/etc/nsswitch.conf` 的 `resolve`：这只避开当前触发点，不能修复不完整的
allocator，而且会全系统改变 systemd-resolved、分接口 DNS、VPN/LLMNR 等名字解析行为。
若排障时临时改过，必须先备份原文件，并在验证结束后原样恢复。长期上游方案是向 Synopsys
索取适配新 glibc 的 `libNPI.so`/`libreplacemalloc.so` 或升级到受支持版本。

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
exec /opt/EDA/Synopsys/scl/2025.03/linux64/bin/lmgrd -z -c /opt/EDA/Synopsys/synopsys.lic -l /opt/EDA/Synopsys/synopsys_licnese.log
```

使用 `exec` 让 systemd 直接跟踪 `lmgrd` 的 PID 和信号，不保留一层等待中的 shell。

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
**推荐做法：安装 `scripts/verdi_wrapper.sh` 为 `~/.local/bin/verdi`**。它只在启动 Verdi 时
注入依赖，不污染全局 Qt5；同时按 Arch 与 Debian/Ubuntu 的常见路径查找系统 Fontconfig：
```bash
#!/usr/bin/env bash
set -u
export VERDI_HOME="${VERDI_HOME:-/opt/EDA/Synopsys/verdi/X-2025.06}"
export LD_LIBRARY_PATH="/opt/EDA/Synopsys/.compat/verdi:$VERDI_HOME/platform/LINUXAMD64/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/lib:$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/plugins:${LD_LIBRARY_PATH:-}"

system_fontconfig=""
for candidate in /usr/lib/libfontconfig.so.1 /usr/lib/x86_64-linux-gnu/libfontconfig.so.1; do
    if [[ -r "$candidate" ]]; then
        system_fontconfig="$candidate"
        break
    fi
done
if [[ -n "$system_fontconfig" && ":${LD_PRELOAD:-}:" != *":$system_fontconfig:"* ]]; then
    export LD_PRELOAD="$system_fontconfig${LD_PRELOAD:+:$LD_PRELOAD}"
fi
exec "$VERDI_HOME/bin/verdi" "$@"
```
装好后 `.zshrc` 需要末尾「最终 PATH 断言」`export PATH="$HOME/.local/bin:$PATH"` 排在
`$VERDI_HOME/bin` 的 prepend 之后（否则命中真身）——与 2.2.5 的 vcs 同理。

> ⚠️ 不要用全局 `export LD_LIBRARY_PATH=...Qt5/lib...`：Verdi 自带 Qt5 5.15.11 会把系统
> Qt5 5.15.19 遮蔽，影响同终端启动的其他 Qt 应用。
> 注意：wrapper 若有 `set -u`，尾部 `$LD_LIBRARY_PATH` 必须写 `${LD_LIBRARY_PATH:-}`，
> 否则无该变量时启动直接报 `LD_LIBRARY_PATH: 未绑定的变量`（已踩）。
> 验证记录：本机（CachyOS）VCS/DC/LC/Verdi 端到端通过；SpyGlass 见 6.1。
> 注意不要加 `etc/lib/libstdc++/linux64` 整目录（老 libstdc++ 会覆盖系统新版本，导致
> 系统 tbb 报 `version CXXABI_1.3.15 not found`）。

### 8.1 CachyOS 新 Fontconfig 配置与 Verdi 旧解析器

**症状**：Verdi 可以启动和加载 KDB/FSDB，但终端连续打印：
```text
Fontconfig error: "/etc/fonts/conf.d/48-guessfamily.conf" ... invalid attribute 'xsi:nil'
Fontconfig warning: ... invalid constant used : monospace
```

**根因**：不能只凭普通 `ldd Novas` 判断。`LD_DEBUG=libs` 实测表明，Verdi 的主进程或子进程
会经 RPATH 加载 `$VERDI_HOME/platform/LINUXAMD64/lib/Qt5/lib/depends/fontconfig/libfontconfig.so.1`，
然后用这套旧解析器读取 CachyOS Fontconfig 2.18.3 的 `/etc/fonts/conf.d` 新语法。

**修复**：由上述 `scripts/verdi_wrapper.sh` 仅对 Verdi 进程预加载系统
`libfontconfig.so.1`，并保留调用方已有的 `LD_PRELOAD`。不要删除或修改
`/etc/fonts/conf.d/48-guessfamily.conf`，也不要全局导出 `LD_PRELOAD`。

2026-08-31 在 CachyOS 上以 Verdi X-2025.06 批处理实际加载 VCS 生成的 KDB 与 FSDB：修复前
稳定复现 `xsi:nil` 和 `invalid constant`；进程级预加载后告警为零，退出码为 0，且 Tcl 标志
`VERDI_BATCH_CHECK: KDB and FSDB load completed` 正常出现。

验证：`ldd $VERDI_HOME/platform/LINUXAMD64/bin/Novas` 无 `not found`；
`verdi -id` 能打印 `Product version = Verdi_X-2025.06`（注意它可能挂起输出版本后 Ctrl-C）。

---

## 验证

```bash
# 不修改系统 /bin/sh；Mint 通常为 dash，CachyOS 当前为 bash。
readlink -f /bin/sh
# 不应再有 /bin/sh -h 的脚本残留
grep -rl '^#! */bin/sh *-h' /opt/EDA/Synopsys/ | wc -l   # 应为 0

# VCS 端到端；把验证文件放在当前工作区的 ./tmp/ 隔离目录。
mkdir -p ./tmp/vcs-smoke
cat > ./tmp/vcs-smoke/t.v <<'EOF'
module t; initial begin $display("VCS OK"); $finish; end endmodule
EOF
(cd ./tmp/vcs-smoke && vcs -full64 -sverilog -o simv t.v && ./simv)

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
- `scripts/vcs_wrapper.sh` — VCS 链接参数合并、KDB 条件 compat、专用 GCC PATH
- `scripts/vcs_gcc_wrapper.sh` — 仅供 VCS 子进程使用的 GCC 16 workaround
- `scripts/lc_shell_wrapper.sh` — LC 旧 krb5 与退出清理崩溃的窄化处理
- `scripts/verdi_wrapper.sh` — Verdi 老 ABI compat 与系统 Fontconfig 的进程级注入
- `reference/zshrc.example` — 实测机器的完整 `~/.zshrc` EDA 工具链配置参考
  （Synopsys 六套工具 env/alias、最终 PATH 断言与 wrapper 的关系、Xilinx 段可忽略），
  主机为 CachyOS，主机名 `vv-cachyos`，license 端口 27080
