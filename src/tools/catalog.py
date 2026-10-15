"""后续工具候选清单。

这里只记录规划中的工具和权限，不注册 handler，也不会出现在 AgentRuntime
提供给模型的 available_tools 中。实现 handler 后，再将工具注册到默认 Registry。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolCandidate:
    name: str
    description: str
    required_permissions: frozenset[str]
    risk_level: str = "low"


TOOL_CANDIDATES: tuple[ToolCandidate, ...] = (
    ToolCandidate(
        name="get_server_health",
        description="查询指定服务器的基础健康状态。",
        required_permissions=frozenset({"server.health.read"}),
    ),
    ToolCandidate(
        name="get_server_metrics",
        description="查询指定服务器的 CPU、内存和磁盘使用情况。",
        required_permissions=frozenset({"server.metrics.read"}),
    ),
    ToolCandidate(
        name="list_k8s_nodes",
        description="按集群查询 Kubernetes 节点状态。",
        required_permissions=frozenset({"k8s.nodes.read"}),
    ),
    ToolCandidate(
        name="list_k8s_pods",
        description="按集群和 namespace 查询 Pod 列表，可选标签筛选。",
        required_permissions=frozenset({"k8s.pods.read"}),
    ),
    ToolCandidate(
        name="get_k8s_pod_detail",
        description="查询指定 Pod 的状态、容器和调度详情。",
        required_permissions=frozenset({"k8s.pods.read"}),
    ),
    ToolCandidate(
        name="list_k8s_events",
        description="按集群和 namespace 查询近期 Kubernetes 事件。",
        required_permissions=frozenset({"k8s.events.read"}),
    ),
    ToolCandidate(
        name="get_k8s_pod_logs",
        description="查询指定 Pod 容器在限定时间和行数范围内的日志。",
        required_permissions=frozenset({"k8s.pods.logs.read"}),
    ),
    ToolCandidate(
        name="create_k8s_pod",
        description="在指定 namespace 创建 Pod；请求批准模式下应审批本次调用。",
        required_permissions=frozenset({"k8s.pods.create"}),
        risk_level="high",
    ),
)
