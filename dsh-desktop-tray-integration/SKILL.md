---
name: dsh-desktop-tray-integration
description: "Build or repair a Linux/GNOME desktop shortcut and system tray (StatusNotifierItem/AppIndicator) for dsh web — launcher wrapper with fixed port and authenticated-URL caching, Python Gio tray with double-click Activate and a 3-item DBusMenu (open/restart/quit), symbolic icon, tray lifecycle tied to dsh web. Use when the user asks for a DSH desktop icon, tray icon/menu, quick launch, restart/quit actions, or when an existing dsh web launcher/tray breaks. 触发场景：给 dsh web 加桌面图标或系统托盘图标、托盘菜单、双击打开、重启/退出、或修复已有 dsh web 托盘与启动器。"
---

# DSH Web 桌面图标 + 系统托盘集成

为一台 Linux/GNOME 机器上的 dsh web 添加：桌面快捷方式（图标 + 启动/复用/停止）、顶栏托盘图标（双击打开、右键 打开/重启/退出、随服务退出而消失），不修改 DSH 源码、不新增依赖。

**已在 CachyOS/Arch + GNOME Shell 51.1 + DSH 0.2.2-rc.1 + AppIndicator 扩展 ACTIVE 的机器上完整验证。**

- 适用 Agent/平台：DSH Web（dsh web）在 Linux/GNOME 上；交互依赖 GNOME AppIndicator（StatusNotifierItem）扩展。
- 依赖：dsh web、GNOME Shell + AppIndicator 扩展、python3 + PyGObject（gi）、notify-send、xdg-open、ss、gtk-update-icon-cache；生成桌面图标尺寸用 ImageMagick（或其他缩放工具）。
- 已验证范围：CachyOS/Arch + GNOME Shell 51.1 + DSH 0.2.2-rc.1 + AppIndicator 扩展 ACTIVE；其他发行版/GNOME 版本按同样契约实现但未实测。

