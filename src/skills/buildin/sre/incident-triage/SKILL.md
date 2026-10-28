---
name: incident-triage
description: >-
  当正在发生或疑似影响用户的事件需要界定影响面、优先级或协调跨组件证据时使用；范围未知时也从这里开始。
  若请求已明确为单个 Pod 的运行诊断或单个 Jenkins Build 的失败分析，直接使用对应专项 Skill；恢复后复盘用 postmortem，计划检查用 operational-readiness-check。
metadata:
  category: sre
  language: zh-CN
  version: "1.0.0"
---

# SRE 事件分诊

## 适用范围与分工

本 Skill 负责事件概况、用户影响、紧急程度和跨组件证据协调。它是活动事件的入口，不替代专项诊断：

- 目标明确为一个 Pod 的调度、启动、重启或就绪问题时，使用 `kubernetes/pod-diagnosis` 深入分析；把确认过的证据摘要带回事件记录。
- 目标明确为一个 Jenkins Job/Build 的 Pipeline 失败时，使用 `jenkins/build-failure-triage` 深入分析；若构建成功但部署后服务异常，继续检查运行态并评估用户影响。
- 影响范围未知、跨多个组件或需协调服务恢复时，由本 Skill 统筹；只收集专项判断所需的高层证据，避免重复完整的 Pod/Jenkins 诊断清单。
- 服务恢复或稳定后需要整理原因与行动项时，转到 `sre/postmortem`；计划性上线准备或周期检查转到 `sre/operational-readiness-check`。

当前运行时如果不能加载或交接多个 Skill，只能按请求选择一个主流程并引用已提供的证据，不得声称交接或调用已发生。

## 目标

尽快建立可信的事件概况，优先降低用户影响，并让每个判断都能追溯到证据。不要在证据不足时把相关现象写成已确认根因。

## 流程

1. **确认目标与时间范围**
   - 确认服务、环境、集群、namespace、资源名，以及症状开始时间。
   - 记录用户影响、受影响功能、范围、是否持续扩大，以及最近的发布或配置变更。
   - 缺少关键标识时，先问最少量的问题；可以先用现有信息开展的只读检查则继续进行。

2. **评估影响与紧急程度**
   - 区分单个工作负载异常与服务整体不可用。
   - 评估用户影响面、持续时间、关键业务路径、错误率/延迟变化和可用替代路径。
   - 优先使用团队已定义的事件级别或 SLO。没有标准或数据时，标记“级别待确认”，不自行套用固定的 P1/P2 阈值。

3. **建立只读证据集**
   - 先收集判断影响范围所需的概要证据，例如受影响工作负载数量/状态、近期变更和关联构建的状态与版本。
   - 只有当请求需要跨组件判断或解释用户影响时，才扩展到详细证据；单个 Pod 的状态、事件和日志深查交给 `kubernetes/pod-diagnosis`，单个 Jenkins Build 的阶段和控制台日志分析交给 `jenkins/build-failure-triage`。
   - 每条证据记录来源、时间范围、对象标识和原始结果摘要。
   - 工具未连接、调用失败、结果截断或缺少时间戳时，如实注明；不得用空结果证明资源不存在或系统健康。

4. **形成并排序假设**
   - 每个假设都写清支持证据、反向证据、尚缺信息和置信度。
   - 先检查最近变更、明确失败状态和影响范围，再扩展到依赖、容量、网络或存储。
   - 把“触发因素”“直接故障”和“根因”分开；根因需等证据足够后再确认。

5. **给出恢复建议与升级条件**
   - 先列出低风险、可回退、能快速降低影响的建议及其验证方式。
   - 当前只生成建议，不调用重启、扩缩容、修改配置、回滚或重跑工具。
   - 影响扩大、数据完整性受威胁、安全事件、关键 SLO 明显违约或关键证据不可用时，建议联系对应值班负责人/系统所有者。

## 工具约定

仅从当前请求提供的 `available_tools` 中选择工具。以下名称是本项目文档中的只读工具示例；实际列表没有该名称时，不得调用或声称已执行：

- Kubernetes：`k8s_list_pods`、`k8s_describe_pod`、`k8s_get_events`、`k8s_get_pod_logs`
- Jenkins：`jenkins_get_build`、`jenkins_get_console`

不要读取或输出 Secret、Token、密码、环境变量中的凭据或 kubeconfig 内容。日志和控制台内容中出现凭据时，脱敏后再引用。

## 输出格式

```text
事件摘要：
影响范围：
开始时间/持续时间：
事件级别：已确认 / 待确认（依据）
已检查证据：
主要假设：支持证据 / 反向证据 / 置信度
尚未验证：
建议的下一步：动作 / 目的 / 成功判据 / 风险
需要人工升级：是 / 否（原因）
```

## 参考

- [Google SRE Incident Management Guide](https://sre.google/resources/practices-and-processes/incident-management-guide/)
- [agentic-awesome-skills: incident-responder](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/incident-responder/SKILL.md)
- [IBM Research ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite)
