# 旧 ABI 实测结论

适用主机：x86_64 Ubuntu 26.04、Linux kernel major 7。扫描范围仅限 `/opt/eda/Synopsys`；未使用或修改 Xilinx，也未下载或安装系统包。

## 准入解释

`inspect` 中出现候选只表示：文件是 ELF64 x86-64，内部 SONAME 精确匹配，并列出了直接 `DT_NEEDED`。它不表示候选已能用于目标产品。

- `same_product=true`：候选来自目标产品或其同版本 supplement，仍需目标程序的符号版本与完整传递依赖验证。
- `same_product=false`：只是其他 Synopsys 产品中的线索，不得自动复制或注入。
- `PARTIAL_SAME_PRODUCT_CANDIDATES`：至少一个依赖有同产品候选，但完整集合不齐。
- `BLOCKED_DEPENDENCY`：没有完整且已验证的同产品依赖集合。

## 逐产品结论

| 产品 | 同产品候选 | 仍缺或未闭合 | 结论 |
|---|---|---|---|
| SCL 2024.06 | 无 | `libncurses.so.5`、`libtinfo.so.5` | license core 的 `lmver/lmstat` 健康；可选 `sclsh` 保持 blocked |
| DC V-2023.12-SP3 | 无满足其当前启动缺失项的完整集合 | `libpython3.6m.so.1.0`、`libpng12.so.0`，另有 glibc private ABI 风险 | 不部署跨产品 Python/png |
| LC V-2023.12-SP3 | 无完整集合 | `libncurses.so.5`、`libtinfo.so.5`、`libpng12.so.0` | wrapper 可修；runtime 保持 blocked |
| ICC2 V-2023.12-SP3 | `etc/{Python,twkPython}/lib/libpython3.6m.so.1.0`，带产品局部 OpenSSL 1.0 依赖 | `libtinfo.so.5`、`libsasl2.so.3`，且需完整闭包验证 | `PARTIAL_SAME_PRODUCT_CANDIDATES`，不部署部分 bundle |
| VCS W-2024.09-SP1 | 内部子组件含 `libtinfo.so.5`、`libpng12.so.0`、Python 3.6 | wrapper 本身有孤立 `else`；候选只允许留在 VCS 内部用途 | 不向其他产品复制；先获取供应商脚本修复 |
| Verdi W-2024.09-SP1 | 主 Verdi `etc/lib/libstdc++/linux64/libpng12.so.0.49.0` 是 ELF64 x86-64、SONAME `libpng12.so.0` | `platform/linux64/bin/novas` 还需要 `libxml2.so.2`；完整 Qt/private closure 未建立 | `PARTIAL_SAME_PRODUCT_CANDIDATES`，不做仅 png 的部分注入 |

全树未找到合格的 Synopsys x86-64 `libncurses.so.5` 或 `libsasl2.so.3`。VCS 中存在 `libtinfo.so.5`，但不能据此给 SCL、LC 或 ICC2 跨产品部署。DC/LC/ICC2 中的 `libxml2.so.2` 也不能直接注入 Verdi。

## VCS 供应商脚本证据

`vcs/W-2024.09-SP1/bin/vcs` 是 Bash-only 脚本，却声明 `#!/bin/sh -h`。改为 Bash 后完整 `bash -n` 在 40132 行失败：

- 38884 的条件由 39471/39473 正常配对；
- 39508 的条件由 40111/40122 正常配对；
- 40123–40130 的 timestamp 条件正常闭合；
- 40131 是 `VcsExit 0;`；
- 40132 是无 opener 的孤立 `else`，40133 开始所谓 non-incremental 分支。

仅删除或注释 40132 可使临时副本通过 `bash -n`，但不能证明 non-incremental 控制流语义正确。因此 skill 只标记 `BLOCKED_VENDOR_SCRIPT`，不自动改 shebang 或删除供应商代码。

## 后续安全来源

只有两种来源可继续评估：

1. Synopsys 针对精确 release/build 的正式兼容补丁；
2. 可追溯的 Ubuntu 官方历史包，在 workspace `./tmp` 解包并通过 ELF、SONAME、符号版本、完整 `DT_NEEDED` 闭包和目标产品最小运行验证。

不得把 `.so.6` 改名为 `.so.5`，不得使用其他厂商安装树，不得写 `/usr/lib`，不得设置全局 `LD_LIBRARY_PATH`。
