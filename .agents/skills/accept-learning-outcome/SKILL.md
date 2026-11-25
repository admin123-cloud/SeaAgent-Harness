---
name: accept-learning-outcome
description: >-
  Use this skill when the user finishes a study or coding task in ai-learning-os and submits it for
  outcome acceptance (e.g. "验收当前学习任务", "学习结束开始验收", "接管验收 [w1-01]", "复验补学项").
  Reads progress.json, verifies code/notes against 35K/month China AI Agent Engineer technical
  interview standards, asks 2-3 probing questions, and writes back pass/remediation verdicts to
  ai-learning-os progress.json.
---

# 学习成果接管验收（Accept Learning Outcome · 35K 标准）

当用户在 `ai-learning-os`「当下学习工作台」点击「学习结束 · 提交成果验收」后，由本 Skill 接管验收，判断是否达到 **国内 35K/月 AI Agent 工程师技术面标准**，决定放行进入下一节还是打回补学。

## 35K 技术面验收标尺

- **不接受“背定义/看完了视频”**：必须能用工程视角讲清 **为什么这样设计、边界和失败模式是什么、生产环境怎么兜底与量化**。
- **代码类任务（SreAgent / Lab）**：必须先在本机跑通实际验证命令（导入、依赖方向、离线断言、脱敏检查），再追问设计取舍。
- **概念/阅读类任务**：必须审阅用户写在 `progress.json` 的笔记，再出 **2–3 道 35K 级追问**（至少包含 1 道场景排障或架构取舍题）。

## 执行步骤

### 第一阶段：接管与审阅（先查证 + 追问，不直接放行）
1. **读取真相源**：
   - 读取 `F:\Projects\ai-learning-os\data\curriculum.json`（定位该 `taskId` 的目标、`interview35k`、`checkCriteria`）
   - 读取 `F:\Projects\ai-learning-os\data\progress.json`（定位 `reviews[taskId]`、`notes[taskId]`、`tasks[taskId]`）
   - 读取 `F:\Projects\ai-learning-os\data\qa.json`（拉取本学习块 `taskId` 的全部实时提问与追问记录，定位未解答问题与高频困惑点）
   - 若用户未指定 `taskId`，自动查找 `reviews` 中 `state == "pending_review"` 的任务（或 `focusTaskId`）。
2. **代码/产物硬校验（如任务含代码或实验）**：
   - 在 `F:\Projects\SreAgent` 检查 `git diff` 并运行对应的本地验证脚本、包依赖方向检查与脱敏扫描。
3. **初步反馈与 35K 追问（支持网页端交互式验收会话）**：
   - 先优先解答 `data/qa.json` 中本块仍为 `pending` 的普通答疑（`kind != "acceptance"`）；
   - 点评已提交的笔记/代码亮点与明显缺漏；
   - 结合本块答疑中暴露的薄弱点，提出 **2–3 道 35K 面试官视角追问**（若为“补学复验”，仅针对上次 `remediation` 清单追问），等待用户作答。
   - **若通过 `qa_watcher.py` 接收到 `kind == "acceptance"` 的 `acc-...` 验收线程**：先调用 `python F:\Projects\ai-learning-os\qa_watcher.py reply --thread-id <acc-id> --file <reply.md>` 将初评与 2–3 道追问直接写回网页工作台（状态自动变为 `answered` 等待学员在网页内作答），随后继续后台 `watch` 等待学员作答回传。

### 第二阶段：裁定、学习块结案总结与回写（用户答完追问后执行）
4. **给出明确 3 档裁定 + 学习块结案总结**：
   - `passed`（**通过 · 达到 35K 标准**，一般 ≥ 8/10）：概念准确、工程边界清晰、代码/产物验证通过。
   - `needs_remediation`（**需补学部分内容**，6–7.5/10）：主干已懂但存在 1–2 个面试必踩坑或关键边界盲区，必须列出具体、小颗粒的 `remediation` 补学项（说明补什么、看哪段资料或写什么小验证，控制在 20–45 分钟内）。
   - `failed`（**未达标需重做**，< 6/10）：核心概念混淆或代码验收未通过，明确返工点。
   - 无论通过与否，输出一段简洁可复用的**「学习块结案总结」**（包含：① 本块已拿下成果 ② 欠缺/易错盲区 ③ 来自 `data/qa.json` 的核心困惑复盘）。
5. **原子写回 `F:\Projects\ai-learning-os\data\progress.json` 与 `data\qa.json`**：
   - **若存在 `acc-...` 交互式验收线程**：优先使用 `python F:\Projects\ai-learning-os\qa_watcher.py verdict --thread-id <acc-id> --state <passed|needs_remediation|failed> --score <分> --summary "<一句话总评>" --strengths "<亮点1|亮点2>" --gaps "<薄弱1>" --remediation "<补学1>" --file <feedback.md>` 一次性原子回写 `data/qa.json` 与 `data/progress.json`（网页会在 4 秒内自动同步结果）。
   - 更新 `reviews[taskId]`：
     - `state`: `"passed"` | `"needs_remediation"` | `"failed"`
     - `reviewedAt`: 当前 `+08:00` ISO 时间
     - `score`: 0–10 分
     - `meets35k`: `true` | `false`
     - `summary`: 一句话总评
     - `strengths`: 已掌握要点数组
     - `gaps`: 薄弱/遗漏点数组
     - `remediation`: 补学清单数组（通过时为空 `[]`）
   - 若 `state == "passed"`：
     - 将 `tasks[taskId].status` 更新为 `2`（已完成）；
     - 自动把 `focusTaskId` 推进到本周下一条未完成任务；
     - 将 `data/qa.json` 中本块已掌握的 `answered` 线程按需标记为 `resolved`（仍需周五复盘的保留为 `review_later`）；
     - 如涉及 `SreAgent` 正式任务，同步更新 `F:\Projects\SreAgent\docs\task\implementation.md` 的验证记录；
     - 如有高价值新考点，同步沉淀到 `docs/INTERVIEW_GUIDE.md` 或 `H:\Agent-Memory-System`。
   - 若 `state == "needs_remediation"` 或 `"failed"`：
     - 保持 `tasks[taskId].status` 为 `1`（进行中），保持 `focusTaskId` 锁定当前任务。
   - 刷新 `updatedAt` 和 `updatedBy = "antigravity-reviewer"`，提醒用户在页面点击「刷新本地同步」查看验收报告与补学清单。
6. **学习块切换与上下文压缩提醒**：
   - 当本学习块验收结案且全部成果/欠缺已落盘到 `progress.json`、`qa.json` 后，明确提示用户：**可在当前专职学习/答疑会话执行 `/compact` 压缩本块细节对话**，保留精炼结论，清爽进入下一个学习块。
