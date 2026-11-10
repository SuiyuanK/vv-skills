# vv-skills 维护流程

## 适用范围与规则

本流程仅适用于创建、修改、引入、更新、归档、删除或替换仓库内容。普通读取和使用 skill 不触发同步、维护验证、提交或推送。

本仓库管理个人 skill 和用户选定纳入的第三方 skill；可以限定 Agent、平台或产品版本，不要求通用。Agent 随软件提供的内置或私有 skill 由官方机制维护，不自动纳入、复制或同步；用户明确要求纳入时按实际来源分类，不仅凭目录判断归属。

优先级为：当前 Agent 的系统/开发者规则与安全底线 > 用户当前明确指令 > 用户维护规范 > skill 自身指令。仓库文档补充具体流程；存在实质冲突时报告差异，不仅凭文件时间判断优先级。无法确定时暂停受影响的操作，其余独立工作可以继续。

## 唯一规范目录与部署

规范目录以本机 CC Switch 实际配置为准，同时必须是 vv-skills 的 Git 工作副本。CachyOS/Linux 当前为 `~/.cc-switch/skills`；Windows 从 CC Switch 设置、技能页或数据目录确认，不照搬 Linux 路径。配置、目录或仓库身份不一致时先询问用户。

Agent 的 skill 目录和部署链接仅作只读核验，不新增、修改、删除或重建。CC Switch 管理的部署、启用、停用均通过 CC Switch 或请用户操作，不手工复制或建链。内置 skill 的官方维护机制不属于本仓库维护流程。

## 修改前检查与协作

同一时间只由一个 Agent 写入。已知其他 Agent 正在维护时暂停写入；工作区干净不证明独占访问。发现其他 Agent 的改动或来源不明的改动时停止说明，不代为提交、还原、清理或 stash。

先读本文件、`catalog.json` 和 `docs/THIRD_PARTY.md`，再检查：

```bash
git branch --show-current
git status --short --branch
git fetch origin main
git rev-list --left-right --count main...origin/main
```

要求分支为 `main`。存在无关的未提交改动、分叉或冲突时停止，不强拉、不覆盖；本地仅落后且工作区干净时使用 `git pull --ff-only`。工具不足时可用通用 shell 或文件操作，不绕过权限或审批。

## 清单、命名与 README

`catalog.json` 是目录元数据源；根 README 分类索引和第三方基线表由脚本生成，不手工修改生成区：

```bash
python3 scripts/catalog.py --render
python3 scripts/catalog.py --check
python3 scripts/validate_skills.py
```

新增、修改、归档、合并、删除或替换时，同步受影响的入口、catalog 用途/平台/依赖/状态及 README；第三方来源或版本变化时更新基线和同步边界。人工章节仅改本次相关内容，详细工作流保留在 skill 自身，不在 README 重复。

新 skill 的目录名、frontmatter `name` 与 catalog `name` 必须一致，使用 kebab-case。历史例外用 catalog 的 `naming_exception` 非空说明登记；不为统一而强行改名。新增或改名涉及部署时，通过 CC Switch 安全迁移；未经用户明确要求不删除旧入口。

`scripts/catalog.py` 的 platforms 白名单与 category 列表属代码内配置；新增平台或分类时同步修改脚本并跑校验，不得绕过。

## 个人 skill

在规范目录中创建、修改和验证。`description` 写清用途与触发场景，如实标注平台、Agent、产品版本及限制。正文保留必要流程，长资料拆到 `references/`。脚本按声明范围编写，不含密钥、token、cookie 或隐私数据，不依赖未声明或不可用工具。

## 第三方 skill

1. 引入前核验真实上游、跟踪分支、目标提交、许可证、维护状态、体积、文件构成、敏感信息及可执行风险，并确认用户要纳入管理。保留 LICENSE；无许可证时说明风险并询问。
2. `catalog.json.upstream` 是唯一机器可读来源：`repository` 使用 HTTPS，记录 `branch`，`baseline` 为 40 位小写 commit，`license` 记录 SPDX 名称或「上游未提供 LICENSE」及风险说明，`version` 可选。
3. `docs/THIRD_PARTY.md` 记录同步边界、本地修复、依赖和许可证；README 来源表由 `catalog.json` 生成，不手工编辑，不新增独立来源记录。
4. 从已记录基线逐项比较目标提交的许可证、文件增删、依赖、敏感信息和本地修复，不直接覆盖。下载与解压只放本次会话开始时工作区根目录的 `./tmp/`。
5. 只同步约定的可安装文件，不引入上游 `.git`、仓库级 README/AGENTS/CI，除非确有必要且已说明。保留现有约定中的必要文件。
6. 新增或调整第三方条目时检查 catalog 校验及设计依据；需要调整时同步验证，不删除或跳过校验规避约束。数量从条目计算，不固定为某个数量。
7. 验证后更新受影响的目录、基线、同步边界及 README。

