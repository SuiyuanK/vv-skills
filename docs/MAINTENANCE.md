# vv-skills 维护流程

## 唯一规范目录

Linux 上 CC Switch 的规范 skill 目录与 `vv-skills` 本地 Git 工作副本是同一目录：

```text
/home/vv/.cc-switch/skills
```

其他系统必须读取 CC Switch 的实际配置，不照搬此路径。Claude、Codex、Gemini、opencode 等 Agent 的 skill 目录和软连接由 CC Switch 管理；不要直接新增、修改、删除或重建这些链接。

## 清单与 README

`catalog.json` 是目录元数据源。根 README 中的分类索引由脚本生成：

```bash
python scripts/catalog.py --render
python scripts/catalog.py --check
```

新增、更新、归档、合并、删除或替换 skill 时必须同步：

1. skill 目录与入口 `SKILL.md`；
2. `catalog.json` 中的用途、平台、依赖、状态和来源；
3. 根 README 的生成索引；
4. 第三方变更对应的 `docs/THIRD_PARTY.md`。

个人 skill 的详细工作流只维护在自身 `SKILL.md` 和必要的 `references/` 中，不在根 README 重复长篇说明。

## 修改前检查

```bash
git branch --show-current
git status --short --branch
git fetch origin main
git rev-list --left-right --count main...origin/main
```

- 要求分支为 `main`。
- 有未提交改动、分叉或冲突时停止，不强制拉取或覆盖。
- 本地仅落后且工作区干净时使用 `git pull --ff-only`。

## 个人 skill

在 CC Switch 规范目录中创建或修改。入口描述应准确区分触发场景；复杂的环境或模式拆到按需读取的 references。验证至少包括：

```bash
python /path/to/skill-creator/scripts/quick_validate.py ./skill-name
python scripts/catalog.py --check
git diff --check
```

新增或改名后先通过 CC Switch 启用新入口、停用旧入口，核验各 Agent 的真实软连接，再移除旧目录。不得用手工链接绕过 CC Switch。

## 第三方 skill

1. 从 `catalog.json` 和 `docs/THIRD_PARTY.md` 读取上游、分支、基线和本地调整。
2. 将上游内容获取到本次调用工作区的 `./tmp/`；不写系统 `/tmp`、`/var/tmp` 或 Agent skill 目录。
3. 比较基线与目标提交，检查许可证、敏感信息、文件增删、依赖和本地修复；不得直接覆盖。
4. 只同步该 skill 约定的可安装文件范围。
5. 运行结构验证、脚本测试和适用的核心功能检查。
6. 更新 `catalog.json` 的完整提交哈希、可选版本及 `docs/THIRD_PARTY.md`。

## 归档、合并与删除

- 未经用户明确要求，不归档、删除或整体替换 skill。
- “当前未启用”不是归档依据；先判断是否过时、被替代或失去适用环境。
- 归档项放在 `archive/<name>/`，并把目录状态改为 `archived`，使 CC Switch 不再把它作为顶层 active skill 发现。
- 合并时在新目录的 catalog 条目中记录 `supersedes`；CC Switch 完成安全迁移后才能删除旧入口。
- 删除前检查个人修改、未提交内容、第三方来源与回滚路径。Git 历史不替代当前数据备份。

## 本地依赖与忽略项

`.venv/`、`__pycache__/` 等本地运行环境不提交。新增依赖时记录用途、影响和配置方式；未经确认不安装系统软件、不修改系统配置。临时下载、缓存、日志和中间产物使用调用工作区的 `./tmp/`。

## 提交与发布

默认不创建分支或 Pull Request，验证后直接提交并推送 `main`：

```bash
git diff --check
git status --short
git add -- <本次相关文件>
git diff --cached --check
git commit -m "refactor: organize skill catalog"
git fetch origin main
git merge-base --is-ancestor origin/main main
git push origin main
```

只暂存本次文件，不强制推送。推送后复查本地状态、远程提交、README 生成索引、第三方基线和 CC Switch 软连接。
