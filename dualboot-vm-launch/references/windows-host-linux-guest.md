# Windows 宿主启动 CachyOS

## 启动现有双系统

1. 确认实体 Linux 上次已完整关机或重启，且未休眠。用 `Get-Disk`、`Get-Partition` 核对持久磁盘标识、型号、容量、分区表和扇区大小。EFI 与 Linux 根分区应位于同一个独立实体盘。排除 Windows 启动盘以及宿主已挂载的分区。发现跨盘引导或标识变化时先重新确认设备。
2. 检查 QEMU、随附 EDK2 固件、WHPX 和可用内存提交量。读取 `\\.\PhysicalDriveN` 需要管理员权限。本机从桌面快捷方式发起 UAC，再选择启动模式。保留 Windows 盘在线状态和实体盘权限。
3. 在恢复虚拟 CPU 前，用 QMP `query-named-block-nodes` 核实实际磁盘模式。

## 桌面启动模式

1. **只读启动（推荐）**。QEMU 使用 `host_device → raw → qcow2`，实体盘和 RAW 层均只读。每次启动都在 TMP 工作区的 `tmp/cachyos-vm/` 下建立唯一运行目录并新建 `guest.qcow2`。目录内已有同名写入层时停止。旧差量保留用于诊断，不复用、不覆盖、不合并回实体盘。虚拟 UEFI 变量和日志也写在本次运行目录内。
2. **直接写入实体盘**。仅在用户明确选择后显示第二次确认，默认取消。提醒先备份，确认实体 Linux 完整关机且 Windows 未挂载其分区。QEMU 通过可写的 `host_device → raw` 接入，客机写入直接落在实体盘。磁盘身份或分区布局不符、宿主已挂载、原盘只读、已有实例运行或 Windows 拒绝访问时停止启动。保持现有磁盘联机状态和权限。此模式的 QMP 拓扑和实际写入仅在合成镜像上验证，实体盘写入尚未实测。
3. **取消**。退出启动流程，不创建运行目录或启动 QEMU。

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

- TMP 工作区的 `Scripts/windows/cachyos-vm.py` 是本机启动器，`focused_win_keys.py` 为其键盘辅助模块。桌面「CachyOS 虚拟机」快捷方式用本机 Python 3 的 `pythonw.exe` 运行 `-B "<启动器路径>" --desktop`。管理员 PowerShell 可使用 `py -3 -B .\Scripts\windows\cachyos-vm.py --clean-shutdown` 直接走只读流程。
- `--check` 只读检查依赖和目标盘身份，`--test` 使用合成镜像验证只读模式的写入隔离，以及直接模式写入底盘的行为。已用合成镜像连续验证两次只读启动创建独立 QCOW2，且第二次启动后第一个写入层的哈希保持一致。正式运行日志在 TMP 工作区的 `tmp/cachyos-vm/`。
- USB Tablet 提供绝对鼠标定位，点击其他窗口即可切换焦点。本机辅助模块仅在该 QEMU 进程的窗口处于前台时截获左右 Win 键，经进程内的 QMP 标准输入转发成 Linux Super 键。切走焦点时释放客机中的 Win 键。普通鼠标、按键、剪贴板由各自原有机制处理。
- 修改虚拟硬件前先正常关闭客机。排查时区分 QEMU 进程是否仍在运行、UEFI 是否找到引导项、GRUB 是否启动内核，以及客机是否到达登录界面。
