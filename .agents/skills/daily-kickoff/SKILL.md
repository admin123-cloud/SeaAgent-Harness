---
name: daily-kickoff
description: >-
  Use this skill when the user starts a study or coding session (e.g. "今天学什么", "每日开工",
  "继续推进 SreAgent", "开始学习"), to read the V6 learning OS progress and implementation ledger
  and produce a concise, actionable daily kickoff plan with links, contracts, and acceptance criteria.
---

# 每日开工引导（Daily Kickoff）

用于每次开始学习或推进项目时，自动对齐 V6 课表进度与仓库真实断点，省去手动翻找链接和上下文的时间。

## 执行步骤

1. **读取单一真相源**（并行读取，不要猜测进度）：
   - `F:\Projects\ai-learning-os\data\curriculum.json`
   - `F:\Projects\ai-learning-os\data\progress.json`
   - `F:\Projects\SreAgent\docs\task\implementation.md`（重点查看当前主线 SDD 章节）
2. **定位今日/当前断点**：
   - 根据当前日期和 `progress.json` 中尚未完成的最早任务，定位当前所属周次（`activeWeek`）、当天或当前断点对应的课程项、项目任务项、以及本周 Python 小目标。
   - 检查 `progress.json` 的 `interviewQueue` 中是否有未回答的随堂面试题。
3. **输出精炼开工清单**（严格控制在 1 屏内，直接可执行、低废话）：
   - **当前定位**：周次、阶段、距 `2027-02-04` 收官剩余天数、上一断点状态。
   - **今日课程任务**：具体内容、计划分钟、**直达学习链接**（附核实状态提示）、以及本节要求的产出（如 3 条笔记）。
   - **今日项目任务（SreAgent / 知识库 Agent / 协作层）**：
     - 先核对 `curriculum.json` 中该任务的 `devGuide`（若有）；若较简略，按当前周次补充清晰细节（W1–W2 讲细、W3 起逐步提升自主拆解要求）；
     - 明确**业务场景与上下游调用链路**（谁调谁、数据怎么流转），以及**不包含的内容**；
     - 给出涉及文件、核心接口契约、Python 易错语法点（对照 Java 的理解点）与仅含 `# TODO` 步骤的最小骨架（**不直接代写核心业务代码**）；
     - 明确可执行的本地验收命令与预期断言。
   - **待答面试题提醒**：若有未答题目，简短列出提醒顺手口答。
4. **同步状态提醒**：
   - 如用户确认开始某任务，可将 `progress.json` 中对应任务状态由 `0`（未开始）更新为 `1`（进行中），不要提前标为已完成。
