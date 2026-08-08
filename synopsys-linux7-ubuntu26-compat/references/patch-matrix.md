# X-2025.06 补丁矩阵

本文只记录足够做结构准入的短锚点和目标语义，不复制 Synopsys 完整专有脚本。脚本以运行时结构判据为准，不将某台安装的固定 SHA-256 作为版本准入。

## 全局状态规则

| 状态 | 含义 | apply 行为 |
|---|---|---|
| `ORIGINAL` | 唯一原始锚点存在，目标锚点不存在 | staged 中执行已知变换 |
| `PARTIAL` | 一个文件内只有部分已知变换完成 | 补齐其余已知变换 |
| `PATCHED` | 所有目标结构恰好各一份 | 幂等跳过 |
| `UNEXPECTED` | 锚点缺失/重复、冲突结构、未知 shebang、symlink/非普通文件 | 整体拒绝，零产品写入 |
| `MISSING` | 目标文件不存在 | 整体拒绝 |
| `UNSUPPORTED_VERSION` | 版本布局不是 X-2025.06 | 整体拒绝 |

每个目标必须是普通、非符号链接文件。所有 roots 必须先全部通过预检，才进入 staging 和 commit。

## 目标矩阵

### `lib/SpyGlass/standard-environment.sh`

| 项目 | 判据 |
|---|---|
| 身份 | 存在 `platform_species ()` 和返回 `Linux4` 的 x86_64 taxonomy |
| 原始 taxonomy | Linux 分支以 `Linux-6*)` 结束 |
| 目标 taxonomy | 同一分支唯一加入 `Linux-7*`，继续返回 `Linux4` |
| 原始 allocator gate | `unameP`、`unameM` 后直接定义 `platform_species` |
| 目标 allocator gate | 中间仅对 x86_64、Ubuntu 26.04 导出 `SPYGLASS_USE_SYSTEM_MALLOC=1` |
| 部分态 | taxonomy 与 allocator gate 只有一项完成 |
| 拒绝 | 任一原/目标锚点重复，host gate 被放宽，结构次序未知 |
| 验证 | `bash -n`；重新分类必须为 `PATCHED` |

不修改 vendor 的 `set_ptMalloc`、`use_ptMalloc`、`set_jeMalloc`、`use_jeMalloc` 函数。

### `<install>/perl/bin/perl`

| 项目 | 判据 |
|---|---|
| 身份 | 有 unknown-platform 报错分支及最终 `exec ${perl_exe} ${perl_SEARCHPATH}` |
| 原始 | Linux case 支持 2/3/4/5/6 |
| 目标 | 唯一增加 Linux 7，x86_64 仍选 `Linux4` |
| 拒绝 | case 原/目标锚点缺失或重复，wrapper 身份不符 |
| 验证 | `bash -n`；`perl -v` 无 `Unknown platform` |

### `SPYGLASS_HOME/bin/spygenlib`

| 项目 | 判据 |
|---|---|
| 身份 | 存在 `platform_species` 和 `exec "$d2/obj/link.$platform" "$@"` |
| 原始 | Linux case 支持 2/3/4 |
| 目标 | 增加 5/6/7 并映射到既有 Linux4 |
| 拒绝 | case 锚点缺失、重复或 exec 形态未知 |
| 验证 | `bash -n`；单独检查 `obj/link.Linux4` |

`obj/link.Linux4` 不存在时只报告 Library Compiler payload 缺失，不创建替代文件。

### `SPYGLASS_HOME/bin/.platform_check.sh`

| 项目 | 判据 |
|---|---|
| 身份 | 有 `platform_check(){` 与 `return $result` |
| 原始定位 | 唯一注释 Ubuntu/Debian 历史分支锚点 |
| 目标 | 在该位置前精确加入 `/etc/os-release` 中 Ubuntu 26.04 分支，`result=1` 并输出本地适配警告 |
| 拒绝 | exact block/警告重复、原始定位不唯一、脚本赋值 `SKIP_PLATFORM_CHECK` |
| 验证 | **`sh -n`**；重新分类为 `PATCHED` |

保持 `#!/bin/sh -x`，不能把此 POSIX 模块改成 Bash。

### `SPYGLASS_HOME/bin/spyglass`

| 项目 | 判据 |
|---|---|
| 身份 | 有已知 Bash `[[ "$1" == *"$id"* ]]` 结构 |
| 原始 | `#!/bin/sh` |
| 目标 | `#!/bin/bash` |
| 拒绝 | Bash-only 身份锚点缺失或 shebang 是其他解释器 |
| 验证 | `bash -n`；`spyglass -version` |

### `SPYGLASS_HOME/bin/spyglass_main`

| 项目 | 判据 |
|---|---|
| 身份 | 有 Bash 数组 `ary=($LD_PRELOAD)` 及两个确切 tcmalloc selector 首分支 |
| 原始 | `/bin/sh`；batch/GUI selector 都直接从 tcmalloc 分支开始 |
| 目标 | `/bin/bash`；两个 selector 均先检查 `SPYGLASS_USE_SYSTEM_MALLOC=1` 并执行空操作 |
| 部分态 | shebang、batch selector、GUI selector 中一或两项已完成 |
| 拒绝 | selector 缺失、重复、重排、只有模糊 malloc 关键字可匹配 |
| 验证 | `bash -n`；normal `sg_shell` marker；compile；GUI smoke |

系统 allocator 分支必须在两个原始 fallback chain 之前，不修改后续 tcmalloc/snpsmem/jemalloc/ptmalloc 顺序。

### `SPYGLASS_HOME/bin/spyexplain`

| 项目 | 判据 |
|---|---|
| 身份 | 使用 `source .../.platform_check.sh` |
| 原始 | `#!/bin/sh` |
| 目标 | `#!/bin/bash` |
| 拒绝 | identity 缺失或未知 shebang |
| 验证 | `bash -n`；`spyexplain -mixed --short_help_only` exit 0 |

## 事务和回滚准入

`apply` 写前必须同时满足：

- host 精确匹配 x86_64、Ubuntu 26.04、kernel major 7；
- 所有 target 状态只有 `ORIGINAL`、`PARTIAL` 或 `PATCHED`；
- backup/staged 与 target 位于同一文件系统；
- staged shell syntax 和语义分类通过；
- backup/staged 动态 SHA-256 正确；
- commit 前 target 仍等于 preflight SHA-256。

`rollback` 必须同时满足：

- manifest schema、skill name、release 和状态有效；
- backup 等于 manifest 的 before hash；
- 当前 target 等于 manifest 的 after hash；
- 原子恢复后等于 before hash。

如果当前 target 已漂移，拒绝覆盖，交由操作者比较升级或人工改动。
