# 多产品兼容矩阵

| 产品 | 已确认问题 | 自动变换 | 当前运行时边界 |
|---|---|---|---|
| SCL 2024.06 | `sclsh` 需要 ncurses/tinfo 5 | 不修改健康的 license core | 无精确来源前为 `BLOCKED_DEPENDENCY` |
| Design Compiler V-2023.12-SP3 | `snps_shell` 在 dash 下使用 `==` | 两处改 POSIX `=` | 缺 Python 3.6/png12，且需继续核对 glibc 私有 ABI |
| Library Compiler V-2023.12-SP3 | 同一 wrapper 问题 | 两处改 POSIX `=` | `-version` 已健康；只有最小 batch 复现后才考虑旧库 |
| ICC2 V-2023.12-SP3 | sh shebang + Bash `[[ =~ ]]` | 改 Bash shebang | 缺 tinfo5/Python 3.6，传递依赖需闭包验证 |
| VCS W-2024.09-SP1 | sh shebang + function/local/array/`[[ ]]`，且改为 Bash 后供应商脚本在 40132 行存在孤立 `else` | 不自动修改；标记 `BLOCKED_VENDOR_SCRIPT` | `-id` 的早退成功不能证明完整编译路径有效；需 Synopsys 修复包或受支持版本 |
| Verdi W-2024.09-SP1 | sh shebang + array/`[[ ]]`/source | 改 Bash shebang | 主二进制需要旧 libxml2/png12；先报告，不全局注入 |
| verdi_supp W-2024.09-SP1 | 安装时空 `VERDI_HOME` 导致 post-install 未完成 | 只检查，不盲目移动 | 等精确映射与事务回滚验证后再集成 |
| SpyGlass X-2025.06 | Linux 7 taxonomy、Ubuntu gate、dash、allocator | 保留原完整适配 | 两套树已通过 normal batch、optional compile、GUI smoke |

## 依赖准入

候选运行库必须全部满足：

1. 来源为目标产品/版本自身 payload，或可追溯的 Ubuntu 官方历史包；其他 Synopsys 产品中的候选只作线索，不自动跨产品复用；
2. `file` 显示 ELF 64-bit x86-64；
3. `readelf -d` 的 SONAME 与目标 `DT_NEEDED` 精确一致；
4. 所有 `DT_NEEDED` 传递依赖可解析；
5. GNU symbol version 不要求当前系统不存在的版本；
6. 在产品局部、干净环境中可加载；
7. 记录来源、包版本、SHA-256 和目标产品。

文件名看似匹配但 SONAME 不匹配必须拒绝。特别是某些其他 EDA 安装中名为 `libncurses.so.5` 的文件，内部可能仍是 `libncurses.so.6`，不得跨厂商复制或部署。

## 运行验证规则

- 先做 wrapper syntax 与 structure；候选完整脚本无法通过目标 shell `-n` 时标记 `BLOCKED_VENDOR_SCRIPT`，不跳过检查；
- `prepare/apply/verify` 可重复指定 `--product`，被阻塞产品不得阻止其他独立产品事务；
- 再做 version/id/help；
- 再做最小 Tcl/Verilog licensed batch；
- 只有 batch 通过且 DISPLAY 可用时才做限时 GUI smoke；
- timeout 后测试器主动 SIGTERM 属于预期，signal 6/11 或 loader error 属失败；
- license feature 缺失与 OS/ABI 故障分别报告。
