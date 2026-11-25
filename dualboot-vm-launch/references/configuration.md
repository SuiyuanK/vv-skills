# Linux 宿主 → Windows：配置基线与验证

## 已验证的环境

- CachyOS x86_64、GNOME Wayland、QEMU 11.1.3；Windows 为另一块 NVMe 上已安装的 UEFI 系统。真实验证了只读启动、进入 Windows 桌面和 2560×1440 图像输出。可写启动器分支仅做过模拟验证。
- Arch 系依赖：`qemu-desktop`（含本流程所需 QEMU/GTK 组件）、`edk2-ovmf`、`swtpm`；启动器需 `zenity`、Python 3 + PyGObject、UDisks2、`lsblk`，菜单检查用 `desktop-file-validate`。先核对本机包和命令，再给缺失依赖的安装方法；不擅自安装。
- 已有启动脚本在 TMP 工作区的 `scripts/linux/tools/windows-qemu-readonly.py`；用户菜单项是 `~/.local/share/applications/windows-qemu-readonly.desktop`。默认状态目录是 `~/.local/share/windows-qemu-readonly/`，包含 `OVMF_VARS.fd`、`tpm2-state/` 和菜单用的 SVG。定位实际工作区和分区，不从此记录猜盘符或写死主机路径。

## 参数与排障

| 项目 | 本机可用配置及注意事项 |
| --- | --- |
| CPU / 存储 | `q35,accel=kvm`，`Skylake-Client-noTSX-IBRS`，4 核 / 4 线程、16 GiB，系统盘呈现为虚拟 NVMe。早期 `-cpu host` 下出现过启动卡住；保留已跑通的组合，逐项对比，不把问题归因于核数或 SATA 单一变量。 |
| 引导 / TPM | OVMF 4 MiB，代码固件只读、使用单独的可写变量文件，未启用 Secure Boot。用持久状态目录的 `swtpm socket --tpm2` 提供虚拟 TPM，QEMU 接 `tpm-crb`。套接字和日志放本次运行目录；可用相对套接字路径避免 Unix 路径长度限制。 |
| 显示 | 显式 `-device VGA,id=winvideo,edid=on,xres=2560,yres=1440`。若需 1080p，改为 1920×1080。曾遇到仅加 `-global VGA.xres/yres` 导致参数未应用、无可截图控制台；检查实际输出像素而不是窗口大小，`Zoom To Fit` 只缩放。Windows 下拉框灰掉时先核查虚拟 VGA 与 OVMF。 |
| 指针 / 键盘 | `qemu-xhci` + `usb-tablet`，确认绝对坐标指针已激活，解决双指针偏移。GTK 的 `Grab On Hover` 按用户习惯开启；它不自动同步 Num Lock，用 Windows 屏幕键盘可单独切换客机状态。 |
| 网络 / 剪贴板 | `e1000e` + 用户态 NAT，不转发端口。GTK 开 `clipboard=on`，`qemu-vdagent` 用 `clipboard=on,mouse=off`，经 virtio-serial 的 `com.redhat.spice.0` 连 SPICE Guest Tools。端口已打开不等于复制成功；登录后用无敏感信息的文字双向测试。 |

Windows 若停在 TianoCore 标志，不要仅从标志断定是 UEFI 卡住。若能进入 Windows 恢复环境，先看 `SrtTrail.txt` 或停止代码；日志中的 `0x0` 通常只表示该项检查执行成功。不要为了启动排障清 TPM、重置系统或修复原盘。

Windows Hello PIN 不是账户密码。实体 TPM 直通在本机用 `cancel-path=/dev/null` 绕过缺失接口后能到锁屏，但原生 PIN 仍不可用；不要重试直通或清实体 TPM。只想少一次验证时，先确认 Windows 已允许密码登录且能用微软账户密码解锁，再考虑删除 PIN。区分原生和客机的登录设置；进桌面也不等于已实测密码解锁。

## 启动器

- 用同一个用户级 `.desktop`，`Terminal=false`，`Exec` 运行 Python 脚本，`Icon` 指向可解码的专用 SVG。先查是否有重复条目或菜单缓存，不靠重启 GNOME 作为首选验证。
- Zenity 用 `--question`、明确的 `--extra-button` 和适度宽度（本机约 350）；只读默认回车、取消不碰磁盘。额外按钮用标准输出区分，不能只看退出码。可写二次确认默认取消。
- 先验证桌面文件能被识别、图标可解码、所有按钮及磁盘节点配置正确。只读启动可验证实际分辨率、状态保存和本次目录清理；强制杀死进程时可能留下临时目录，不要在下次启动时复用或批量删除历史目录。
