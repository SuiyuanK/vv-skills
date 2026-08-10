# QQ 音乐启动闪退 根因与判别

## 适用与排除

| 场景 | 归属 | 处理 |
|---|---|---|
| ELF 报错 `cannot open shared object file` | 缺动态库 | 走 `apt` 安装依赖，不属于本 skill |
| `The display compositor is frequently crashing` | GPU/图形栈 | 本 skill：`--disable-gpu-sandbox` |
| `UnhandledPromiseRejectionWarning` / `login refresh fail` | 噪音（旧 Electron 常见） | 忽略，非闪退主因 |
| 终端按 Ctrl+C 后进程退出 | 正常关闭 | 非闪退 |

## 已知可靠参数

在 x86_64 Ubuntu 26.04（kernel major 7）上，对官方 `/opt/qqmusic`
客户端：

- `qqmusic` → 闪退（`display compositor is frequently crashing`）；
- `--disable-gpu --disable-gpu-compositing` → 可能仍闪退；
- `--disable-gpu --disable-gpu-compositing --ozone-platform=x11` → 可能仍闪退；
- `LIBGL_ALWAYS_SOFTWARE=1 --use-gl=swiftshader --disable-gpu-sandbox` → 需实测；
- `--disable-gpu-sandbox` → 已验证有效。

## 永久化原则

只改个人 `.desktop`，不写系统目录；包更新后修复仍保留。

```text
原始：Exec=/opt/qqmusic/qqmusic %U
修改：Exec=/opt/qqmusic/qqmusic --disable-gpu-sandbox %U
```

先 `grep '^Exec='` 确认实际命令再 `sed` 替换，避免整段盲目改写。
