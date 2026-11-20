# Windows 宿主 → Linux：待实机验证

目标是在 Windows 保持运行时，把另一块物理盘上现有的 Linux 启动为虚拟机。当前尚未选定或验证虚拟化软件，不将 Linux 宿主的 UDisks2、KVM、磁盘节点或剪贴板参数直接套到 Windows。

1. 从 Windows 用 PowerShell 只读检查 `Get-Disk`、`Get-Partition`，核对 Linux 盘与 EFI 分区的位置、型号和容量。确认 Linux 已完整关机，未休眠；区分 Linux 盘、Windows 启动盘和共享数据盘。如果 Linux 引导依赖 Windows 所在盘的 EFI 分区，不能直接把宿主正在使用的整盘交给客机。
2. 核对实际安装的虚拟化软件与版本，再查其官方文档是否支持物理盘、UEFI 和写入隔离。若做不到原盘可靠只读，不用直接写原盘代替，先考虑独立镜像。未经确认不脱机磁盘、不改权限或分区。
3. 实测后记录软件版本、磁盘接入与隔离方式、是否能正常进入 Linux，以及显示、输入和双向剪贴板验证结果。仅在实际验证后更新 catalog 平台和依赖。
