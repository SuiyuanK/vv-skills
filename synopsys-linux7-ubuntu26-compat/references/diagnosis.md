# 诊断记录：SpyGlass X-2025.06、Ubuntu 26.04 与 Linux 7

## 结论

本问题不是单一“系统版本检查失败”，而是四个串联的兼容层：

1. kernel taxonomy 不认识 `Linux-7.*`，bundled Perl 在最早阶段退出；
2. 独立发行版白名单不认证 Ubuntu 26.04；
3. vendor wrapper 用 Bash 语法却声明 `/bin/sh`，在 Ubuntu dash 下产生假错误；
4. 产品自带的替换 allocator 在该 host 的普通 engine 和 GUI 路径崩溃，系统 allocator 工作正常。

修复必须逐层、窄范围完成。绕过其中一层并不代表运行链完整。

## 第一层：Linux 7 只是未知 taxonomy，不是缺少 Linux7 runtime

X-2025.06 安装内容提供现代 64-bit Linux runtime `Linux4`，没有 `Linux7`。`Linux4` 是产品内部“物种名”，不是 kernel major 的同名目录。

原有多个 wrapper 只匹配到 Linux 6。因此 kernel 7 到来时，bundled Perl 报：

```text
ERROR(perl): Unknown platform: Linux-7.0.0-29-generic
```

这又被上层包装成误导性错误：

```text
The Perl 5 installation within `$SPYGLASS_HOME' could not be validated.
```

正确适配是让 `Linux-7*` 沿用 x86_64 的 `Linux4` 分支，涉及：

- `lib/SpyGlass/standard-environment.sh`；
- `<install>/perl/bin/perl`；
- `bin/spygenlib` 的 taxonomy。

绝不能新建 `Linux7` 目录、复制 runtime 或修改 ELF 文件。

## 第二层：发行版检查与 kernel taxonomy 相互独立

`.platform_check.sh` 有自己的发行版认证清单。即使 kernel 已映射到 `Linux4`，Ubuntu 26.04 仍会被拒绝，因为 vendor 清单没有该版本。

该脚本有反常的 return 约定：

```text
0 = unsupported
1 = accepted non-SUSE Linux
2 = accepted SUSE
```

本地适配只为 `x86_64 + /etc/os-release ID=ubuntu + VERSION_ID=26.04` 设置既有成功值 `1`，并打印：

```text
WARNING: Using a local SpyGlass X-2025.06 compatibility adaptation ... not a Synopsys support certification.
```

这是透明性告警，不是错误。不能全局设置 `SKIP_PLATFORM_CHECK`，也不能伪造系统发行版。

## 第三层：Ubuntu `/bin/sh` 是 dash，而 wrapper 实际依赖 Bash

已知 wrapper 中存在：

- `[[ ... ]]`；
- Bash 数组，如 `ary=($LD_PRELOAD)`；
- `source`；
- Bash 模式匹配。

它们却使用 `/bin/sh` shebang。在 Ubuntu 上由 dash 执行后，可见：

```text
[[: not found
source: not found
/tmp space is not sufficient
```

最后一项不是磁盘空间真的不足，而是前置 Bash 条件表达式在 dash 下失败，导致错误分支被执行。

只对确实含已知 Bash-only 锚点的 `spyglass`、`spyglass_main`、`spyexplain` 改为 `/bin/bash`。`.platform_check.sh` 本身保持 POSIX shell，并用 `sh -n` 检查。

## 第四层：替换 allocator 是普通 engine/GUI 崩溃根因

平台和 shell 问题修复后，最小 Tcl 脚本仍在首个 marker 之前崩溃：

```text
SIGSEGV
exit code 3
```

重要对照：同一脚本使用 `--gdb` 可以完成。继续检查 wrapper 后发现这些诊断模式会改变 allocator 路径，因此“调试器下成功”不是程序本身随机恢复，而是 allocator 对照实验。

测试结果：

- 默认产品替换 allocator：崩溃；
- 显式 product ptmalloc：崩溃；
- product snpsmem：崩溃；
- 系统 allocator：最小 Tcl、compile 和 GUI 均可运行。

因此准确结论是：**所测 SpyGlass 产品替换 allocators 在该 host 上不兼容**，不能只归咎于某一个 ptmalloc 库。正常 fallback 常会选择 bundled jemalloc。

修复使用产品 wrapper 内的显式开关语义：

```text
SPYGLASS_USE_SYSTEM_MALLOC=1
```

它在精确 host 上由 standard environment 导出；`spyglass_main` 的 batch 和 GUI 两个 allocator selector 均加入第一优先的空操作分支，从而不注入产品替换 allocator。

注意：

- `SPYGLASS_USE_PTMALLOC=no` 不会关闭 ptmalloc，因为 vendor 逻辑只检查变量是否非空；
- 仅清空 `SPYGLASS_LD_PRELOAD`/`LD_PRELOAD` 不能阻止 selector 随后注入 allocator；
- `--gdb`/`--strace`/`--valgrind` 是诊断证据，不是生产修复。

## 验证证据

真正的通过标准不是“窗口出现”或 `-version` 单点成功，而是：

- bundled Perl 可以启动并报告 5.8.3 runtime；
- `spyglass -version` 报 X-2025.06；
- normal-mode `sg_shell` 在不使用调试模式时打印 marker 并正常退出；
- 真实 compile 验证完成：
  - `new_project`；
  - 读取 example gates library；
  - 读取 Verilog；
  - `compile_design`；
  - 完成 marker，exit code 0；
- `spyexplain -mixed --short_help_only` exit code 0，无 `source: not found`；
- GUI 运行 25 秒未出现 signal 6/11，之后测试主动终止。

GUI 日志中的 signal 15 若发生在预定 timeout，是测试清理，不是 allocator crash。真实失败重点是 signal 6 (`SIGABRT`) 或 11 (`SIGSEGV`)。

`QGtkStyle could not resolve GTK` 在上述 GUI 仍持续运行时只是主题/外观告警。尝试 `Fusion`、`Cleanlooks`、`Plastique` 并未解决原崩溃，也进一步说明它不是根因。

## 容易误判的独立问题

### `spygenlib` 缺 `obj/link.Linux4`

修补 taxonomy 只使 wrapper 正确计算 `Linux4`。如果以下文件不存在：

```text
SPYGLASS_HOME/obj/link.Linux4
```

则缺的是 Library Compiler payload/安装组件。不能伪造 executable，也不能宣称 taxonomy 修复应生成它。

### 离线文档包名为空

`post_install.sh` 通过失败的：

```text
spyglass -batch -id
```

提取完整版本，再拼出 `Spyglass_docs_<version>.tar.gz`。启动器在安装期失败时版本为空，于是日志出现：

```text
Spyglass_docs_.tar.gz is not available
```

解决 runtime 兼容后仍需核对安装介质实际文档 archive 名称和版本。这与 engine/GUI 兼容是独立事项。

### Classic flow exit code 7

X-2025.06 会拒绝已废弃 classic flow。这个错误说明调用方式不再支持，不说明 Ubuntu/Linux 7 适配失败。使用现代 `sg_shell` 做功能回归。

### post-crash GDB attach 被拒

Linux `ptrace_scope` 可导致：

```text
ptrace: Operation not permitted
```

无需为了诊断修改系统安全策略。直接通过产品 `--gdb` 让 debugger 成为子进程父级即可做对照，但最终仍要回到 normal-mode 验证。
