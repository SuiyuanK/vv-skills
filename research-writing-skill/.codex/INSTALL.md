# Installing Research Writing Assistant for Codex

通过 Codex 原生技能发现机制启用科研写作助手。只需克隆并创建符号链接。

## 前置要求

- Git

## 安装步骤

1. **克隆仓库：**
   ```bash
   git clone https://github.com/Norman-bury/research-writing-skill.git ~/.codex/research-writing-skill
   ```

2. **创建技能符号链接：**
   ```bash
   mkdir -p ~/.agents/skills
   ln -s ~/.codex/research-writing-skill/skills ~/.agents/skills/research-writing
   ```

   **Windows (PowerShell)：**
   ```powershell
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.agents\skills"
   cmd /c mklink /J "$env:USERPROFILE\.agents\skills\research-writing" "$env:USERPROFILE\.codex\research-writing-skill\skills"
   ```

3. **重启 Codex**（退出并重新启动 CLI）以发现技能。

## 验证安装

```bash
ls -la ~/.agents/skills/research-writing
```

你应该看到一个指向 research-writing-skill/skills 目录的符号链接（Windows 上是目录连接）。

## 更新

```bash
cd ~/.codex/research-writing-skill && git pull
```

技能通过符号链接即时更新。

## 卸载

```bash
rm ~/.agents/skills/research-writing
```

可选：删除克隆的仓库：`rm -rf ~/.codex/research-writing-skill`

## 使用

安装后，在对话中提到论文写作相关任务即可触发技能：

- "帮我写毕业论文"
- "我要写一篇 SCI 论文"
- "帮我做文献综述"
- "画一个数据图表"

技能会自动引导你完成头脑风暴、章节规划和写作流程。
