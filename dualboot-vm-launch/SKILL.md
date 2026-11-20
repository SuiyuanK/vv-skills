---
name: dualboot-vm-launch
description: 在不重启当前宿主的情况下，把另一块盘上已安装的 Windows 或 Linux 作为虚拟机启动，并维护启动器与排查引导、显示、输入和剪贴板。已验证 Linux 宿主用 QEMU/KVM 启动 Windows，以及 Windows 宿主用 QEMU/WHPX 启动 CachyOS。
---

# 把现有双系统作为虚拟机启动

先区分宿主和客机。Linux 宿主启动 Windows 按下面的流程。Windows 宿主启动现有 CachyOS，或维护桌面启动模式、排查虚拟 NVMe 和输入焦点时，读 [Windows 宿主启动 CachyOS](references/windows-host-linux-guest.md)。本 skill 面向既有双系统。两侧的每次只读启动均使用全新写入层，旧差量不复用、不合并回原盘。

## Linux 宿主 → Windows：先确认原盘

1. 用 `lsblk`、`findmnt`、`efibootmgr -v` 核对磁盘型号、EFI 分区 PARTUUID、Windows 系统分区和宿主根分区。Windows EFI 与系统分区同盘时才直接按单盘方案执行。跨盘引导先查清依赖，不把宿主系统盘或共享数据盘顺手交给客机。
2. 确认原生 Windows 已完整关机，未休眠或使用快速启动；开了 BitLocker 或设备加密时，让用户自己确认备有恢复密钥，不索取密钥。检查目标分区在宿主未挂载，不强制卸载。沙箱可能隐藏设备节点或把挂载显示为只读；必要时获批在宿主复查。
3. 检查 `/dev/kvm` 和所需依赖；已有应用菜单项时，先读对应 `.desktop` 的 `Exec`、`Icon` 及脚本。不要另造会漂移的启动命令。

## Linux 宿主的默认只读模式

- 通过 UDisks2 `Block.OpenDevice` 以 `r` 和 `O_EXCL` 打开已核实的整盘；检查文件描述符的访问模式及设备号。以普通用户把句柄传给 QEMU，不用 root 跑 QEMU、不永久放宽块设备权限。
- QEMU 使用 `host_device → raw → qcow2`，前两层明确只读。每次在调用工作区的 `tmp/` 创建唯一运行目录和新的写入层；退出后只清理本次目录，不复用旧层、不合并回原盘。原生启动会改变底盘，旧差量不能安全套回。
- UEFI 变量和虚拟 TPM 状态独立于一次性写入层，保存在用户专用目录，权限限当前用户。不自动重置或清除；客机内的 PIN 凭据和应用改动属于客机磁盘，丢弃写入层后不会保留。需要长期保存客机改动、同时继续原生启动时，改用独立磁盘镜像。
- 仅在用户明确要求时提供可写模式：单独二次确认，默认取消，提醒备份、完整关机和保持分区未挂载；独占读写原盘，不经差量、不做自动合并。不要在验证启动器时用实体盘实测写入。

启动参数、GNOME 弹窗、Windows 登录与排障见 [本机配置与验证](references/configuration.md)。
