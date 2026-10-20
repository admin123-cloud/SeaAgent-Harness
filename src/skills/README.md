# SreAgent 内置 Skills

本目录保存随项目维护的内置 Skill 资产。用户级 Skill 安装、启用和更新流程暂不在本批范围内。

## 分类

| 分类 | Skill | 用途 |
|---|---|---|
| SRE | `sre/incident-triage` | 处理正在发生或疑似影响用户的事件；界定影响面并协调跨组件证据 |
| SRE | `sre/operational-readiness-check` | 对尚无活动事件的服务做计划性上线准备或周期可靠性检查 |
| SRE | `sre/postmortem` | 服务恢复或稳定后复盘一个已发生事件 |
| Kubernetes | `kubernetes/pod-diagnosis` | 深入诊断一个明确 Pod 的调度、启动、重启或就绪问题 |
| Jenkins | `jenkins/build-failure-triage` | 深入诊断一个 Jenkins Job/Build 的 Pipeline 阶段和构建错误 |

## 选择与交接

- **需要评估活动事件的用户影响、优先级或跨组件协调，或影响范围未知：**从 `sre/incident-triage` 开始，即使已经发现某个 Pod 或 Build 异常。它负责事件概况和证据协调，不重复专项诊断流程。
- **只问一个明确 Pod 的运行原因：**使用 `kubernetes/pod-diagnosis`。若发现请求重点其实是服务影响评估，或影响扩大到多个组件，把关键证据交给 `sre/incident-triage`。
- **只问一个 Jenkins Job/Build 为什么失败：**使用 `jenkins/build-failure-triage`。若 Jenkins 成功但部署后的 Pod 或用户功能异常，转到对应 Pod 专项；需要评估用户影响时转到 `sre/incident-triage`。
- **请求是上线前或定期检查，不是在响应当前故障：**使用 `sre/operational-readiness-check`。它评估当前准备度，不编写事件时间线或根因复盘。
- **事件已恢复或稳定，目标是整理经验和行动项：**使用 `sre/postmortem`。若故障仍在扩大或尚未稳定，先回到 `sre/incident-triage`。
- 一个请求只选一个主 Skill；只有遇到明确的专项子问题时才交接。专项 Skill 的证据摘要可以回到事件分诊或复盘中引用。

每个 Skill 目录包含一个符合 Agent Skills 目录约定的 `SKILL.md`。Skills 描述工作流程和判断方式；它们不新增工具权限，也不代表流程已经自动接入运行时。

以上选择规则是内容层的路由说明；当前运行时未实现 Skill 自动发现或交接，不能据此声称某个 Skill 已自动执行。

当前 `pyproject.toml` 的 wheel `only-include` 尚未包含 `src/skills`；本批资产保存在源码仓库中，若要随安装包发布，之后还需调整打包配置。

## 当前边界

- 只调用当前 Agent 请求中实际提供的只读工具；不要因为 Skill 文档列出某个工具名，就假设该工具已注册或已连接。
- 工具缺失、查询失败或返回信息不足时，标注为“未验证”，并说明还需要哪类证据。
- 本批 Skills 只生成诊断和检查结果，不执行集群变更、重启、扩缩容、回滚或 Jenkins 重跑。
- Kubernetes、Jenkins、SLO、监控、容量、备份等检查结果必须来自可核对的证据；未知不等于通过。
- 研究来源及本地改写范围见 [SOURCES.md](SOURCES.md)。内容按项目场景重新组织，没有整包复制外部 Skill 或数据集。

## 结构

```text
src/skills/
├── sre/
├── kubernetes/
└── jenkins/
```

`humanizer/` 是已有资产，本次保留且未改动。
