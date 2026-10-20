# 内置 Skills 的研究来源

整理日期：2026-10-19

以下来源用于提取流程结构、检查维度和评估场景。`src/skills/**/SKILL.md` 的正文是针对 SreAgent 当前只读诊断方向重新编写的内容，不是外部 Skill 或数据集的副本。

## GitHub

- [sickn33/agentic-awesome-skills](https://github.com/sickn33/agentic-awesome-skills)（约 47.9k stars）：高热度的多领域 Skill 合集。只参考其中 [incident-responder](https://github.com/sickn33/agentic-awesome-skills/blob/main/skills/incident-responder/SKILL.md) 的事件流程主题；不将整个集合或某个 Skill 的星数视为质量保证。
- [bregman-arie/sre-checklist](https://github.com/bregman-arie/sre-checklist)（约 2.6k stars）：非 Agent Skill 的 SRE 检查清单，用于整理运行准备度检查项。仓库作者明确说明其内容具有个人观点，不能直接当作适用于所有组织的标准。

## 官方技术文档

- [Kubernetes：Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)：Pod 状态、容器状态和近期事件的故障定位顺序。
- [Jenkins：Getting started with Pipeline](https://www.jenkins.io/doc/book/pipeline/getting-started/)：构建详情和 Console Output 的定位入口。
- [Jenkins：Running Pipelines](https://www.jenkins.io/doc/book/pipeline/running-pipelines/)：流水线阶段重跑能力的说明。本项目当前 Skill 不发起重跑，只用于界定“重跑”属于有副作用的操作。
- [Google SRE：Incident Management Guide](https://sre.google/resources/practices-and-processes/incident-management-guide/) 与 [Postmortem Analysis](https://sre.google/workbook/postmortem-analysis/)：事件响应、无责复盘、触发原因和改进项的组织方式。

## Hugging Face

- [IBM Research ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite)（Apache-2.0）：卡片列出 65 个场景，其中 35 个 SRE 故障定位场景，包含日志、指标、追踪、Kubernetes 事件和资源状态等证据维度。只借鉴证据分类和评估思路，不复制场景数据；其卡片也指出静态快照缺少实时观测和交互式排障特征。

## ModelScope

- [ModelScope Skills Center](https://modelscope.cn/skills)：作为 Skills 目录进行检索。本次检索未找到足够匹配 SreAgent 当前 Kubernetes/Jenkins 只读排障流程、且可直接采用的 SRE 运维 Skill。
- [StabilityLab/zhiyu](https://modelscope.cn/models/StabilityLab/zhiyu)：这是 SRE 领域模型而非 Skill。其模型卡涉及运维经验、组件文档、真实故障案例和 SQL/PromQL 等专业能力维度；这里只用于交叉检查分类是否遗漏，不采用模型权重或训练数据。

## 适配原则

1. 外部材料只作为起草和复核依据；最终判断标准以目标服务的 SLO、告警规则、值班流程和权限策略为准。
2. 星数、下载量和平台收录情况只是发现信号，不代表运行安全、内容正确或适合本项目。
3. 如后续要直接引入外部 Skill 包，需单独保留其上游来源、版本、许可证和修改记录。本批生成的是本项目新写的内置流程文档。