## 双平台、依赖与临时文件

两平台仅通过 Git 同步。文本统一 UTF-8（无 BOM）与 LF，根 `.gitattributes` 约束文本换行，二进制文件不转换；`*.cmd`/`*.bat` 因 cmd.exe 兼容性单独保持 CRLF，不按纯文本处理。不进行与任务无关的全库换行重写；提交前排除仅换行或编码造成的整文件差异。

避免大小写不同名、Windows 非法字符、保留名、结尾点或空格及超长路径。skill 使用 HOME、USERPROFILE、仓库相对路径或说明性占位，不写死用户名、盘符或本机绝对路径。按声明范围验证；未验证平台不声称支持。

Linux 示例使用 bash 和 `python3`；Windows 使用 PowerShell 及 `py -3` 或 `python` 等价执行，不默认 bash 可用。仓库 GitHub Actions 在 Linux 与 Windows 上执行 `catalog.py --check`、`validate_skills.py` 和索引换行检查；CI 结果不替代本地验证。

新增或改变 Python/Node 依赖、系统软件、命令、环境变量、权限、网络/API 服务或模型配置时，先说明用途、影响和配置方式。未经授权不安装软件、不修改系统或 Agent 配置；已有明确授权不重复询问。缺失依赖时提供平台适用的方法，继续不受影响的工作，不隐瞒缺失项或跳过必要验证。

测试产物、下载、缓存、日志和中间文件仅放本次会话开始时工作区根目录的 `./tmp/`；不覆盖或删除其中已有内容。工具支持时显式设置临时目录；无法控制临时输出位置时停止该操作并说明。`.venv/`、`__pycache__/` 等运行环境不提交。

## 验证门槛

提交前必须通过：

```bash
python3 scripts/catalog.py --check
python3 scripts/validate_skills.py
git diff --check
```

同时确认：

- frontmatter 可解析，name/目录/catalog 一致或符合已登记例外，引用的脚本与资料存在。`scripts/validate_skills.py` 负责结构与 name/description 校验；安装 PyYAML 时做完整 YAML 解析，未安装时降级为最小校验并明确提示，缺失依赖按依赖流程处理。
- 脚本通过语法、`--help` 或适用的只读路径检查；破坏性或不可逆步骤仅静态检查或 dry-run，不在真机演练。
- 多平台或多 Agent 改动至少静态核验编码、换行、路径及涉及的 bash/PowerShell 语法；有条件时分别实测，并如实记录已验证范围和未验证项。
- 必要验证无法完成时报告阻塞原因，不声称通过。

## 归档、合并与删除

未经用户明确要求不归档、删除或整体替换；未启用不是归档理由。归档移入 `archive/<name>/` 并设 `status: archived`；合并用新条目的 `supersedes` 记录被替代项。删除前核查个人修改、未提交内容、第三方来源和回滚路径；发现风险或冲突时先说明并等待确认。Git 历史不替代当前数据备份。

## 提交、推送与复查

验证通过后默认直接提交并推送 `main`，不建分支或 PR，除非用户明确要求。只暂存本次相关文件，不 force push：

```bash
git diff --check
git status --short
git add -- <本次相关文件>
git diff --cached --check
git commit -m "<说明本次变更>"
git fetch origin main
git merge-base --is-ancestor origin/main main
git push origin main
```

推送前重新核验远端与工作区；远端新增提交时先检查差异，在没有冲突或无关改动的前提下快进，或 rebase 本次未推送提交，再运行受影响的验证。出现分叉、冲突或来源不明的改动时停止说明，不擅自合并或覆盖。

推送后核验远端提交、本机状态、README 索引、第三方基线和可读取的本机 CC Switch 部署。另一平台或不可访问的部署标为未验证，不声称已同步或部署完成。推送失败时报告本地和远端状态；事后错误用新 commit 修正或 revert，不强推。部署异常通过 CC Switch 处理或请用户操作，不手工建链或搬运。
