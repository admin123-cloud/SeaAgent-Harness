---
name: pod-diagnosis
description: >-
  当请求目标明确为一个或少量 Kubernetes Pod 的调度、启动、反复重启、未就绪、镜像拉取或运行异常时使用。
  跨服务影响评估和事件协调用 incident-triage；Jenkins Job/Build 失败用 build-failure-triage。
metadata:
  category: kubernetes
  language: zh-CN
  version: "1.0.0"
---

# Kubernetes Pod 故障诊断

## 适用范围

本 Skill 只诊断 Pod 与容器运行态。若症状涉及服务整体可用性、多个工作负载或跨组件影响，把 Pod 证据交给 `sre/incident-triage` 统筹；若问题发生在 Jenkins Pipeline 构建阶段，使用 `jenkins/build-failure-triage`。

## 输入要求

尽量确认集群标识、namespace、Pod 名、异常时间范围、预期行为和用户影响。namespace 不在工具允许范围内时，不要尝试绕过 allowlist；说明需要授权的范围。

## 诊断步骤

1. **查看 Pod 列表摘要**
   - 确认目标 Pod 是否存在、Pod phase、Ready 状态、重启次数和创建时间。
   - 如同一工作负载有多个副本，比较正常副本与异常副本，判断故障是否集中于单个实例。
   - 列表没有结果时，先确认 namespace、筛选条件、集群和工具返回状态；不要直接得出“资源不存在”。

2. **查看 Pod 详情**
   - 核对每个容器的 state、last state、退出码、重启次数、镜像摘要、探针结果和调度状态。
   - 区分 Pod phase 与容器状态：Pod 为 `Running` 不代表应用已 `Ready`。
   - 对 `CrashLoopBackOff`，优先确认上一次退出原因和时间；若工具不支持上一实例日志，明确标为证据缺口。

3. **查看近期事件**
   - 按时间顺序关联 Pod 事件与首次异常时间。
   - 重点识别调度失败、拉取镜像失败、卷挂载失败、探针失败、驱逐和容器启动失败等信号。
   - 事件可能已过期或只返回限定窗口；无事件不能证明没有发生过故障。

4. **查看限定范围日志**
   - 先读取异常容器的日志尾部；如果能指定容器和时间范围，按异常开始时间缩小查询。
   - 将日志错误与容器重启时间、退出码、事件关联。
   - 对日志截断、无日志、时区不明或日志来源不确定的情况单独标记。

5. **按状态分支判断**
   - `Pending`：检查调度事件、资源不足、亲和性/污点、PVC 等信号。没有 Node、PVC 或资源指标工具时，只列为未验证项。
   - `ImagePullBackOff` / `ErrImagePull`：核对镜像仓库、路径、标签/摘要和事件错误；不要读取或披露拉取 Secret。
   - `CrashLoopBackOff` / `Error`：关联退出码、上次状态、日志和最近变更；区分应用退出与外部终止。
   - `OOMKilled`：以容器终止状态作为内存压力证据；没有历史用量或 limit 配置时，不推断具体峰值或安全调高资源。
   - `Running` 但未就绪：检查 readiness/liveness/startup probe 事件和容器状态；没有 Service/EndpointSlice 工具时，不判断流量是否已到达 Pod。
   - `Terminating`：查看删除时间和事件；无 finalizer/Webhook 相关信息时，不建议直接删对象或手工移除 finalizer。

6. **输出结论**
   - 将观察事实、推断、未验证内容分栏。
   - 每项建议说明目标、验证方法和风险；只读工具不足以验证时，要求补充证据。
   - 当前 Skill 不执行删除、重启、修改资源、清理 PVC 或变更集群配置。

## 输出格式

```text
资源标识：cluster / namespace / pod / container
当前状态：
时间线：
观察到的证据：状态与退出码 / 事件 / 日志
可能原因（按证据排序）：
未验证项：
建议的只读检查或人工操作：
验证成功的判据：
```

## 可用工具

工具名必须以当前请求的 `available_tools` 为准。项目文档中的候选名称包括 `k8s_list_pods`、`k8s_describe_pod`、`k8s_get_events` 和 `k8s_get_pod_logs`；如果当前未提供，停止对应读取并标记为未验证。

## 参考

- [Kubernetes: Debug Pods](https://kubernetes.io/docs/tasks/debug/debug-application/debug-pods/)
- [IBM Research ITBench-Lite](https://huggingface.co/datasets/ibm-research/ITBench-Lite)
- [bregman-arie/sre-checklist](https://github.com/bregman-arie/sre-checklist)
