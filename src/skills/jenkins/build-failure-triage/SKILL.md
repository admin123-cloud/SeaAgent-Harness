---
name: build-failure-triage
description: >-
  当请求目标明确为一个 Jenkins Job/Build 的 Pipeline 失败、状态异常或构建结果不符预期时使用。
  构建后 Pod 运行故障用 pod-diagnosis；跨组件用户影响和事件协调用 incident-triage；计划性服务检查用 operational-readiness-check。
metadata:
  category: jenkins
  language: zh-CN
  version: "1.0.0"
---

# Jenkins 构建失败分诊

## 适用范围

本 Skill 诊断 Jenkins Job/Build 自身及其 Pipeline 记录的制品交付步骤，不负责集群运行态或服务整体健康判断。若 Pipeline 已成功但 Pod 未启动，转到 `kubernetes/pod-diagnosis`；若已影响用户或涉及多个组件，由 `sre/incident-triage` 评估和协调。

## 输入要求

尽量确认 Jenkins 地址/实例、Job 全名、build number、分支、提交 SHA、目标环境和大致发生时间。没有 build number 时先查 Job 的最近构建元数据，不要凭标题猜一个构建。

## 诊断步骤

1. **读取构建状态与元数据**
   - 核对 build number、结果、开始/结束时间、持续时间、分支、提交或触发来源（工具提供哪些就记录哪些）。
   - 区分 `FAILURE`、`UNSTABLE`、`ABORTED`、仍在执行和查询失败。
   - 若构建是新版本部署的一部分，先核对它是否对应用户所说的提交；不要把源码分支已更新等同于镜像已构建或部署已完成。

2. **读取 Console Output**
   - 从日志尾部或失败阶段上下文找到最终失败位置，再向前定位该阶段最早出现的、能够解释失败的错误。
   - 把根因与后续级联错误、清理错误、通知错误分开。
   - 如果日志被截断或只返回尾部，说明缺少前文，不要声称找到了首个根因。

3. **归类失败阶段**
   - **SCM/checkout**：仓库、凭据引用、分支/提交和 fetch 错误。
   - **环境/Agent**：executor、工具版本、磁盘、网络、权限或 Kubernetes Agent 分配。
   - **依赖/编译/测试**：首个依赖解析、编译或测试失败，而不是只报告流水线末尾的总失败。
   - **制品/镜像**：tag/digest、架构、仓库路径、推送结果和后续实际消费的制品。
   - **部署/验证**：只核对 Pipeline 记录的构建、发布和验证步骤及制品对应关系；集群 rollout 细节交给 Pod 专项，用户面健康与影响范围交给事件分诊。

4. **检查环境与代码的区分证据**
   - 比较同一 Job 的最近成功构建与失败构建（如果工具提供）。
   - 结合失败阶段、变更提交、Agent/环境报错和依赖服务状态判断更像代码问题还是环境问题。
   - 证据不足时用“尚不能区分”，不要把短暂网络、资源或凭据错误归为代码缺陷。

5. **给出建议**
   - 先建议只读核验（例如对照 Jenkinsfile、工具版本、制品摘要和目标环境状态）。
   - 当前 Skill 不修改 Job、凭据、Jenkinsfile，不重跑或从失败阶段恢复 Pipeline；需人工确认后再执行有副作用的操作。

## 输出格式

```text
Job / Build：
构建状态与时间：
分支 / commit / 制品（若可见）：
失败阶段：
首个有效错误：
根因判断：代码 / 环境 / 外部依赖 / 尚不能区分
支持证据：
未验证项：
建议的下一步及验证方式：
```

## 工具约定

仅使用当前 `available_tools` 中实际出现的工具。项目文档列出的 `jenkins_get_build` 与 `jenkins_get_console` 是预期只读能力示例，不保证已在当前运行时注册。日志中若含密码、Token、私钥或环境变量值，输出前必须脱敏。

## 参考

- [Jenkins: Getting started with Pipeline](https://www.jenkins.io/doc/book/pipeline/getting-started/)
- [Jenkins: Running Pipelines](https://www.jenkins.io/doc/book/pipeline/running-pipelines/)
- [arjunprabhulal/devops-skills](https://github.com/arjunprabhulal/devops-skills)（流程写作参考；本文件独立改写）
