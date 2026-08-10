---
name: qqmusic-linux-fix
description: >-
  Diagnose and fix QQ 音乐 (QQ Music) desktop client that
  crashes on startup ("闪退") on Ubuntu 26.04 / Linux graphics
  stacks. Covers read-only diagnosis via terminal launch,
  confirming the GPU-sandbox workaround, and a user-local
  .desktop launcher override so the fix survives package
  updates. Strict scope: official /opt/qqmusic client on
  Ubuntu 26.04 (x86_64, Linux kernel major 7).
---

# QQ 音乐 Ubuntu 26.04 启动闪退修复

本 skill 处理 QQ 音乐桌面客户端在 Ubuntu 26.04 / 新版图形栈上
启动即闪退的问题（旧 Electron 与 GPU compositor 不兼容）。

严格适用范围：

- 官方 / 常规安装的 QQ 音乐桌面客户端（Electron 版，例如
  `/opt/qqmusic/qqmusic`）；
- x86_64；
- Ubuntu 26.04（`ID=ubuntu`、`VERSION_ID=26.04`）；
- Linux kernel major 7；
- 症状：双击桌面图标立刻闪退，终端无缺库报错。

其他发行版、架构、非 Electron 版本、或真实缺失动态库的报错
必须停止，不能盲目套用 GPU 修复或改写启动器。

## 诊断顺序

1. **确认发行版与架构确实属于适用范围内**，否则停止。
2. **先用终端启动看真实报错**，不要只从桌面图标双击：
   ```bash
   qqmusic
   ```
3. 区分两类根因：

   - **缺动态库**：输出形如
     ```text
     error while loading shared libraries: libXXX.so: cannot open shared object file
     ```
     → 这是缺失依赖，走 `apt` 安装对应 `-dev`/运行时包；
     **不属于本 skill 的 GPU 修复范围**，按普通缺库处理。
   - **GPU/图形栈崩溃**：输出包含
     ```text
     FATAL: gpu_data_manager_impl_private.cc
     The display compositor is frequently crashing
     ```
     → 是本 skill 的修复目标。前面的
     `UnhandledPromiseRejectionWarning` 和 `login refresh fail`
     与闪退主因无关，不要被它们误导。

## 修复步骤

### 1. 确认可用参数

依次测试，找到有效启动方式（任一成功即停）：

```bash
qqmusic --disable-gpu --disable-gpu-compositing
qqmusic --disable-gpu --disable-gpu-compositing --ozone-platform=x11
LIBGL_ALWAYS_SOFTWARE=1 qqmusic --use-gl=swiftshader --disable-gpu-sandbox
qqmusic --disable-gpu-sandbox
```

已知结论：旧 Electron 客户端在 Ubuntu 26.04 上，通常是
`--disable-gpu-sandbox` 有效（`--disable-gpu` / swiftshader
单独使用不一定有效）。

若终端能启动，**按 Ctrl+C 关闭属于正常现象，不是闪退**。

### 2. 让桌面图标永久使用有效参数

目标：不修改系统文件，让包更新也不会覆盖修复。

找到启动器：

```bash
find /usr/share/applications ~/.local/share/applications \
  -iname '*qq*music*.desktop' -print 2>/dev/null
```

查看实际启动命令（不要乱猜）：

```bash
grep '^Exec=' /usr/share/applications/qqmusic.desktop
```

把系统启动器复制为个人版本，并只注入有效参数（以
`--disable-gpu-sandbox` 为例）：

```bash
mkdir -p ~/.local/share/applications

if [ -e ~/.local/share/applications/qqmusic.desktop ]; then
  printf '%s\n' '已存在个人 QQ 音乐启动器，未作覆盖。'
else
  cp /usr/share/applications/qqmusic.desktop \
     ~/.local/share/applications/qqmusic.desktop
  sed -i 's|^Exec=/opt/qqmusic/qqmusic %U$|Exec=/opt/qqmusic/qqmusic --disable-gpu-sandbox %U|' \
    ~/.local/share/applications/qqmusic.desktop
fi
```

校验：

```bash
grep '^Exec=' ~/.local/share/applications/qqmusic.desktop
# 预期：Exec=/opt/qqmusic/qqmusic --disable-gpu-sandbox %U
```

若菜单未即时更新，注销再登录，或运行
`update-desktop-database ~/.local/share/applications`。

## 安全边界

- 优先在 **个人 `.desktop`** 中注入参数，不直接改
  `/usr/share/applications/qqmusic.desktop`；只有用户明确要求
  且已确认原始 `Exec=` 行时才修改系统文件（并先备份）。
- 不修改 `/opt/qqmusic` 内任何文件。
- 不编写 `sudo` 自动安装命令到系统库目录。
- 临时产物、日志统一写入调用工作区 `./tmp`，不写系统 `/tmp`。
- `--disable-gpu-sandbox` 会降低 GPU 进程隔离，仅作为旧客户端
  无法正常启动时的绕行方案，并在结果中提示优先更新到官方新版。

## 参考资料与测试

- `references/diagnosis.md`：根因与报错判别表。
- `tests/test_qqmusic_fix.py`：合成生命周期测试。
