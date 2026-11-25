---
name: code-review-verify
description: >-
  Use this skill when the user finishes writing code or asks to review, check, or verify a task
  or commit (e.g. "帮我 review", "验收 15.1a", "我写好了检查一下"). Runs local verification commands,
  checks package dependency direction and security boundaries, provides structured teaching feedback,
  and syncs implementation.md and AI Learning OS progress upon user confirmation.
---

# 本地真实验收与代码 Review（Code Review & Verify）

将代码审查、本地自动化验收、教学四件套点评与进度同步收拢为一个确定性闭环。

## 执行步骤

1. **检查变更范围**：
   - 在 `F:\Projects\SreAgent` 运行 `git status -sb` 与 `git diff`（或 `git show --stat`），确认变更严格落在当前任务范围内；确认**搬家与改逻辑未混在同一步**。
2. **执行硬性本地验证（不靠肉眼猜测）**：
   - **全包导入检查**：在 `src` 目录下运行 `python -c "import agent, tools, skills, web_app; print('imports ok')"`。
   - **包依赖方向检查（`CLAUDE.md §6`）**：
     - `tools/*.py` 不得导入 `agent` 或 `skills`；
     - `skills/*.py` 不得导入 `agent`、`bootstrap`、`database`、`config`、`web_app`；
     - `agent/*.py` 不得导入 `bootstrap`。
   - **运行验收脚本**：运行当前任务对应的离线验证脚本（如 `python -m scripts.verify_registry`、`python -m scripts.verify_runtime --offline` 或 `pytest`），记录准确命令与退出码。
   - **安全与脱敏扫描**：检查是否存在硬编码密钥、未脱敏的异常原文拼接（如把网关 401/凭据/SA 信息拼入日志或 summary）、`print(env)` 等敏感信息泄露，以及越权/写操作风险。
   - 如涉及真实 LLM 或外部 K8s 集群验证且本机环境未直接执行，必须明确列为**未验证项**，禁止臆测通过。
3. **输出结构化 Review 报告**：
   - **验收结论**：明确给出 `PASS` / `NEEDS_FIX` / `VERIFYING（缺真实环境证据）`，附实际执行的命令、退出码与关键输出摘要。
   - **代码缺陷与改进建议**：按「必须修（阻断验收） / 建议优化（可延后）」分层，指出具体文件路径和行号，给出修法思路（默认不直接代改业务代码）。
   - **教学四件套标注**：
     1. 面试考点
     2. 业界做法
     3. 本项目的取舍
     4. 原理锚点
   - **1 道对标面试题**：紧扣本次改动出 1 道面试追问，等待用户作答；同时把题目登记到 `F:\Projects\ai-learning-os\data\progress.json` 的 `interviewQueue`。
4. **文档与进度同步（门禁生效后）**：
   - 仅当验收全部通过且用户确认后：
     - 更新 `F:\Projects\SreAgent\docs\task\implementation.md` 中对应任务的验证记录与状态；
     - 更新 `F:\Projects\ai-learning-os\data\progress.json` 对应任务状态与时间戳；
     - 如产生新的高频面试考点或项目踩坑案例，同步补充到 `docs/INTERVIEW_GUIDE.md`（跨项目经验沉淀到 `H:\Agent-Memory-System`）。
   - 提醒用户推送前先执行 `git pull --rebase`。