## 产物与整体架构

    ~/.local/share/applications/<app>.desktop        # 桌面入口 + 右键 Stop 动作
    ~/.local/bin/<app>-launcher                      # bash 启动器：启动/复用/停止/托盘生命周期
    ~/.local/bin/<app>-tray                          # Python 托盘守护进程（SNI + DBusMenu）
    ~/.local/share/icons/hicolor/*/apps/<icon>.png   # 桌面图标（128/256/512）
    ~/.local/share/icons/hicolor/scalable/apps/<icon>-symbolic.svg  # 顶栏 symbolic 图标
    ${XDG_STATE_HOME}/<app>/                        # pid、url、tray.pid、日志

    .desktop → launcher ─┬─ dsh web --port PORT        （子进程，写 state/pid、state/url）
                         └─ setsid <app>-tray          （托盘，读同一 state；端口探测生命周期）

## 前置检查（先查，不擅自安装）

    gnome-shell --version
    gnome-extensions info appindicatorsupport@rgcjonas.gmail.com     # 必须「已启用 / ACTIVE」
    python3 -c "import gi; gi.require_version('Gio','2.0'); gi.require_version('GLib','2.0'); from gi.repository import Gio, GLib; print('gi ok')"
    busctl --user list | grep -E 'StatusNotifierWatcher|StatusNotifierItem'
    command -v notify-send xdg-open ss gtk-update-icon-cache

- GNOME 没有传统托盘，只能用 AppIndicator / StatusNotifierItem 扩展。
- 若 AppIndicator 扩展未安装：向用户说明用途后再安装（Arch 系优先 yay）：yay -S --needed gnome-shell-extension-appindicator，然后 gnome-extensions enable appindicatorsupport@rgcjonas.gmail.com。
- 缺少 python3 PyGObject 时同样先征得同意。

## A. 桌面快捷方式与启动器

1. 图标来源：DSH 自带前端 dist 里的官方图标：
   /usr/lib/node_modules/@deepseek-ai/dsh/node_modules/@deepseek-ai/dsh-web-frontend/dist/icon-512.png
   用 magick 生成 128/256/512 三个尺寸装入 ~/.local/share/icons/hicolor/<size>x<size>/apps/<icon>.png。
2. 写 .desktop：Exec 指向 launcher 绝对路径、Icon 用上面图标名、Categories=Development、Actions=Stop（右键停止）。最小模板：

    [Desktop Entry]
    Type=Application
    Name=DSH Web
    Comment=Run dsh web and open the browser UI
    Exec=/home/<user>/.local/bin/dsh-web-launcher
    Icon=dsh-web
    Terminal=false
    Categories=Development;
    Actions=Stop;

    [Desktop Action Stop]
    Name=Stop DSH Web server
    Exec=/home/<user>/.local/bin/dsh-web-launcher --stop

3. 启动器（参考实现：~/.local/bin/<app>-launcher；新机器按下列要点实现）关键点：
   - 端口固定：PORT 变量（默认示例 1314；避开 dsh web 默认 3080、选 1024-32767 之间且未占用）。测试可用环境变量 DSH_WEB_PORT 覆盖。
   - 认证 URL 只能从 dsh web 自身日志解析：正则 ^dsh web: (http\S*)$ 命中后写入 state/url（token 每次启动都变，不能硬编码）。
   - 复用：state/pid 存活 → xdg-open 缓存 URL 后退出。
   - 端口兜底：若指定端口已被其他实例占用（插件市场重启遗留的 detached 实例）→ 直接 xdg-open http://127.0.0.1:PORT/（浏览器 cookie 与 authority=host:port 绑定、签名密钥持久化，进程重启后同端口仍可登录）。
   - 串行化：exec 9>lock + flock，防止连点并发启动。
   - 启动 dsh web 与托盘时都必须 9>&-，避免子进程继承 flock fd 导致后续点击阻塞（已踩坑）。
   - --stop：先停托盘（TERM 等待→KILL，删 tray.pid），再停 dsh web，删 pid/url。
   - 启动成功后 setsid 拉起托盘，并写 state/tray.pid 供复用/停止：
       setsid "$TRAY_BIN" --port "$PORT" --state-dir "$STATE_DIR" --launcher "$SELF" --url-file "$URL_FILE" --pid-file "$PID_FILE" --log "$TRAY_LOG" >/dev/null 2>&1 9>&- &
4. chmod +x；可选 update-desktop-database ~/.local/share/applications。

## B. 托盘守护进程（核心）

### 为什么手写 SNI
libayatana-appindicator 这类库只能做到「点图标弹菜单」，无法满足「双击打开 + 右键菜单」。必须自己导出 StatusNotifierItem + DBusMenu。GNOME AppIndicator 扩展的行为（源码 indicatorStatusIcon.js 已核实）：
- 双击主键：若 introspect 中存在 Activate 方法 → 调用 Activate（这正是「双击快速打开」）
- 单击主键：等待 doubleClickTime 后弹出菜单
- 右键：弹出菜单；中键：SecondaryActivate

### D-Bus 契约
- 对象 /StatusNotifierItem → org.kde.StatusNotifierItem
  - 必需属性：Id、Menu（对象路径 /MenuBar）、Status（Active）；建议再给 Title、Category（ApplicationStatus）、ItemIsMenu=false、IconName、空 pixmap 属性。
  - 方法：Activate(x,y)、SecondaryActivate(x,y)、ContextMenu(x,y)、Scroll(i,s)、ProvideXdgActivationToken(s)、XAyatanaSecondaryActivate(u)。
  - **XML 里必须包含 Activate 方法**，否则扩展认为不支持激活，双击不会打开。
- 对象 /MenuBar → com.canonical.dbusmenu（静态菜单，revision=1）
  - 方法：GetLayout(i,i,as) → (u,(ia{sv}av))；GetGroupProperties(ai,as) → a(ia{sv})；GetProperty(i,s) → v；Event(i,s,v,u)；EventGroup；AboutToShow(i)→b；AboutToShowGroup。
  - 菜单项 id 任意固定值（示例 10=打开 / 20=重启 / 30=退出），属性至少给 label/enabled/visible/type/icon-name/children-display/toggle-type。
  - **GetLayout 的 children 必须是 av（variant 数组）**，不是 a(ia{sv}av)；否则 Gio 报 is_of_child_type 断言、GetLayout 返回 NULL。
- 注册：连接上导出对象后调用
      org.kde.StatusNotifierWatcher.RegisterStatusNotifierItem(唯一 bus 名)
  并监听 watcher 的 owner 变化（扩展重载/延迟启动后自动重注册）。

### Gio 实现要点（Python + PyGObject）
- 用 Gio.DBusNodeInfo.new_for_xml(...) 得到接口信息，然后
      bus.register_object(path, iface, method_callback, get_property_callback, None)
- 实测 Gio 会自动实现 org.freedesktop.DBus.Properties、Introspectable、Peer，无需手写 Get/GetAll。
- **get_property 回调签名是 (connection, sender, object_path, interface_name, property_name)**，Python 方法因此要 self + 5 个参数；少一个参数就是 TypeError。
- 动作：
  - 打开：优先读 state/url（token URL），否则 http://127.0.0.1:PORT/；调用 xdg-open（异步，1.5 秒去抖）；失败 notify-send。
  - 重启：定位 dsh web pid（state/pid 存活优先，否则 ss -H -ltnp 'sport = :PORT' 解析 pid=）→ SIGTERM 等待≤10s 再 SIGKILL → 等端口释放 → setsid 调用 launcher（继承 DSH_WEB_PORT/XDG_STATE_HOME 等环境；旧 launcher 仍持 flock，退出后新 launcher 自然拿到锁）→ 等端口重新监听且 url 文件变化（≤120s）；失败 notify-send。
  - 退出：停 dsh web 后托盘自身退出（图标消失）；不关浏览器。
- 生命周期：后台定时器每 1 秒探测端口，连续 3 次失败（且不在重启中）→ 清理 tray.pid 并退出。收到 SIGTERM/SIGINT 也清理退出。
- 单实例：fcntl.flock(state/tray.lock, LOCK_EX|LOCK_NB)，失败直接退出；pid 写 state/tray.pid。
- 日志：state/tray.log，带时间戳，超过约 512KB 轮转为 .old。
- 完整可运行实现可参考 ~/.local/bin/dsh-web-tray（约 660 行）；新机器按本节契约实现，关键 D-Bus 骨架见 references/dbus-menu-skeleton.md。

### launcher 与托盘的配合
- launcher 三条路径都要 ensure_tray：新启动成功后、复用存活实例时、端口被外部实例占用的兜底分支。
- ensure_tray：tray.pid 存活则跳过；否则 setsid 启动托盘；失败只记日志，不阻塞启动。
- 重启时旧 launcher 会在 dsh web 退出后清理 pid/url 并退出；新 launcher 因 flock 会等旧 launcher 退出后再启动，顺序天然正确。

## C. symbolic 图标（深色顶栏可见）

- 源：dsh-web-frontend/dist/favicon.svg（矢量鲸鱼，path fill="#000"）。
- 生成：把 width/height 改为 16，fill 改成 #ffffff，安装为
  ~/.local/share/icons/hicolor/scalable/apps/<icon>-symbolic.svg
- 顶栏 system-status-icon 会按 foreground 重着色名为 *-symbolic 的图标；白色填充同时保证万一不重着色也能看清。
- 刷新：gtk-update-icon-cache -f -t ~/.local/share/icons/hicolor
- 验证解析：python3 -c "import gi; gi.require_version('Gtk','3.0'); from gi.repository import Gtk; print(Gtk.IconTheme.get_default().lookup_icon('dsh-web-symbolic',24,0).get_filename())"
- 兜底：若截图仍不可见，改为运行时用 GdkPixbuf 生成白色 ARGB IconPixmap（16/22/24/32/48）并清空 IconName。

## D. 关键坑（按踩坑顺序）

| 坑 | 现象 / 处理 |
|---|---|
| 扩展双击不触发 | Introspection 里没有 Activate 方法 → 双击被当普通点击；确保方法已导出 |
| GetLayout 返回 NULL | children 用错类型；必须是 av（new_array(GLib.VariantType.new("v"), [new_variant(node),...])） |
| 属性读不到 | get_property 回调参数个数错（self + 5）；Gio 会打 TypeError 日志 |
| 顶栏图标黑/不可见 | 用 symbolic 白色 SVG；常规彩色图标在深色顶栏看不清 |
| 托盘继承 launcher 的 flock | 启动托盘必须 9>&-（及 dsh web 子进程），否则后续 launcher 点击阻塞在 flock |
| 端口占用时点击菜单无反应 | 打开/重启前先探测端口；打开失败给 notify-send |
| 权限 / file sandbox | 写 ~/.local 与系统路径需要 danger-full-access 文件策略；测试临时文件放工作区 ./tmp/ |
| gdbus 测 GetLayout 失败 | 负数参数 -1 被 gdbus 当选项；改用 Python Gio call_sync 测试 |
| 插件市场重启导致端口漂 | dshmarket 重启会重放当前进程 argv；固定 --port 后端口稳定，且重启后浏览器 cookie 仍可登录 |
| 托盘只在 launcher 管理时存在 | 终端裸跑 dsh web 无托盘；文档中说明该限制 |

## E. 验证清单（按序执行）

1. 静态检查：bash -n launcher；python3 -m py_compile tray。
2. D-Bus 契约：
       gdbus introspect --session --dest <bus名> --object-path /StatusNotifierItem   # 应有 Activate
       gdbus call --session --dest <bus名> --object-path /StatusNotifierItem --method org.freedesktop.DBus.Properties.GetAll org.kde.StatusNotifierItem
       # GetLayout 用 Python Gio 调用（避免 gdbus 的 -1 解析问题）
       gdbus call --session --dest org.kde.StatusNotifierWatcher --object-path /StatusNotifierWatcher --method org.freedesktop.DBus.Properties.Get org.kde.StatusNotifierWatcher RegisteredStatusNotifierItems
3. 视觉：org.freedesktop.portal.Screenshot 截图（默认写 ~/Pictures/Screenshot.png），裁剪顶栏放大后用 read_image 确认图标；再停掉托盘截一次对比，确认图标消失。
4. 动作：通过 DBusMenu Event(10,'clicked') 触发打开；用 stub 环境验证重启/退出/外部死亡：
   - 测试端口（如 13999）+ fake web（python http.server）+ fake launcher（写新 url 并起新 fake web）
   - 断言：重启后旧 pid 死、新 pid 监听、url 变化、托盘仍在；退出后端口关闭且 tray.pid 消失；外部杀 web 后托盘约 3-4s 自动退出。
5. 真实端到端（隔离，不打断当前实例）：XDG_STATE_HOME=<工作区 tmp> DSH_WEB_PORT=14999 启动真实 launcher，触发菜单重启/退出，并验证 --stop 连带停托盘。
6. 注意：真实实例上的「重启/退出」会断开当前页面（会话已持久化），不要在对话进行中贸然操作；或在最后一步再交给用户手动点击。

## F. 回滚 / 卸载

- 修改 launcher 前先备份（遵循本机临时文件规范，保存到会话工作区 tmp/）。
- 卸载：停托盘（TERM）→ 删 tray 脚本与 symbolic svg → 恢复 launcher 备份 → 删 .desktop 与其图标（如需）→ 清理 state/tray.*。
- 无系统级改动、无新装包；端口行为可随时回退（例如改回 --port 0 随机端口）。

## G. 参数化与适配

- 名称：dsh-web / DSH Web / 图标名 dsh-web 可替换为任意应用；文件与图标名保持一致。
- PORT：换成目标机器上 1024-32767 且空闲的端口（ss -tuln 检查）。
- 不同 DSH 安装：先用 command -v dsh 确认路径；桌面文件 Exec 必须用绝对路径；日志行格式若变化需同步改 URL 解析正则。
- 若要支持多实例：端口、state 目录、图标名都要一起参数化（本方案默认单实例固定端口）。

## H. 参考实现与已验证范围

- ~/.local/bin/dsh-web-launcher（启动/复用/停止 + 托盘生命周期）
- ~/.local/bin/dsh-web-tray（SNI + DBusMenu 托盘）
- ~/.local/share/applications/dsh-web.desktop
- ~/.local/share/icons/hicolor/128x128|256x256|512x512/apps/dsh-web.png 与 scalable/apps/dsh-web-symbolic.svg
- 备份：修改 launcher 前按本机临时文件规范在会话工作区 tmp/ 下保存副本
- 上述文件可直接作为模板复制；新机器上没有这些文件时，按本文 A/B/C 节从头实现即可（D-Bus 骨架与可复制片段见 references/dbus-menu-skeleton.md）。
