# Windows 宿主启动 CachyOS

## 启动现有双系统

1. 确认实体 Linux 上次已完整关机或重启，且未休眠。用 `Get-Disk`、`Get-Partition` 核对持久磁盘标识、型号、容量、分区表和扇区大小。EFI 与 Linux 根分区应位于同一个独立实体盘。排除 Windows 启动盘以及宿主已挂载的分区。发现跨盘引导或标识变化时先重新确认设备。
2. 检查 QEMU、随附 EDK2 固件、WHPX 和可用内存提交量。读取 `\\.\PhysicalDriveN` 需要管理员权限。本机从桌面快捷方式发起 UAC，再确认完全关机。保留 Windows 盘在线状态和实体盘权限。
3. 启动前以 QMP `query-named-block-nodes` 核实 `host_device → raw → qcow2` 的前两层为只读，且只有 QCOW2 可写，再恢复虚拟 CPU。每次在调用工作区的 `tmp/` 创建独立目录，保存差量文件、虚拟 UEFI 变量和日志。每次使用新差量，已有差量仅供诊断，不复用或合并回实体盘。需要持久保存客机改动时，使用独立磁盘镜像。

## 已验证的本机配置

| 项目 | 设置 |
| --- | --- |
| 虚拟化 | QEMU 11.1.0，`whpx,kernel-irqchip=off` |
| CPU、内存 | `-cpu host -smp 4 -m 16384` |
| 主板、固件 | Q35，`pic=off`，EDK2 UEFI |
| 磁盘 | 虚拟 SATA，逻辑扇区 512 字节，物理扇区 4096 字节 |
| 显示、鼠标 | GTK、VirtIO 显卡、USB Tablet，`grab-on-hover=off` |
| 网络 | 模拟 E1000e，用户态 NAT |

4 vCPU 和 16 GiB 已启动到图形登录界面，用户确认鼠标与键盘行为符合预期。虚拟 NVMe 能被 UEFI 枚举，但加载启动项返回 `Not Found`，同一磁盘改用 SATA 可引导。TCG 曾卡在 GRUB 加载 initramfs 的阶段。Windows 方向的双向剪贴板尚未实测。

## 本机入口与排查

- TMP 工作区的 `Scripts/windows/cachyos-vm.py` 是本机启动器，`focused_win_keys.py` 为其键盘辅助模块。桌面「CachyOS 虚拟机」快捷方式用本机 Python 3 的 `pythonw.exe` 运行 `-B "<启动器路径>" --desktop`。管理员 PowerShell 可用 `py -3 -B .\Scripts\windows\cachyos-vm.py --clean-shutdown`。
- `--check` 只读检查依赖和目标盘身份，`--test` 使用合成镜像验证写入隔离。正式运行日志在 TMP 工作区的 `tmp/cachyos-vm/`。
- USB Tablet 提供绝对鼠标定位，点击其他窗口即可切换焦点。本机辅助模块仅在该 QEMU 进程的窗口处于前台时截获左右 Win 键，经进程内的 QMP 标准输入转发成 Linux Super 键。切走焦点时释放客机中的 Win 键。普通鼠标、按键、剪贴板由各自原有机制处理。
- 修改虚拟硬件前先正常关闭客机。排查时区分 QEMU 进程是否仍在运行、UEFI 是否找到引导项、GRUB 是否启动内核，以及客机是否到达登录界面。
