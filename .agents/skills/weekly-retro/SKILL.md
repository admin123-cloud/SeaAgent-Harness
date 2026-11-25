---
name: weekly-retro
description: >-
  Use this skill when the user wants to run the Sunday weekly wrap-up, review weekly progress,
  re-schedule unfinished tasks, or generate the next week's detailed daily plan (e.g. "周日收尾",
  "本周复盘", "生成 W2 详细课表", "重新排期"). Reads and updates AI Learning OS curriculum.json
  and progress.json.
---

# 周日收尾与下周排课（Weekly Retro & Planning）

完成每周 30 分钟收尾复盘，更新周进度并动态生成下一周的详细日课表（写入 `ai-learning-os` 直接展示）。

## 执行步骤

1. **读取本周全量状态**：
   - 读取 `F:\Projects\ai-learning-os\data\curriculum.json` 与 `progress.json`。
   - 对照 `F:\Projects\SreAgent\docs\task\implementation.md` 的最新任务状态，核对是否存在“代码已验收但看板未勾选”或“看板已勾但缺验证证据”的偏差。
2. **输出本周复盘摘要**：
   - **计划 vs 实际**：工作日计划分钟、实际投入分钟、任务完成率、考察得分与薄弱点、视野拓展阅读情况。
   - **未完成项归因**：区分“排期过满 / 技术卡点 / 方向调整 / 外部打断”，明确哪些顺延、哪些按 V6“砍掉清单”原则降级。
   - **偏差预警**：评估距离 `2027-02-04` 收官日与阶段里程碑（阶段 A W6 / 阶段 B W9 / 阶段 C W12）的风险。
3. **起草下一周详细日课表（先确认、再落盘）**：
   - 严格遵守时间约束：上午全职工作不排任务；周一至周五下午各约 3 小时（180 分钟），周二/周四晚各 1 小时（60 分钟），周六 120 分钟可选机动（含 60 分钟视野拓展），周日 30 分钟收尾。
   - 为每天的每条任务绑定明确产出和直达学习链接（取自 `curriculum.json` 的 `links`）。
   - **针对 `SreAgent` / 知识库 / 协作层等编码类任务，必须在任务对象中同步编写详尽的 `devGuide`（Markdown 字符串）**，帮助学员先看懂业务链路再写 Python（难度随周次渐进提升）：
     1. **业务场景与调用链路**：写清用户/模型请求从哪里进、经过哪些模块/函数、最终吐出什么（让学员理解这段代码在系统里的真实作用，而不是孤立背需求）；
     2. **涉及文件与改造清单**：明确“改哪个文件哪个类/函数、加什么字段/方法、本次**不改**什么”；
     3. **Python 实战语法与骨架提示**：W1–W2 对照 Java/直觉讲解当前用到的 Python 特性，并给出只含类/函数签名与 `# TODO` 步骤的接口骨架（**绝不代写完整业务实现**）；W3–W6 逐步收敛骨架、侧重接口契约与边界用例；W7–W13 逐步过渡为由学员自主拆解模块与手写边界；
     4. **分步验证命令**：给出可直接在本机运行的测试/检查命令与预期结果。
   - 列出草案请用户确认。
4. **用户确认后落盘同步**：
   - 将本周状态与完成日期写入 `F:\Projects\ai-learning-os\data\progress.json`（更新 `weekStatus` 和 `activeWeek`）。
   - 将确认后的下周详细日课表写入 `F:\Projects\ai-learning-os\data\curriculum.json` 的 `weeklyPlans[nextWeek]`，并更新当周 `todo`。
   - 通知用户刷新 `http://127.0.0.1:4173` 即可看到新一周课表与待办。
