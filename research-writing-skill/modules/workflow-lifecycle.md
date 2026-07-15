# 论文全流程编排模块（Lifecycle Orchestration）

本模块用于把“选题到投稿”拆成可执行阶段，并让 AI 在每阶段产出可追踪文档。

适用场景：
- 用户要做整篇论文长期协作
- 用户希望知道下一阶段该做什么
- 用户准备投稿，需要补齐材料与合规项

## 一、阶段总览（Stage Gates）

| 阶段 | 目标 | AI可执行动作 | 必交付物 |
|---|---|---|---|
| S0 启动与边界 | 明确研究问题与约束 | 讨论题目、研究问题、截止时间、格式规则 | `plan/project-overview.md` |
| S1 方案与注册 | 固化研究计划 | 生成研究方案草稿、可选预注册清单 | `plan/stage-gates.md`（S1） |
| S2 文献检索 | 构建可追溯证据池 | 生成检索式、去重策略、纳排标准 | `plan/notes.md`（检索日志） |
| S3 大纲与方法 | 锁定结构和方法路线 | 对齐章节结构、方法与数据要求 | `plan/outline.md` |
| S4 写作与图表 | 形成完整初稿 | 章节写作、图表脚本、结果解释 | `paper/*` 与 `figures/*` |
| S5 质量与合规 | 降低投稿风险 | 逐项做报告规范检查、引用核验、AI使用披露检查 | `plan/progress.md`（质量记录） |
| S6 投稿包准备 | 完成可提交材料 | 生成 cover letter、贡献声明、数据共享声明草稿 | `plan/submission-checklist.md`（可选） |
| S7 返修与归档 | 版本迭代与复现归档 | 生成回复审稿意见草稿、变更日志、复现清单 | `plan/notes.md`（返修记录） |

## 二、按阶段补充能力（你这个 skill 现在可新增的重点）

### S0 启动与边界

AI除了建 plan，还应做：
1. 输出“任务边界声明”：本轮只改哪些文件，不改哪些文件。
2. 输出“验收标准”：每阶段什么算完成。
3. 记录用户写作偏好（无加粗、段间空一行、正文少列表）。

### S1 方案与注册

AI可做：
1. 根据研究类型推荐是否进行预注册（preregistration）。
2. 给出 OSF 注册模板选择建议与字段草稿。
3. 对临床研究提醒注册与数据共享要求。

### S2 文献检索

AI可做：
1. 先做 broad search，再做 focused search（主题词收敛）。
2. 维护检索日志：数据库、检索式、日期、结果数。
3. DOI 元数据回填与去重（题名+作者+年份+DOI）。
4. 对系统综述任务，自动维护 PRISMA 所需流程统计项。

### S3 大纲与方法

AI可做：
1. 先按研究类型路由报告规范，再反推章节骨架。
2. 在 `outline.md` 里标记“必含方法信息”和“可选扩展信息”。
3. 给出图表规划表（图号、变量、统计方法、文件路径）。

### S4 写作与图表

AI可做：
1. 保持你定义的排版约束（无加粗、段间空一行）。
2. 对每章生成“证据—论点映射”，避免空泛段落。
3. 画图前自动检查环境；画图后写入图注草稿与复现实验参数。

### S5 质量与合规

AI可做：
1. 研究类型到报告规范清单映射（逐项核对缺失项）。
2. 引用一致性检查（文内引用是否在参考文献出现）。
3. AI 使用披露草稿（如目标期刊要求）。
4. 相似性风险检查提示（重点是人工判读，不只看分数）。

### S6 投稿包准备

AI可做：
1. 生成投稿材料骨架：cover letter、作者贡献、利益冲突、伦理声明、数据共享声明。
2. 生成“期刊适配清单”：字数、图表数、参考文献样式、附件要求。
3. 生成提交前最终检查单（文件命名、盲审信息清理、元数据一致性）。

### S7 返修与归档

AI可做：
1. 生成“审稿意见-响应矩阵”（comment-by-comment）。
2. 对每条意见标注：接受/部分接受/不接受 + 理由 + 修改位置。
3. 输出变更日志（版本号、日期、改动范围、风险点）。

## 三、研究类型与报告规范路由

当用户说明研究类型时，优先映射到对应规范：

1. 随机对照试验（RCT）
- 优先：CONSORT 2025（结果报告）
- 协同：SPIRIT 2025（方案/protocol）

2. 观察性研究（队列/病例对照/横断面）
- 优先：STROBE checklist

3. 系统综述/Meta
- 优先：PRISMA 2020（27-item + flow diagram）

4. 医学投稿综合约束
- 参考：ICMJE Recommendations（当前站点显示更新为 2026-01）

## 四、默认产物策略（建议启用）

每个阶段至少保留一个“可审计”文件：

1. S0/S1：`project-overview.md` + `stage-gates.md`
2. S2/S3：`notes.md` + `outline.md`
3. S4：章节正文 + 图表脚本
4. S5/S6：`progress.md` + 投稿检查清单
5. S7：`notes.md` 中的返修记录

## 五、执行协议（AI必须遵守）

1. 开始任务前先判断当前处于哪个阶段。
2. 若阶段不明，先提出 3 个确认问题再执行。
3. 每完成一轮操作，更新 `stage-gates.md` 和 `progress.md`。
4. 若用户跳过阶段，AI要提示风险并记录在 `notes.md`。

## 六、外部依据（官方来源）

1. EQUATOR reporting guidelines 检索库
- https://www.equator-network.org/reporting-guidelines/

2. PRISMA 2020（27-item + flow diagram）
- https://www.prisma-statement.org/prisma-2020-statement
- https://www.prisma-statement.org/prisma-2020-checklist

3. SPIRIT/CONSORT 2025（protocol 与 RCT 报告）
- https://www.consort-spirit.org/

4. STROBE 观察性研究清单
- https://www.strobe-statement.org/checklists/

5. ICMJE Recommendations（站点显示更新：2026-01）
- https://www.icmje.org/recommendations
- https://www.icmje.org/recommendations/browse/manuscript-preparation/sending-the-submission.html
- https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html

6. 文献与作者元数据生态
- Crossref REST API: https://www.crossref.org/documentation/retrieve-metadata/rest-api/
- OpenAlex Works Search: https://docs.openalex.org/api-entities/works/search-works
- ORCID Public API: https://info.orcid.org/what-is-orcid/services/public-api/

7. 引用与软件/数据可引用性
- Zotero Word Processor Integration: https://www.zotero.org/support/word_processor_integration
- GitHub CITATION.cff: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files
- Zenodo CITATION.cff: https://help.zenodo.org/docs/github/describe-software/citation-file/

8. 数据与复现
- FAIR principles (Sci Data 2016): https://www.nature.com/articles/sdata201618
- DataCite Schema 4.6 (Released 2024-12-05): https://schema.datacite.org/
- CRediT taxonomy (NISO): https://credit.niso.org/
