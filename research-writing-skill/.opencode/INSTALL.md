# Installing Research Writing Assistant for OpenCode

## 前置要求

- [OpenCode.ai](https://opencode.ai) 已安装

## 安装步骤

在你的 `opencode.json`（全局或项目级别）的 `plugin` 数组中添加：

```json
{
  "plugin": ["research-writing-assistant@git+https://github.com/Norman-bury/research-writing-skill.git"]
}
```

重启 OpenCode。插件会自动安装并注册所有技能。

验证安装：询问 "告诉我你的科研写作能力"

## 从旧版符号链接安装迁移

如果之前使用 `git clone` 和符号链接安装，请移除旧配置：

```bash
# 移除旧符号链接
rm -f ~/.config/opencode/plugins/research-writing.js
rm -rf ~/.config/opencode/skills/research-writing

# 可选：删除克隆的仓库
rm -rf ~/.config/opencode/research-writing-skill
```

然后按上述安装步骤操作。

## 使用

使用 OpenCode 原生 `skill` 工具：

```
use skill tool to list skills
use skill tool to load research-writing/brainstorming-research
```

## 更新

重启 OpenCode 时自动更新。

锁定特定版本：

```json
{
  "plugin": ["research-writing-assistant@git+https://github.com/Norman-bury/research-writing-skill.git#v3.1.0"]
}
```

## 故障排除

### 插件未加载

1. 检查日志：`opencode run --print-logs "hello" 2>&1 | grep -i research`
2. 验证 `opencode.json` 中的插件配置
3. 确保运行的是最新版本的 OpenCode

### 技能未找到

1. 使用 `skill` 工具列出已发现的技能
2. 检查插件是否正常加载（见上文）

## 获取帮助

- 报告问题：https://github.com/Norman-bury/research-writing-skill/issues
- 完整文档：https://github.com/Norman-bury/research-writing-skill
