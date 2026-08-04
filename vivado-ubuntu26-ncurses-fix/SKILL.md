---
name: vivado-ubuntu26-ncurses-fix
description: >-
  Fix Xilinx Vivado/Vitis 2025.2.1 install hanging on Ubuntu 26.04 at
  "Generating installed device list" (missing libncurses.so.5 in the dynamic
  lib search path, ldlibpath.sh doesn't recognize Ubuntu 26). Use when the
  installer stalls, vivado batch prints "libncurses.so.5: cannot open shared
  object file", or installed_devices.txt is never generated.
---

# Vivado 2025.2.1 在 Ubuntu 26.04 上安装卡死 修复

## 适用场景 (When to use)

- Xilinx 安装器在 **Ubuntu 26.04**（或任何 ldlibpath.sh 未识别的发行版）上装 Vivado/Vitis 2025.2.1。
- 安装卡在最后一步 **`Generating installed device list`**，进度条一直不结束。
- `vivado -mode batch` 启动时出现：
  `couldn't load file "libxv_commontasks.so": libncurses.so.5: cannot open shared object file: No such file or directory`
- `Vivado/data/parts/installed_devices.txt` 永远生成不出来。
- 重装后 Vivado 直接运行时报同样的 ncurses 错误。

## 症状 (Symptoms)

1. 安装器进程存活，但最后一步日志停在：
   `Executing script Generating installed device list: .../vivado -mode batch -source .../xlpartinfo.tcl`
2. 派生的 `vivado` 批处理子进程长时间 **CPU 0%、状态 `Sl+`、wchan=`futex_do_wait`**，只开 3 个 fd。
3. `installed_devices.txt` 不存在。
4. 手动跑 `vivado -version` 正常，但 `vivado -mode batch -source xx.tcl` 时脚本**静默不执行**（Tcl 初始化中断），只输出 ncurses 警告。

## 根因 (Root cause)

- Vivado 的 `bin/ldlibpath.sh` 的 Ubuntu 分支只识别 `18*/20*/22*/24*`：
  ```sh
  *ubuntu*)
    distro=Ubuntu
    case "$rl" in
      18*) distrover=18 ;;
      20*) distrover=20 ;;
      22*) distrover=22 ;;
      24*) distrover=24 ;;
      *) distrover= ;;
    esac
  ```
- **Ubuntu 26.04 匹配不到 `distrover`** → 输出的搜索路径是 `$P/Ubuntu:$P`，**缺 `$P/Ubuntu/24`**。
- 而 Vivado 需要的 `libncurses.so.5` / `libtinfo.so.5` **只存在于 `lib/lnx64.o/Ubuntu/24/`**（AMD 为 Ubuntu 24 专门打包的）。
- 于是 Tcl 初始化加载 `libxv_commontasks.so` 失败 → 安装器最后一步的 Vivado 子进程死锁在 futex。
- 附带：安装器的 `setupLibTinfo.sh`/`setupLibNCurses.sh` 是 **SuSE 专用**，Ubuntu 上直接"nothing to do"，不会帮你装。

## 修复 (Fix)

库本身 Vivado **自带**，只需让它们进入动态库搜索路径。核心动作：把 `Ubuntu/24/` 里的库复制到**始终在搜索路径里**的 `lib/lnx64.o/` 根级。

直接跑本 skill 附带的脚本（幂等，可重复执行）：

```bash
bash scripts/vivado_fix_ncurses.sh
```

脚本做三件事：
1. 修复已安装产品 **Vivado / Vitis / PDM** 的 `lib/lnx64.o/` 根级（这是"直接运行 Vivado"正常的关键）。
2. 修复**安装器目录**的 `lib/lnx64.o/` 根级（`LD_LIBRARY_PATH` 自带该目录，保证**重装不再卡死**）。
3. 若 `installed_devices.txt` 缺失，自动重新生成。

路径可覆盖：`XILINX_INSTALL_ROOT=... XILINX_INSTALLER_DIR=... bash vivado_fix_ncurses.sh`

### 手动等价命令（不想用脚本时）

```bash
# 1. 修复已安装的三个产品
for P in Vivado Vitis PDM; do
  SRC=/opt/eda/Xilinx/2025.2.1/$P/lib/lnx64.o/Ubuntu/24
  cp "$SRC/libncurses.so.5" "$SRC/libtinfo.so.5" /opt/eda/Xilinx/2025.2.1/$P/lib/lnx64.o/
done

# 2. 修复安装器目录（防重装卡死，一劳永逸）
INST=/path/to/FPGAs_AdaptiveSoCs_Unified_SDI_2025.2.1_0320_0604
cp /opt/eda/Xilinx/2025.2.1/Vivado/lib/lnx64.o/Ubuntu/24/libncurses.so.5 \
   /opt/eda/Xilinx/2025.2.1/Vivado/lib/lnx64.o/Ubuntu/24/libtinfo.so.5 \
   "$INST/lib/lnx64.o/"
```

## 验证 (Verification)

```bash
# 1. 干净启动（无 ncurses 警告）
/opt/eda/Xilinx/2025.2.1/Vivado/bin/vivado -version

# 2. batch 模式真的执行脚本（关键：修复前此脚本静默不跑）
echo 'puts "BATCH_OK"; exit' > /tmp/t.mcl
/opt/eda/Xilinx/2025.2.1/Vivado/bin/vivado -nolog -nojournal -mode batch -source /tmp/t.mcl
# 应输出 BATCH_OK，且无 "libncurses.so.5" 报错

# 3. 器件列表存在
ls -la /opt/eda/Xilinx/2025.2.1/Vivado/data/parts/installed_devices.txt
```

## 注意事项 (Notes)

- **重装后必须重跑一遍脚本**：全新解压不会带根级副本，只有 `Ubuntu/24/` 有库。
- 安装器目录的修复是持久的（安装器目录不会被重装清空），所以重装**过程**本身不卡。
- 系统级方案（可选，更彻底）：把 `libncurses.so.5` 也放进 `/usr/lib/x86_64-linux-gnu/` 并装 `libtinfo5`，则动态链接器走系统路径、与脚本无关。Ubuntu 26.04 官方源没有 `libtinfo5` 包，需下载 deb 或直接用 Vivado 自带库。

## 其他已知坑 (Gotchas)

- **卸载器 NPE**：如果上次安装是强杀的、`~/.Xilinx/registry/` 为空，卸载器 GUI 会报 `InstallationRecord.setSelectedPacakge(...) NPE` 起不来。此时手动 `rm -rf /opt/eda/Xilinx`（内容 vv 所有可直接删，顶层目录若 root 所有会留下空壳，不影响重装）。
- **卸载器缺语言资源**：`.xinstall/2025.2.1/data/` 缺 `dynamic_language_bundle.properties`/`idata.dat`，从安装器目录 `data/` 复制过去即可（若遇到）。
- **快捷方式残留**：每次安装会在 `~/.local/share/applications/` 生成带时间戳后缀的 `.desktop`，重装多次会产生失效残留，可按时间戳组清理。
- **xic 窗口**：安装收尾会弹 Xilinx Installer Client 窗口，无害，关掉即可。

## 参考文件

- `scripts/vivado_fix_ncurses.sh` — 幂等修复脚本
- `references/diagnosis.md` — 完整排查过程记录
