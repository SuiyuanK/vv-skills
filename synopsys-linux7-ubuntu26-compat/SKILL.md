---
name: synopsys-linux7-ubuntu26-compat
description: >-
  Diagnose and transactionally adapt installed Synopsys SpyGlass X-2025.06,
  SCL 2024.06, DC/LC/ICC2 V-2023.12-SP3, and VCS/Verdi W-2024.09-SP1
  for x86_64 Ubuntu 26.04 with Linux kernel 7. Covers vendor wrapper Bashisms,
  SpyGlass platform and allocator failures, strict legacy-ABI reporting,
  normal-mode verification, and drift-safe rollback.
---

# Synopsys Ubuntu 26.04 / Linux 7 统一兼容适配

本 skill 统一处理当前主机上已确认的 Synopsys 兼容层，并保留原 SpyGlass skill 的全部诊断、事务补丁与验证能力。

严格适用范围：

- x86_64；
- Ubuntu 26.04；
- Linux kernel major 7；
- SpyGlass X-2025.06；
- SCL 2024.06；
- Design Compiler、Library Compiler、ICC2 V-2023.12-SP3；
- VCS、Verdi、`verdi_supp` W-2024.09-SP1。

其他版本、架构、发行版、内核或未知 wrapper 形态必须停止，不能模糊套用。

## 两个入口

### 多产品 wrapper 与 ABI 检查

```bash
python3 scripts/synopsys_compat.py inspect
python3 scripts/synopsys_compat.py prepare --workspace "$PWD" --product dc --product lc --product icc2 --product verdi
python3 scripts/synopsys_compat.py apply --workspace "$PWD" --product dc --yes --write-system
python3 scripts/synopsys_compat.py verify --workspace "$PWD" --product dc
python3 scripts/synopsys_compat.py rollback --manifest ./tmp/synopsys-linux7-ubuntu26-compat/apply-.../manifest.json --yes --write-system
```

`prepare` 只生成候选、备份和 manifest，不修改产品；`apply` 重新执行相同预检后才原子提交。`--product` 可重复使用，并使 VCS 等被阻塞产品不会影响其他产品；实际提交建议每次只指定一个产品，从而得到独立回滚 manifest。只做结构验证时使用：

```bash
python3 scripts/synopsys_compat.py verify --workspace "$PWD" --no-runtime
```

### SpyGlass 完整适配

原有 CLI 和功能完整保留：

```bash
python3 scripts/spyglass_compat.py diagnose
python3 scripts/spyglass_compat.py apply --workspace "$PWD" --yes --write-system
python3 scripts/spyglass_compat.py verify --workspace "$PWD"
python3 scripts/spyglass_compat.py rollback --manifest MANIFEST --yes --write-system
```

SpyGlass 的 Linux 7 taxonomy、Ubuntu 26.04 精确 host gate、dash/Bash wrapper、batch/GUI system allocator selector、optional compile 和 GUI smoke 行为不变。详见 `references/diagnosis.md` 与 `references/patch-matrix.md`。

## 多产品自动变换

`scripts/synopsys_compat.py` 只修改五个已验证目标：

1. DC `bin/snps_shell`：两处 `test` 的 `==` 改为 POSIX `=`，继续使用 `/bin/sh`；
2. LC `bin/snps_shell`：同样的 POSIX 最小修复；
3. ICC2 `bin/icc2_shell`：已有 `[[ =~ ]]`，精确改为 Bash shebang；
4. VCS `bin/vcs`：虽含 function/local/array/`[[ ]]`，但当前 W-2024.09-SP1 文件改为 Bash 后在供应商脚本内部产生未配对 `else`；候选会被完整 `bash -n` 标记为 `BLOCKED_VENDOR_SCRIPT`，**不会自动改 shebang**，`llib -> vcs` 同样保持原状；
5. Verdi `bin/.wrapper`：已有 array/`[[ ]]`/source，精确改为 Bash；所有指向它的公共命令自动受益。

不会修改 SYN/LC 的 `snps_common.sh` 平台映射，不会修改健康的 SCL license server，也不会给 VCS/Verdi复制 SpyGlass allocator 修复。

## 状态与事务

- `ORIGINAL`：精确已知原始结构；
- `PARTIAL`：同一目标只存在部分已知变换；
- `PATCHED`：目标语义已完整存在；
- `UNEXPECTED`：锚点重复、缺失、冲突、未知 shebang、符号链接或非普通文件；
- `MISSING`：固定 release 的目标缺失；
- `BLOCKED_VENDOR_SCRIPT`：已知最小变换后的完整脚本无法通过目标 shell 语法检查，必须保持未修改并由供应商补丁或受支持版本解决；
- `BLOCKED_DEPENDENCY`：wrapper 可修，但完整运行仍缺经验证的旧 ABI。

事务会保存动态 SHA-256、owner/group/mode/mtime/xattr，要求工作区 `./tmp` 与产品目标位于同一文件系统，执行 staged syntax/semantic validation、pre-commit drift check、原子替换、失败恢复和 drift-safe rollback。

所有日志、备份、staging、Tcl/Verilog 和运行产物必须位于调用工作区的 `./tmp`。脚本不调用 sudo，不写系统 `/tmp`，也不修改 `.zshrc`/`.bashrc`。

## 旧 ABI 处理边界

当前 Ubuntu 26 可能缺失：

- `libncurses.so.5`、`libtinfo.so.5`；
- `libpython3.6m.so.1.0`；
- `libpng12.so.0`；
- `libsasl2.so.3`；
- Verdi 需要的 `libxml2.so.2`（系统可能只有新 SONAME）。

本版自动化只报告 Synopsys 树内候选及其真实 SONAME、ELF class、machine 和直接 `DT_NEEDED`，**不自动部署运行库**。候选可能来自其他 Synopsys 产品，只能视为线索，不能据此跨产品复用。只有来源可追溯、目标产品/版本匹配、ELF64 x86-64、内部 SONAME 精确匹配、符号版本与传递依赖均验证通过的库才可进入后续产品局部 bundle。

明确禁止：

- 不把 `.so.6` 改名或链接成 `.so.5`；
- 不把 libpng16 冒充 libpng12；
- 不复制或替换 glibc、`libpthread.so.0`、动态加载器；
- 不复用 Xilinx 等其他厂商安装树中的库；
- 不向 `/usr/lib` 写文件；
- 不设置全局 `LD_LIBRARY_PATH`。

如果无合格 Synopsys payload 或 Ubuntu 历史包，状态保持 `BLOCKED_DEPENDENCY`，并建议使用 Synopsys 官方兼容补丁或受支持 Linux 容器/虚拟机。

## Verdi supplement

`verdi_supp/W-2024.09-SP1` 是主 Verdi 的补充包，不是第二套独立 Verdi。当前 `inspect` 会检查同版本与 post-install 状态，但不会盲跑会移动大量目录的 vendor 脚本，也不会把 supplement 的 `bin` 加入 PATH。只有 source-to-destination 映射、冲突规则和完整回滚边界验证后才可自动集成。

## 文件

- `scripts/synopsys_compat.py`：多产品 inspect/prepare/apply/verify/rollback；
- `scripts/spyglass_compat.py`：SpyGlass 完整兼容入口；
- `references/multi-product-matrix.md`：逐产品修复与阻塞矩阵；
- `references/abi-findings.md`：当前安装树的 x86-64 候选、跨产品边界与 VCS 供应商脚本证据；
- `references/diagnosis.md`、`references/patch-matrix.md`：SpyGlass 原有证据；
- `tests/test_synopsys_compat.py`、`tests/test_spyglass_compat.py`：合成事务与回归测试。
