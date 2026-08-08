---
name: spyglass-x2025-linux7-ubuntu26-fix
description: >-
  Diagnose and safely adapt Synopsys SpyGlass X-2025.06 for x86_64 Ubuntu
  26.04 with Linux kernel 7. Use for ERROR(perl): Unknown platform:
  Linux-7, unsupported OS checks, dash errors such as "[[: not found" or
  "source: not found", normal sg_shell SIGSEGV, or GUI SIGABRT caused by
  SpyGlass replacement allocators. Includes transactional apply, verification,
  manifest rollback, and separate reporting for missing spygenlib payloads.
---

# SpyGlass X-2025.06 Ubuntu 26.04 / Linux 7 兼容适配

此 skill 把一次经过真实 batch、compile 和 GUI 回归的兼容适配整理成可审计工具。它只针对：

- Synopsys SpyGlass **X-2025.06**；
- **x86_64**；
- **Ubuntu 26.04**；
- **Linux kernel major 7**。

其他版本、架构、发行版、内核主版本或未知 vendor wrapper 形态必须停止，不能猜测套用。

## 何时使用

以下症状可能属于同一组兼容问题：

- bundled Perl 报 `ERROR(perl): Unknown platform: Linux-7...`；
- `.platform_check.sh` 拒绝 Ubuntu 26.04；
- Ubuntu `/bin/sh`（dash）执行 wrapper 时出现 `[[: not found`、`source: not found`，或错误地报告 `/tmp space is not sufficient`；
- 普通 `sg_shell` 在首个 Tcl marker 前 `SIGSEGV`，但 `--gdb`/`--strace` 模式能运行；
- GUI 启动时 `SIGABRT`，而避开 SpyGlass 自带替换 malloc 后可以保持运行。

先读 `references/diagnosis.md` 理解各层根因；逐文件准入规则见 `references/patch-matrix.md`。

## 固定工作流

在本 skill 目录运行脚本，或使用其绝对路径。脚本只依赖 Python 3 标准库，不安装 pip、Node 或系统包。

### 1. 只读诊断

```bash
python3 scripts/spyglass_compat.py diagnose
```

默认只检查：

```text
/opt/eda/Synopsys/spyglass/X-2025.06
/opt/eda/Synopsys/ufe_optional_spyglass-vcs/X-2025.06
```

可重复指定安装根或 `SPYGLASS_HOME`：

```bash
python3 scripts/spyglass_compat.py diagnose \
  --root /opt/eda/Synopsys/spyglass/X-2025.06 \
  --root /opt/eda/Synopsys/ufe_optional_spyglass-vcs/X-2025.06/SPYGLASS_HOME
```

状态语义：

- `ORIGINAL`：已知原始 X-2025.06 结构，尚未做该变换；
- `PARTIAL`：同一目标内仅部分已知变换存在；
- `PATCHED`：所有目标语义已存在；
- `UNEXPECTED`：锚点缺失、重复、冲突、未知 shebang、符号链接或非普通文件；
- `MISSING`：目标文件不存在；
- `UNSUPPORTED`：host 或整套结构不在支持范围。

任何 `UNEXPECTED`/`MISSING` 都必须在写入前调查，不能放宽成模糊搜索替换。

### 2. 审核并事务应用

先确认输出中的精确目标路径。`apply` 需要对安装树的写权限，但脚本不调用 `sudo`：

```bash
python3 scripts/spyglass_compat.py apply \
  --workspace "$PWD" \
  --yes --write-system
```

所有备份、staged 候选和 manifest 写入调用工作区的：

```text
./tmp/spyglass-x2025-linux7-ubuntu26-fix/apply-<run>/
```

必须保留输出的 `manifest.json`。它记录运行时计算的前后 SHA-256、owner、group、mode、mtime 与备份路径；不依赖某台机器的固定哈希。

事务在写前完成：

1. 两套树全部结构预检；任一未知则零产品写入；
2. 保存原字节、构造候选、执行 `bash -n`/`sh -n` 和语义复检；
3. 验证备份与 staged 哈希，复查产品文件未漂移；
4. 同文件系统原子替换并保留 metadata；
5. 任一步失败时恢复本次已经替换的文件。

