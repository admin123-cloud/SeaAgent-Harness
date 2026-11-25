# Graph Report - src  (2026-11-25)

## Corpus Check
- 68 files · ~10,179 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 564 nodes · 1311 edges · 34 communities (17 shown, 17 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 117 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `91828c6c`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `python scripts/graphify_project.py update` after code changes (no API cost).

## Community Hubs (Navigation)
- store.py
- IncidentRepository
- SREWebApp
- errors/__init__.py
- state_manager.py
- web_app.py
- openai_compatible_llm_adapter.py
- IncidentRepository
- json
- runtime.py
- Incident
- 内置 Skills 的研究来源
- Incident
- SRE 运行准备度检查
- Jenkins 构建失败分诊
- tools/registry.py
- Kubernetes Pod 故障诊断
- SRE 事件分诊
- model/models/kubernetes_observation.py
- Evidence
- SRE 事件复盘
- ConversationEntry
- StatusTransition

## God Nodes (most connected - your core abstractions)
1. `IncidentRepository` - 28 edges
2. `IncidentRepository` - 27 edges
3. `SREWebApp` - 23 edges
4. `SkillRegistry` - 22 edges
5. `Incident` - 21 edges
6. `SkillDetail` - 21 edges
7. `OpenAICompatibleLLMAdapter` - 19 edges
8. `DecisionRequest` - 19 edges
9. `FileSkillStore` - 19 edges
10. `Incident` - 19 edges

## Surprising Connections (you probably didn't know these)
- `OpenAICompatibleLLMAdapter` --uses--> `DecisionRequest`  [INFERRED]
  src/agent/openai_compatible_llm_adapter.py → request/decision_request.py
- `StateManager` --uses--> `IncidentStatus`  [INFERRED]
  src/agent/state_manager.py → enums/incident_status.py
- `StateManager` --uses--> `Evidence`  [INFERRED]
  src/agent/state_manager.py → models/evidence.py
- `StateManager` --uses--> `Incident`  [INFERRED]
  src/agent/state_manager.py → models/incident.py
- `StateManager` --uses--> `StatusTransition`  [INFERRED]
  src/agent/state_manager.py → models/status_transition.py

## Import Cycles
- None detected.

## Communities (34 total, 17 thin omitted)

### Community 0 - "store.py"
Cohesion: 0.07
Nodes (20): SkillConflict, SkillError, SkillForbidden, SkillImportError, SkillInvalid, SkillNotFound, SkillReadOnly, SkillDetail (+12 more)

### Community 1 - "IncidentRepository"
Cohesion: 0.18
Nodes (4): IncidentAlreadyExistsError, IncidentNotFoundError, IncidentRepository, IncidentStatusConflictError

### Community 3 - "errors/__init__.py"
Cohesion: 0.12
Nodes (11): _is_cert_error(), K8sApiError, K8sConnectError, K8sError, K8sForbiddenError, K8sNotFoundError, K8sTlsError, K8sUnauthorizedError (+3 more)

### Community 4 - "state_manager.py"
Cohesion: 0.10
Nodes (6): IncidentStatus, WorkflowStage, Evidence, utc_now(), utc_now(), utc_now()

### Community 5 - "web_app.py"
Cohesion: 0.05
Nodes (11): demo_tool(), utc_now(), FinalDecision, ToolCallDecision, DecisionResponse, ToolCallDecision, KubernetesObservation, ToolCall (+3 more)

### Community 6 - "openai_compatible_llm_adapter.py"
Cohesion: 0.20
Nodes (12): _build_message(), _correction_message(), FormatStats, Message, OpenAICompatibleLLMAdapter, _parse(), LLMAuthenticationError, LLMError (+4 more)

### Community 7 - "IncidentRepository"
Cohesion: 0.05
Nodes (9): DuplicateEvidenceError, IncidentAlreadyExistsError, IncidentNotFoundError, IncidentRepository, IncidentStatusConflictError, SQLiteDatabase, ConversationEntry, StatusTransition (+1 more)

### Community 8 - "json"
Cohesion: 0.21
Nodes (6): FingerCount, fingerprint_of(), normalize_args(), ProgressObservation, signature_of(), content_hash_of()

### Community 9 - "runtime.py"
Cohesion: 0.06
Nodes (24): LLMAdapter, ProgressTracker, AgentRuntime, AgentDeps, build_deps(), LLMSettings, load_llm_settings(), DecisionTask (+16 more)

### Community 10 - "Incident"
Cohesion: 0.17
Nodes (3): StateManager, Incident, DuplicateEvidenceError

### Community 11 - "内置 Skills 的研究来源"
Cohesion: 0.15
Nodes (11): SreAgent 内置 Skills, 分类, 当前边界, 结构, 选择与交接, GitHub, Hugging Face, ModelScope (+3 more)

### Community 13 - "SRE 运行准备度检查"
Cohesion: 0.22
Nodes (8): SRE 运行准备度检查, 参考, 工具约定, 检查范围, 检查项, 结果判定, 输出格式, 适用范围

### Community 15 - "Jenkins 构建失败分诊"
Cohesion: 0.25
Nodes (7): Jenkins 构建失败分诊, 参考, 工具约定, 诊断步骤, 输入要求, 输出格式, 适用范围

### Community 20 - "tools/registry.py"
Cohesion: 0.09
Nodes (16): ToolInputValidationError, ToolNotFoundError, ToolCall, ToolResult, check_execution_and_runtime(), check_spec_and_naming(), _DummyLLM, expect() (+8 more)

### Community 23 - "Kubernetes Pod 故障诊断"
Cohesion: 0.25
Nodes (7): Kubernetes Pod 故障诊断, 参考, 可用工具, 诊断步骤, 输入要求, 输出格式, 适用范围

### Community 24 - "SRE 事件分诊"
Cohesion: 0.25
Nodes (7): SRE 事件分诊, 参考, 工具约定, 流程, 目标, 输出格式, 适用范围与分工

### Community 29 - "SRE 事件复盘"
Cohesion: 0.29
Nodes (6): SRE 事件复盘, 前置条件, 参考, 编写步骤, 证据规则, 输出模板

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `python scripts/graphify_project.py query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SREWebApp` connect `SREWebApp` to `web_app.py`, `openai_compatible_llm_adapter.py`, `IncidentRepository`, `runtime.py`, `Incident`, `Incident`, `ConversationEntry`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `SQLiteDatabase`) actually correct?**
  _`IncidentRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `store.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06905370843989769 - nodes in this community are weakly interconnected._
- **Why does `StateManager` connect `Incident` to `IncidentRepository`, `SREWebApp`, `state_manager.py`, `web_app.py`, `IncidentRepository`, `runtime.py`, `Incident`, `Evidence`, `StatusTransition`?**
  _High betweenness centrality (0.046) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `IncidentStatus`) actually correct?**
  _`IncidentRepository` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `errors/__init__.py` be split into smaller, more focused modules?**
  _Cohesion score 0.12436974789915967 - nodes in this community are weakly interconnected._
- **Why does `build_deps()` connect `runtime.py` to `store.py`, `tools/registry.py`, `web_app.py`, `IncidentRepository`?**
  _High betweenness centrality (0.044) - this node is a cross-community bridge._