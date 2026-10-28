---
name: postmortem
description: >-
  用于服务恢复或稳定后，撰写或审查一个已发生 SRE 事件的复盘，整理影响、时间线、原因、响应过程和可跟踪的改进行动。
  活动事件响应使用 incident-triage；计划性可靠性或上线准备检查使用 operational-readiness-check。
metadata:
  category: sre
  language: zh-CN
  version: "1.0.0"
---

# SRE 事件复盘

## 前置条件

确认服务已经恢复或稳定后再做复盘。收集事件记录、工具证据、告警和变更时间线；涉及不同团队时标注来源和时区。若影响仍在扩大或恢复尚未稳定，先使用 `sre/incident-triage` 继续响应，不要让复盘阻断减轻影响。

## 编写步骤

1. **说明事件摘要**：服务、环境、发生时间、持续时间、影响用户/功能、业务影响和最终恢复时间。缺少数据时注明估算或未知。
2. **建立时间线**：首次症状、告警、确认影响、关键决策、缓解措施、恢复验证。区分自动时间戳、人员回忆和推定时间。
3. **拆分原因**：
   - 触发因素：使故障开始或暴露的问题。
   - 直接机制：系统如何从触发因素发展为用户影响。
   - 促成条件：监控、架构、容量、发布、依赖或流程中让影响扩大/持续的条件。
   - 证据不足的因果关系写成待验证假设。
4. **评估响应过程**：发现时延、告警质量、沟通与职责、诊断效率、缓解方案、恢复验证，以及有效做法和阻碍因素。
5. **形成改进项**：每项都应指向风险降低、检测提早或恢复加快，指定负责人、截止时间、优先级、完成定义和验证方法。
6. **检查措辞**：解释系统、流程和防护如何导致结果；不归咎个人、不写羞辱性描述，也不把“加强注意”当成唯一措施。

## 输出模板

```text
事件标题 / 服务 / 环境：
摘要：
影响：
检测与恢复：
时间线：
触发因素：
直接故障机制：
促成条件：
哪些措施有效 / 哪些造成延迟：
证据缺口：
行动项：负责人 | 截止日期 | 优先级 | 完成定义 | 验证方式
```

## 证据规则

- 保留来源、时间范围和对象标识；不要把回忆、推断和工具观测混在一起。
- 统计影响和时长应说明计算口径；无法确认时标为估算。
- 根因必须有证据链；暂时没有就记录“尚未确认”，并给出补充验证计划。
- 脱敏日志、用户标识、内部主机名和凭据；只保留复盘所需信息。

## 参考

- [Google SRE: Incident Management Guide](https://sre.google/resources/practices-and-processes/incident-management-guide/)
- [Google SRE Workbook: Postmortem Analysis](https://sre.google/workbook/postmortem-analysis/)
- [agentic-awesome-skills: incident-responder](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/incident-responder/SKILL.md)