### 3. 独立运行时验证

```bash
python3 scripts/spyglass_compat.py verify --workspace "$PWD"
```

验证使用正常模式，不用 `--gdb`/`--strace` 作为通过捷径，包括：

- bundled `perl -v`；
- `spyglass -version`；
- 最小普通 `sg_shell` Tcl marker；
- optional 安装中示例可用时执行 `new_project`、读 gateslib/Verilog 和 `compile_design`；
- `spyexplain -mixed --short_help_only`；
- 有 `DISPLAY` 时运行限时 GUI smoke test；
- 检查 `SPYGLASS_HOME/obj/link.Linux4` 是否存在。

验证产物只进入工作区 `./tmp`。GUI 到时后由测试终止、且无 signal 6/11，属于“保持运行后主动关闭”。以下警告本身不表示失败：

```text
WARNING: Using a local SpyGlass ... compatibility adaptation ... not a Synopsys support certification.
Warning: QGtkStyle could not resolve GTK.
```

前者是有意保留的透明告警，后者通常是外观主题告警；应结合进程存活、退出状态和 signal 判断。

### 4. 仅由 manifest 回滚

```bash
python3 scripts/spyglass_compat.py rollback \
  --manifest ./tmp/spyglass-x2025-linux7-ubuntu26-fix/apply-.../manifest.json \
  --yes --write-system
```

回滚恢复备份原字节，不做反向文本替换。若当前文件不再等于 manifest 中的 patched hash，说明 apply 后有人修改或升级过产品，脚本会拒绝覆盖。

## 实际变换边界

- Linux 7 归类到产品已存在的 `Linux4` 64-bit runtime；**不创建 `Linux7` runtime**。
- 发行版放行严格限定 `ID=ubuntu`、`VERSION_ID=26.04` 和 x86_64，并保留“本地适配、非厂商认证”警告。
- 只有已知 Bash-only 结构存在时才把 `spyglass`、`spyglass_main`、`spyexplain` wrapper shebang 改为 Bash；`.platform_check.sh` 保持 POSIX `sh`。
- 在精确 host 上导出 `SPYGLASS_USE_SYSTEM_MALLOC=1`，并在 batch/GUI 两个 allocator selector 中优先跳过产品替换 allocator。
- 不修改 `use_ptMalloc()`、`use_jeMalloc()` 等 vendor allocator 实现。

## 明确禁止

- 不设置或导出全局 `SKIP_PLATFORM_CHECK`；
- 不伪造 `/etc/os-release`，不让所有未知发行版通过；
- 不将 `SPYGLASS_USE_PTMALLOC=no` 当作关闭开关：vendor 脚本按“变量非空”判断；
- 不用清空 `LD_PRELOAD`/`SPYGLASS_LD_PRELOAD` 代替 selector 修复；
- 不把 `--gdb`、`--strace`、`--valgrind` 当永久运行方案；
- 不生成不存在的 `obj/link.Linux4`、不伪造 Library Compiler payload；
- 不修改 `.zshrc`/`.bashrc`；
- 不自动 sudo，不覆盖未知文件，不递归搜索其他 `/opt` 版本。

## 独立安装问题

- `spygenlib` taxonomy 修复后若仍缺 `SPYGLASS_HOME/obj/link.Linux4`，这是 **Library Compiler payload 未安装**，不是 Linux 7 映射失败。
- 安装日志出现 `Spyglass_docs_.tar.gz is not available`，通常是安装期 `spyglass -batch -id` 先失败导致版本字符串为空；离线介质文档包命名/缺失仍需单独解决。
- Classic flow 已被版本弃用时出现 exit code 7，不属于 OS 适配失败；信息验证使用 `spyglass -version`，工程验证使用现代 `sg_shell`。

## 文件

- `scripts/spyglass_compat.py`：`diagnose`、`apply`、`verify`、`rollback` 单一入口；
- `references/diagnosis.md`：分层根因、验证证据和误导现象；
- `references/patch-matrix.md`：各目标的准入、变换和拒绝条件；
- `tests/test_spyglass_compat.py`：不含完整专有脚本的合成事务测试。
