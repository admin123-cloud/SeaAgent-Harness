# SRE Agent MCP

这是 SRE Agent 的 Python V0.1 基础层。它目前是一个模型无关的 Streamable HTTP MCP Server，先提供受控的本地工作区工具；后续可接入 Kubernetes、Jenkins、Prometheus、Loki，并由 ChatGPT、Codex 或私有化模型作为不同的推理入口。

当前 SRE MCP 工具层已具备基础能力；Agent Runtime 尚未实现。接下来从状态模型开始，由用户亲自编写，按小步完成后再逐层接入模型和 MCP Client。

## V0.1 能力

- `workspace_list_files`：列出工作区文件，跳过生成目录。
- `workspace_read_file`：读取 UTF-8 文本文件或指定行区间。
- `workspace_search_code`：使用 ripgrep 搜索，限制结果数量。
- `workspace_write_file`：工作区内创建/替换文件，替换需要显式 `overwrite=true`。
- `workspace_run_project_command`：只允许 Git 状态、Git diff、Maven test、Maven compile。
- `k8s_list_pods`：读取 allowlist namespace 内的 Pod 摘要。
- `k8s_describe_pod`：读取单个 Pod 的状态、容器和调度信息。
- `k8s_get_pod_logs`：读取指定 Pod 日志尾部，默认最多 200 行。
- `k8s_get_events`：读取 namespace 最近事件。
- `jenkins_get_build`：读取 Jenkins 构建状态和元数据。
- `jenkins_get_console`：读取 Jenkins 控制台日志尾部。

默认拒绝 `.env`、SSH 密钥、kubeconfig、常见证书/密钥文件等敏感路径。Kubernetes namespace 必须在 `K8S_ALLOWED_NAMESPACES` 中。`WORKSPACE_ROOT` 必须显式配置。V0.1 不提供任意 Shell 执行，也不提供 Pod 重启、Deployment 修改或 Jenkins 重跑。

## 本地运行

需要 Python 3.12+ 和 ripgrep。当前开发机已具备 Python 3.14。

```powershell
Copy-Item .env.example .env
# 按需修改 WORKSPACE_ROOT 和 MAVEN_COMMAND
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m sre_agent_mcp.server
```

## 本地 SRE 事件工作台

开发和调试不再需要直接运行 `main.py`。使用本地 Web 工作台按事件管理对话，并查看 Agent 的结构化处理过程：

```powershell
python -m sre_agent.web_app
# 或安装项目后执行
sre-agent-web
```

打开 <http://127.0.0.1:8765>。事件、聊天消息、状态变化、模型请求/响应和错误记录在 `.sre-agent-data/sre-agent.sqlite3`，重启页面或进程后仍可恢复。可以通过 `SRE_AGENT_WEB_HOST`、`SRE_AGENT_WEB_PORT` 和 `SRE_AGENT_DB_PATH` 调整监听地址、端口和数据库位置。

当前工作台只展示模型已返回的结构化结果和可审计的过程记录，不把未接入的 Kubernetes/MCP 采集步骤伪装成已执行。

MCP 地址：

```text
http://127.0.0.1:8787/mcp
```

Kubernetes 和 Jenkins 工具需要在 `.env` 中配置对应的访问范围和凭据。Jenkins 建议使用只读 API Token；不要把密码、Token 或 kubeconfig 内容作为工具返回值交给模型。

## 后续架构

```text
SRE Agent Core
    ├── Model Adapter
    │     ├── OpenAI
    │     ├── OpenAI-compatible 私有模型
    │     └── 本地模型
    └── MCP Client
          └── SRE MCP Server
                ├── Kubernetes
                ├── Jenkins
                ├── Prometheus
                └── Loki
```

ChatGPT 只是备用入口，不是 SRE Agent 的核心依赖。

## 分阶段实施

```text
Step 1  设计并实现 Incident + StateManager + Workflow 状态机  ← 当前
Step 2  LLM Adapter，先支持结构化 Decision
Step 3  MCP Client，连接当前 SRE MCP Server
Step 4  Planner + Diagnose，只读 Pod 故障闭环
Step 5  Knowledge / Memory / Context 管理
Step 6  Verify 和人工确认型 Act
```

第一条业务闭环固定为：创建 Incident → 获取 Pod 状态 → 获取事件 → 获取日志 → 形成假设 → 输出根因和建议。V0.1 的 Act 只生成建议，不执行集群修改。

## 开发协作规范

本项目采用“用户主写、助手主导”的协作模式，详细约定见 [开发协作规范](docs/DEVELOPMENT_GUIDE.md)：

- 用户负责 Python 代码实现、命令执行和逐步实验；
- 助手负责架构拆解、概念解释、任务分步、接口设计、伪代码、Review 和错误定位；
- 默认不直接代写或修改核心业务代码，只有用户明确要求提供代码或补丁时才例外；
- 每一步先明确目标、输入、实现要求和验收标准，用户完成后再进入下一步。
