---
name: verification
description: Use when about to claim work is complete, a chapter is finished, or references are verified - requires running verification commands and confirming output before making any success claims
allowed-tools: Read, Bash, Grep
---

# 验证机制

## 核心原则

**声称完成而没有验证，是不诚实的表现。**

```
没有验证证据，就不能声称完成
```

## 验证门控

```
在声称任何状态或表达满意之前：

1. 确认：什么命令/操作能证明这个声称？
2. 执行：运行完整的验证操作
3. 读取：完整输出，检查结果
4. 验证：输出是否确认声称？
   - 如果否：说明实际状态和证据
   - 如果是：说明声称和证据
5. 然后才能：做出声称

跳过任何步骤 = 撒谎，不是验证
```

## 常见验证场景

| 声称 | 需要的验证 | 不充分 |
|------|----------|--------|
| 章节完成 | 字数统计、结构检查、文件存在 | "应该写完了" |
| 引用真实 | DOI 可访问、CrossRef API 确认 | "看起来像真的" |
| 论点有支撑 | evidence map 中有段落级证据 | "这段写得像论文" |
| 格式正确 | 运行格式检查脚本 | 目测检查 |
| 无AI痕迹 | 运行风格检查脚本 | "读起来还行" |
| 文献搜索完成 | 结果数量、DOI 列表、JSON 文件存在 | "搜过了" |
| skill 改造完成 | 运行 `scripts/check_skill_integrity.ps1` | "文件都写了" |
| 初稿达到质量门 | 运行 `scripts/research_quality_gate.ps1` | 只运行 style_check |

## Red Flags - 停止

出现以下情况时，必须先验证：

- 使用"应该"、"可能"、"看起来"
- 在验证前表达满意（"好了！"、"完成！"）
- 准备提交/推送/合并而不验证
- 相信代理的成功报告
- 依赖部分验证
- 想着"就这一次"
- 疲劳想结束工作
- **任何暗示成功但没有运行验证的措辞**

## 借口与事实

| 借口 | 事实 |
|------|------|
| "应该行了" | 运行验证命令 |
| "我很确信" | 确信 ≠ 证据 |
| "就这一次" | 没有例外 |
| "格式检查过了" | 格式检查 ≠ 内容正确 |
| "代理说成功了" | 独立验证 |
| "我累了" | 疲劳不是借口 |
| "部分检查够了" | 部分证明不了什么 |

## 关键验证模式

### 章节完成验证

```
✅ [运行字数统计] [看到：3000字] "章节字数达标"
✅ [检查文件存在] [看到：chapters/01-introduction.md 存在] "章节文件已创建"
✅ [运行格式检查] [看到：0 errors] "格式正确"
❌ "应该写完了" / "看起来完整"
```

### 引用验证

```
✅ [调用 CrossRef API] [看到：DOI 存在，信息匹配] "引用已验证"
✅ [搜索原始来源] [找到：作者、期刊、年份一致] "引用真实"
❌ "引用看起来正确" / "应该是真的"
```

### 论点支撑验证

```
✅ [检查 evidence-map] [看到：每个 gap claim 对应 2 条来源] "研究空白有文献支撑"
✅ [检查 citation slot] [看到：段落 P2 使用 FL-05 + FL-07] "引用位置明确"
❌ "相关工作看起来完整" / "这段有学术感"
```

### Skill 完整性验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/check_skill_integrity.ps1
```

用于确认新增技能、路由、验证脚本和关键门控仍然存在。

### 稿件质量门验证

```powershell
powershell -ExecutionPolicy Bypass -File scripts/research_quality_gate.ps1 -ProjectPath <paper-project>
```

用于检查引用覆盖、正文污染、列表化、占位策略、figure data manifest 和 evidence map。投稿前加 `-Submission`，禁止未回填占位。

### 文献搜索验证

```
✅ [检查 JSON 文件] [看到：20 条结果，每条有 DOI] "搜索完成"
✅ [验证 BibTeX 输出] [看到：可解析，无错误] "BibTeX 有效"
❌ "搜过了" / "应该有结果"
```

## 验证检查清单

每项工作完成前必须验证：

- [ ] 运行了验证命令
- [ ] 读取了完整输出
- [ ] 确认结果支持声称
- [ ] 没有依赖"应该"或"可能"
- [ ] 证据在当前消息中呈现

## 为什么这很重要

从实际失败案例中：
- 引用伪造导致论文撤稿
- 章节字数不达标导致返工
- 格式错误导致投稿失败
- AI 痕迹明显导致评审质疑

## 底线

**验证没有捷径。**

运行命令。读取输出。然后才能声称结果。

这是不可协商的。
