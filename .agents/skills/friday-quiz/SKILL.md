---
name: friday-quiz
description: >-
  Use this skill when the user wants to take a scheduled Friday unit quiz, retest, or comprehensive
  mock interview (e.g. "周五考察", "开始 U1a 考察", "出考察题", "模拟面试"). Generates 5 rubric-based
  questions (0-2 points each, pass >= 8), grades answers interactively, and saves scores and weak
  points to AI Learning OS progress.json.
---

# 周五 5 题考察与模拟面试（Friday Quiz & Mock Interview）

严格按 V6 课程表的 8 次考察排期（W1、W2、W3、W4、W6、W8、W10、W12；含 W6 与 W11 综合模拟面试）执行高保真验收。

## 考察规则

- 每次考察 **5 题**，每题 **0–2 分**，满分 **10 分**。
- 评级标准：**≥ 8 分通过**；**6–7 分补读**；**≤ 5 分重学（2 天后重考）**。
- 题目必须现出且紧贴当周实际学过的内容与项目代码，不提前泄露题目或答案。
- 视野拓展主题不进普通周五考察（仅在 W6、W12 综合考察可各带 1 题）。

## 执行步骤

1. **读取上下文**：
   - 读取 `F:\Projects\ai-learning-os\data\curriculum.json`（确认当周学习单元、Lab 与 SreAgent 任务）和 `progress.json`（确认本周实际完成了什么、有哪些历史薄弱点）。
   - 必要时扫一眼 `F:\Projects\SreAgent` 本周最新代码，确保题目结合用户亲手写过的实现。
2. **第一轮：只出题，不给答案**：
   - 一次性或分批给出 5 道题（明确标注每题对应的知识点/项目点，例如 U1a 必含 1 道 MCP 入门题）。
   - 题型分布建议：1 题核心原理、2 题工程设计与安全边界、1 题结合本周代码的场景追问、1 题技术选型与取舍。
   - 提示用户按自己的理解作答，不查资料优先。
3. **第二轮：逐题批改与深度追问**：
   - 针对用户每道题的回答，分别给出：得分（0 / 0.5 / 1 / 1.5 / 2）、答对的点、遗漏或表述不严谨的点、以及面试官视角的标准表达范式。
   - 汇总总分与评级（通过 / 补读 / 重学），提炼 1–3 条本周薄弱点与具体补救建议。
   - 若为 W6 / W11 综合模拟面试，追加 2–3 轮深挖追问（聚焦真实故障数字、架构取舍与事故复盘）。
4. **成绩与薄弱点落盘**：
   - 更新 `F:\Projects\ai-learning-os\data\progress.json` 中 `assessments[week]` 的 `scores`（5 项数组）、`date`、`weakPoints` 与 `updatedAt`。
   - 将有代表性的错题/高频追问补充到 `F:\Projects\SreAgent\docs\INTERVIEW_GUIDE.md`。
