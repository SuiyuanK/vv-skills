# 完整排查过程记录

> 环境：Ubuntu 26.04 (resolute) / Vivado & Vitis 2025.2.1 / 安装器 `FPGAs_AdaptiveSoCs_Unified_SDI_2025.2.1_0320_0604`（离线包，96GB payload）

## 时间线

| 时间 | 事件 |
|---|---|
| 22:28 | 安装器启动 |
| 22:47 | 所有安装脚本完成：qemu、setupLibTinfo、setupLibNCurses、vlm(license)、创建快捷方式 |
| 22:47:07 | 最后一步 `Generating installed device list` 启动 `vivado -mode batch -source xlpartinfo.tcl` |
| 22:47~次日 | Vivado 子进程死锁，`installed_devices.txt` 永远不生成，安装器卡死 |
| 01:08 | 修复方案验证：重装后该步骤由安装器自动完成 |

## 排查步骤

### 1. 定位卡住的位置

```bash
# 找到卡住的进程
ps aux | grep -iE 'vivado|installer|xilinx'
# 安装器日志最后一行 = 卡住的步骤
tail -30 ~/.Xilinx/xinstall/xinstall-*.log
# 关键线索：日志停在
#   Executing script Generating installed device list: .../vivado -mode batch -source .../xlpartinfo.tcl
```

判断标准（进程状态）：
```bash
cat /proc/<vivado_pid>/status | grep -E 'State|Threads'
# State: S(sleeping), wchan=futex_do_wait, CPU 0, 只有 2-3 个 fd
# => 启动早期就死锁，不是正常慢
```

### 2. 手动复现，排除"安装器问题"

```bash
# Vivado 本体能启动
echo 'puts "ALIVE"; exit' | vivado -mode batch
# 但 -source 脚本静默不执行（关键区别！）
echo 'puts "OK"; exit' > /tmp/t.mcl
vivado -mode batch -source /tmp/t.mcl
# 输出只有：libncurses.so.5 警告，脚本没跑
```

### 3. 揪出缺库

```bash
# 警告指向 libxv_commontasks.so → 缺 libncurses.so.5
# 但库其实"存在"
ls Vivado/lib/lnx64.o/Ubuntu/24/libncurses.so.5
# 关键：ldlibpath.sh 生成什么路径
Vivado/bin/ldlibpath.sh /opt/eda/Xilinx/2025.2.1/Vivado/lib/lnx64.o
# 输出: .../lib/lnx64.o/Ubuntu:.../lib/lnx64.o   ← 缺 /Ubuntu/24 !
```

### 4. 根因确认

```bash
grep -E 'ID|VERSION_ID' /etc/os-release   # VERSION_ID="26.04"
sed -n '/ubuntu)/,/esac/p' Vivado/bin/ldlibpath.sh
# 只认 18/20/22/24，26 匹配不到 → distrover 为空 → Ubuntu/24 不进搜索路径
```

### 5. 修复并验证

复制 `Ubuntu/24/` 库到根级 → `vivado -mode batch` 恢复执行脚本、`installed_devices.txt` 生成成功。

## 关键洞察

1. **`-version` 不触发问题**，必须用 `-mode batch -source` 测试——`libxv_commontasks.so` 是 Tcl applet 初始化时才加载的。
2. 安装器派生 vivado 的 `LD_LIBRARY_PATH` **包含安装器目录的 `lib/lnx64.o`**，所以在那里放库能治"重装卡死"，且安装器目录不会被清空。
3. 安装器的 `setupLibTinfo.sh` 是 SuSE 专用，Ubuntu 上直接跳过，别指望它。
4. `libncurses.so.5` 是 Ubuntu 24 专属库（ncurses5 在新系统被移除），Vivado 为每个支持的发型版都打包了一份。

## 测试用命令速查

```bash
# 基本启动测试
echo 'puts "VIVADO_ALIVE_OK"; exit' | vivado -mode batch

# batch + source 测试（暴露 ncurses 问题的关键）
echo 'puts "BATCH_OK"; exit' > /tmp/t.mcl
vivado -nolog -nojournal -mode batch -source /tmp/t.mcl

# 生成器件列表（手动执行安装器卡住的那步）
vivado -nolog -nojournal -mode batch \
  -source /opt/eda/Xilinx/2025.2.1/Vivado/scripts/sysgen/tcl/xlpartinfo.tcl \
  -tclargs /opt/eda/Xilinx/2025.2.1/Vivado/data/parts/installed_devices.txt
```
