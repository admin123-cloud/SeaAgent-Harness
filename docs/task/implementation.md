# 实施任务跟踪

> 本文是 SDD 的执行层台账。需求和验收标准以 [PRD](../PRD.md) 为准；每个任务完成后必须补充验证记录和文档同步情况。

## 1. 文档信息

| 项目 | 内容 |
| --- | --- |
| 项目 | SRE Agent |
| 规范方式 | SDD（Specification-Driven Development） |
| 当前版本 | V0.1 基础层 |
| 当前日期 | 2026-10-27 |
| 总体状态 | `IN_PROGRESS` |
| 当前主线 | 阶段一验收收尾（SDD-005）＋ Skill/Tool 注册链路接入 |

## 2. 状态与更新规则

- `TODO`：没有开始。
- `IN_PROGRESS`：正在设计或实现。
- `VERIFYING`：实现已完成，正在执行验收。
- `BLOCKED`：依赖外部条件，必须写清阻塞原因和解除条件。
- `DONE`：实现、验收和文档同步都完成。
- `CANCELLED`：确认取消，并保留原因。

更新任务时至少填写：状态、完成内容、验证命令/结果、遗留风险和下一步。

## 3. 五阶段进展总览

| 阶段 | 目标 | 状态 | 进入条件 | 退出条件 |
| --- | --- | --- | --- | --- |
| 第一阶段：大模型调用 | 让 Agent 能调用大模型并获得结构化决策 | `IN_PROGRESS` | 状态/证据边界明确 | 至少接通一个模型，输出可校验，错误和敏感信息可控 |
| 第二阶段：Skill/MCP 工具扩展 | 让模型具备查询、根因定位、修复和验证工具 | `TODO` | 第一阶段退出 | 完成查询 → 诊断 → 修复/确认 → 验证闭环 |
| 第三阶段：知识库与历史记忆 | 让模型使用知识、历史聊天和历史事件 | `TODO` | 第二阶段退出 | 召回有来源和权限边界，Incident 可沉淀和复用 |
| 第四阶段：OODA + ReAct | 用外层 OODA 管理事件，用内层 ReAct 执行工具 | `TODO` | 第三阶段退出 | 能循环观察、调整、执行、验证，超限可停止并升级 |
| 第五阶段：持续积累与纠偏 | 用反馈、评估和复盘持续修正定位与修复能力 | `TODO` | 第四阶段退出 | 有版本化改进、回归评估和人工纠偏闭环 |

阶段严格按顺序推进。第五阶段可以反向改进前四阶段，但任何改动仍要先更新 PRD、拆分任务并重新验收。

## 4. 模块任务总览

| ID | 任务 | 依赖 | 状态 | 验收摘要 |
| --- | --- | --- | --- | --- |
| SDD-001 | 建立 SDD 规范文档体系 | 无 | `DONE` | 根目录规范、PRD、任务台账已建立 |
| SDD-002 | MCP Server 受控工具层 | 无 | `BLOCKED` | 2026-10-27 裁定 MCP 接入暂缓；仓库仅存工具候选清单，待重新立项 |
| SDD-003 | Incident 状态与证据模型 | SDD-001 | `DONE` | 模型字段和输入校验已实现；UTC 行为已人工验证 |
| SDD-004 | StateManager 与 SQLite Incident 仓储 | SDD-003 | `IN_PROGRESS` | 可持久化/恢复 Incident，执行状态流转并追加去重证据 |
| SDD-005 | LLM Adapter 结构化决策 | SDD-004 | `IN_PROGRESS` | 模型无关、结构化输出、超时和错误可控；真模型最小调用已通过（2026-10-27） |
| SDD-006 | MCP Client | SDD-002、SDD-005 | `TODO` | 能调用只读 MCP 工具并标准化错误 |
| SDD-007 | Planner / Diagnose 只读闭环 | SDD-004、SDD-006 | `TODO` | 创建 Incident → 收集状态/事件/日志 → 形成假设与建议 |
| SDD-008 | Knowledge、Memory、Context 分层 | SDD-007 | `TODO` | 证据、历史事件和上下文有明确边界 |
| SDD-009 | Verify 与受控 Act | SDD-007 | `TODO` | 生成建议并在确认后执行安全动作，具备审计和回滚 |
| SDD-010 | OODA 外层循环与 ReAct 内层执行 | SDD-005、SDD-006、SDD-007、SDD-008、SDD-009 | `TODO` | 有界循环执行工具，达到后置条件才结束 |
| SDD-011 | 持续积累、评估、定位和纠偏 | SDD-010 | `TODO` | 反馈进入知识、Skill、提示词和回归评估 |
| SDD-012 | 高级 Skill/Tool 管理页面 | SDD-005、SDD-006 | `IN_PROGRESS` | 页面支持 Skill ZIP 导入与 Skill/Tool 元数据 CRUD、启停；变更审计并作用于后续请求 |

## 5. 当前任务明细

### SDD-001 建立 SDD 规范文档体系

- 状态：`DONE`
- 产出：`CLAUDE.md`、`docs/PRD.md`、`docs/task/implementation.md`
- 完成内容：定义文档职责、SDD 工作流、状态枚举、验收门禁和安全边界。
- 验证：检查三个文件存在、UTF-8 可读、相互链接有效、内容与仓库当前实现一致。
- 遗留：后续需求变更必须先更新 PRD，再拆任务。

### SDD-002 MCP Server 受控工具层

- 状态：`BLOCKED`
- 状态变更：2026-10-27 用户裁定 MCP 接入暂缓；原 MCP Server 工具实现已移出仓库，下列“已有实现”仅为历史记录，当前不生效。
- 历史实现（代码已不在仓库）：
  - 工作区列举、读取、搜索、受保护写入和预定义项目命令；
  - Kubernetes Pod、事件、描述和日志读取；
  - Jenkins 构建元数据和控制台尾部读取；
  - namespace、资源名、路径、命令、输出大小和超时限制。
- 当前仓库现状：`src/tools/catalog.py` 仅登记工具候选清单（命名约定 `<领域>_<动作>_<对象>`、权限与风险元数据，不注册 handler）；`src/tools/jenkins.py`、`src/tools/kubernetes.py` 为空占位。
- 解除条件：重新立项 MCP Server 或改为直接工具注册形态，并按下列验收标准执行边界验收。
- 验收标准：
  - [ ] 配置缺失时启动失败且错误可定位；
  - [ ] 越界路径、敏感路径、非 allowlist namespace 被拒绝；
  - [ ] 外部命令失败保留 stderr，并在超时后返回明确错误；
  - [ ] Jenkins 凭据不出现在返回值和日志；
  - [ ] README 的能力列表与实际工具一致。
- 当前风险：当前工作树未发现测试目录；需要后续补充针对边界行为的验证方案。

### SDD-003 Incident 状态与证据模型

- 状态：`DONE`
- 已有实现：`Incident` 已成为 Pydantic 根模型，具备默认状态、空环境/证据、非负迭代次数、非空 `incident_id/goal` 校验、带时区时间校验并转换为 UTC。`Evidence` 已增加可选 `stage` 字段、非空 ID 和 JSON 数据校验；`StatusTransition` 管理状态变化记录。
- 实现要求：
  - `Incident` 使用可校验、可序列化的数据模型；
  - 明确 `schema_version`、事件标识、目标、环境、状态、阶段、证据、迭代次数和时间字段；
  - `incident_id`、`goal` 去除首尾空格后不能为空；
  - `created_at`、`updated_at` 必须带时区并规范为 UTC；
  - `Evidence` 关联产生阶段；
  - Evidence 时间也必须带时区并规范为 UTC。
- 验收标准：见 [PRD FR-004、FR-005、FR-006](../PRD.md#功能需求)。
- 阶段性验收：用户已手动验证无时区时间被拒绝、上海时区时间转换为 UTC；基础构造和 JSON 往返此前通过。
- 后续验证：自动化回归和完整嵌套 Evidence 序列化检查在阶段验收时补齐，不阻塞 SDD-004 开发。
- 后续职责：证据追加/历史保留由 SDD-004 StateManager 实现；数据大小限制、敏感信息过滤和结论引用证据由后续诊断/上下文层实现。

### SDD-004 StateManager、SQLite Repository 与最小状态流转

- 状态：`IN_PROGRESS`
- 持久化决策：采用 Python 标准库 `sqlite3`；默认数据库文件位于项目根目录 `.sre-agent-data/sre-agent.sqlite3`，可由 `SRE_AGENT_DB_PATH` 覆盖，无需增加第三方依赖。
- 职责：`StateManager` 统一管理状态转移、阶段更新、时间戳刷新和证据追加；`IncidentRepository` 集中处理 SQL、读写和事务；模型负责字段与数据不变量校验。
- 模型映射：`incidents` 表对应 Pydantic 根模型 `Incident`；`evidence` 对应 `Evidence`；`status_transitions` 对应 `StatusTransition`。`Incident` 聚合两张子表的记录；项目使用标准库 `sqlite3`，由仓储负责拆分和组装。
- 最小表结构：`incidents` 以 `incident_id` 为主键保存当前字段；`evidence` 外键关联 Incident，并通过 `(incident_id, evidence_id)` 复合主键防重；`status_transitions` 保存 `from_status`、`to_status`、原因和变更时间。SQLite 连接启用外键。时间以带时区 UTC ISO 8601 字符串存储，`environment` 和 `Evidence.data` 以 JSON 文本存储。
- 已写入类：`models/incident.py` 定义根模型；`models/status_transition.py` 定义状态变化模型；`storage/sqlite_database.py` 管理连接、外键、schema 初始化和 `PRAGMA user_version`；`storage/incident_repository.py` 提供 Incident 创建/加载、状态变更和证据追加；`StateManager` 通过仓储完成持久化后再更新内存对象。
- 状态流转：按 PRD FR-005 的图实现合法边；拒绝非法转移；BLOCKED 恢复回 PLANNING；失败和阻塞原因可追踪。
- 原因归属：阻塞/失败原因属于状态变更记录，不直接塞进 `Incident` 的未声明字段；可通过仓储查询状态变更历史。
- 状态变更事务：在一个事务中写入 `status_transitions` 并更新 `incidents`；只有提交成功后才更新内存中的 `Incident`。
- 证据追加事务：在一个事务中插入 Evidence 并刷新 Incident 的 `updated_at`；唯一约束冲突转换成清晰的重复证据错误。可先 `SELECT` 改善错误提示，但它不能替代唯一约束。
- 仓储接口至少覆盖：建表/初始化、创建 Incident、按 ID 加载、保存状态变更、追加 Evidence。`StateManager` 不直接拼 SQL。
- 验收：覆盖正常路径、非法路径、阻塞/恢复、失败终态、Incident 重启恢复、重复证据拒绝和证据不覆盖历史；自动化验证按用户要求放到阶段性检查。
- 当前步骤：本地调试入口已初始化 schema、创建或加载 `incident-001`，并以 `StateManager(state, repository)` 接入生命周期；入口已成功运行。`StateManager` 和 `StatusTransition` 已要求进入 `BLOCKED` 或 `FAILED` 时提供非空原因。状态流转、重启恢复和证据去重的验证仍留到阶段性验收。

### SDD-005 LLM Adapter 结构化决策

- 状态：`IN_PROGRESS`
- 目标：定义模型供应商无关的结构化请求/响应，并通过 Adapter 隔离具体 HTTP/SDK 调用。
- 子任务与命名：

| 子任务 | 文件 | 类型/接口名 | 目标 |
| --- | --- | --- | --- |
| SDD-005-A 决策契约模型 | `models/decision.py` | `DecisionTask`、`DecisionRequest`、`DecisionResponse` | 统一规划/诊断请求和结构化响应 |
| SDD-005-B Adapter 接口 | `agent/llm_adapter.py` | `LLMAdapter` | 定义异步 `decide(request)` 边界 |
| SDD-005-C 调用配置与错误 | `config/llm_settings.py`、`agent/llm_errors.py` | `LLMSettings`、`LLMError` 及具体子类 | 管理模型名、服务地址、密钥引用、超时/重试，并归一化错误 |
| SDD-005-D OpenAI-compatible 实现 | `agent/openai_compatible_adapter.py` | `OpenAICompatibleLLMAdapter` | 调用兼容接口并把响应校验为 `DecisionResponse` |
| SDD-005-E 调用可观测性 | `agent/llm_adapter.py` 及日志配置 | `LLMCallSummary` | 记录耗时、结果类型和错误类型，不记录密钥或完整上下文 |

- 当前步骤：SDD-005-A/B（决策契约与 Adapter 接口）、SDD-005-C（`LLMSettings` 与 `llm_errors` 错误模型）、SDD-005-D（OpenAI-compatible 实现）已完成。2026-10-27 通过 `src/scripts/verify_runtime.py` 完成真模型最小调用验证：模型经 `available_tools`/`available_skills` 注入后主动调用 `demo_echo` 与 `read_skill`（`skill://sre/incident-triage`），两轮工具调用成功，最终结论通过 `DecisionResponse` 校验。请求由调用方提供已脱敏的 Incident 上下文；响应只表达计划、诊断结论、证据引用和建议，不携带可直接执行的工具调用。
- 遗留：SDD-005-E 调用摘要日志（`LLMCallSummary`）未实现；超时/重试/错误归一化路径未系统验收；`verify_runtime.py` 缺可重复断言；`DecisionResponse.evidence_ids` 语义需收紧（真模型曾把工具 call_id 填入证据引用）。
- 后续：依次完成配置/错误模型、一个 OpenAI-compatible 提供方、超时与有界重试、调用摘要日志；阶段性验收再验证真实模型调用、输出 schema 和错误处理。

## 6. 五阶段执行计划

### 阶段一：实现大模型调用

- 状态：`IN_PROGRESS`
- 任务：SDD-003、SDD-004、SDD-005。
- [ ] 完成 `Incident`、`Evidence`、SQLite 仓储和状态流转契约。
- [x] 定义 `LLMAdapter`，隔离供应商、模型配置和传输细节。
- [x] 定义结构化 Prompt 输入、决策输出和 schema 校验。
- [ ] 增加超时、有限重试、错误归一化、敏感信息脱敏和调用记录。
- [x] 用一个真实模型或 OpenAI-compatible 接口完成最小调用验收（2026-10-27 `verify_runtime.py` 真模型通过）。

阶段验收：能够输入一个结构化 Incident，获得可解析的计划/诊断决策；模型不可直接执行工具；调用失败可以定位且不会泄露凭据。

### 阶段二：Skill/MCP 工具扩展

- 状态：`TODO`
- 任务：SDD-002、SDD-006、SDD-007、SDD-009。
- [ ] 建立 Skill/Tool 注册、描述、权限和版本机制。
- [ ] 完成 MCP Client，统一连接、调用、超时和错误对象。
- [ ] 接入工作区、Kubernetes、Jenkins 等查询工具。
- [ ] 将诊断、修复和验证拆成有边界的工具；修复默认人工确认。
- [ ] 实现查询 → 根因假设 → 修复建议/经确认修复 → 验证闭环。

阶段验收：模型只能调用注册工具；每次调用可追踪；修复失败、验证失败、权限不足或风险超限时停止并转人工。

### 阶段三：知识库与历史记忆

- 状态：`TODO`
- 任务：SDD-008。
- [ ] 设计工作记忆、会话记忆、事件记忆和审核知识库的边界。
- [ ] 建立知识摄取、切分、索引、检索和来源引用协议。
- [ ] 保存历史聊天、Incident 摘要、根因、修复和验证结果。
- [ ] 增加相关性、时间、环境、权限和版本过滤。
- [ ] 增加敏感信息隔离、失效、删除和知识过期处理。

阶段验收：模型能召回相关历史并引用来源；无关或越权记忆不会进入上下文；每个结束 Incident 可按策略沉淀。

### 阶段四：OODA 外层循环 + ReAct 内层执行

- 状态：`TODO`
- 任务：SDD-010。
- [ ] 用 Observe、Orient、Decide、Act 组织外层事件循环。
- [ ] 用结构化的目标、行动、观察和下一步组织内层 ReAct 执行。
- [ ] 将工具白名单、参数校验、超时、最大迭代和停止条件接入执行器。
- [ ] 为修复动作增加前置检查、后置验证、幂等性、审计和回滚信息。
- [ ] 将成功、阻塞、失败和人工升级映射到 Incident 状态。

阶段验收：新观察可以驱动计划调整；只有满足后置条件才标记 `RESOLVED`；循环超限或风险上升会停止并升级。

### 阶段五：持续积累与定位纠偏

- 状态：`TODO`
- 任务：SDD-011。
- [ ] 为完成、失败、误判和人工修正建立反馈记录。
- [ ] 建立故障分类、历史回放、离线评估和线上指标。
- [ ] 将重复问题沉淀为知识条目、Skill、诊断规则或回归用例。
- [ ] 对知识、Skill、提示词和策略进行版本、审核、灰度和回滚管理。
- [ ] 建立效果退化检测和人工纠偏流程。

阶段验收：每个 Incident 都能产生可复用结果；改进经过评估和审核；系统不会未经审核地自我修改生产行为。

## 高级功能待开发

### SDD-012 Skill 与 Tool 动态管理

- 状态：`IN_PROGRESS`
- 目标：通过页面展示和维护运行时已注册的 Skill 与 Tool；本任务不属于当前 LLM/只读诊断闭环的阻塞项。
- 已有实现（2026-10-20 ~ 10-23）：内置 Skill 内容库（sre/kubernetes/jenkins 三组共 5 个 SKILL.md + meta.json + SOURCES）；`FileSkillStore`/`SkillRegistry`（builtin 只读 + team 可写双库、原子写、导入暂存与回滚）；`SkillToolkit`（目录快照 + `read_skill`，禁用/未校验按“不存在”口径过滤）；`read_skill` 已注册进默认工具表，`AgentRuntime` 已接入 `skill_toolkit` 并向上下文注入 `available_skills`。2026-10-27 真模型链路验证通过。
- 未实现：第 3 层 `SkillAdminService`（增删改查、启停、校验、审计）、ZIP 导入页面、管理页面全部 UI。
- Skill 管理：导入 `.zip` Skill 包并预览校验结果；创建 Skill 时填写名称、描述、分类、版本、适用任务、Markdown 指引、来源和许可证；支持查询、详情、更新、删除、启用和停用。
- Tool 管理：支持查询、详情、创建、更新、删除、启用和停用；登记名称、用途、已注册实现绑定、输入/输出 Schema、权限、资源范围、风险、副作用、超时和版本。页面只维护注册信息与策略，不通过表单执行任意代码。
- 生命周期：变更留存操作者、时间、来源和版本；启停变更从下一次新请求起生效；删除或停用后保留可追溯的历史记录。
- 安全验收：ZIP 导入拒绝路径穿越和超限文件；缺少 `SKILL.md` 必填字段或 Tool 无有效实现绑定时不允许启用；禁用项不会进入后续模型请求的能力清单。
- 页面验收：管理员能在页面完成上述查询、创建、更新、删除和启停操作，并能查看导入校验结果及变更历史。

## 7. 近期执行顺序

1. `verify_runtime.py` 补齐可重复断言（结果为 `FinalDecision`、事件成对且 round 递增、工具结果 success 全真、`read_skill` 返回含 skill_id/instructions），并定案 FakeLLM 确定性回归与真模型冒烟的脚本分工。
2. 收紧 `DecisionResponse.evidence_ids` 字段描述：只允许引用 Incident Evidence ID，不允许工具 call_id。
3. 实现 SDD-005-E `LLMCallSummary` 调用摘要日志，并完成超时/重试/错误路径验收。
4. 执行阶段一阶段验收（结构化 Incident 输入 → 可解析决策；调用失败可定位且不泄露凭据），随后关闭 SDD-003/004/005。
5. 阶段一退出后按优先级进入 SDD-006 MCP Client 或 SDD-012 管理层；SDD-002 恢复 MCP 形态还是改走直接工具注册，届时重新裁定（候选清单见 `src/tools/catalog.py`）。

## 8. 变更记录

| 日期 | 任务 | 变更 | 验证/备注 |
| --- | --- | --- | --- |
| 2026-09-29 | SDD-001 | 建立规范、PRD 和任务台账 | 文档初版；代码未改动 |
| 2026-09-29 | 路线规划 | 将产品路线明确为大模型调用、工具扩展、知识记忆、OODA/ReAct、持续纠偏五阶段 | 已同步 PRD、CLAUDE 和本台账 |
| 2026-09-30 | 阶段一启动 | 开始指导 Incident 状态模型，为大模型调用准备稳定上下文契约 | 当前执行 SDD-003，代码待用户实现和 Review |
| 2026-10-08 | SDD-003 进展 | Incident/Evidence 字段校验、Evidence.stage 和 UTC 转换已实现；用户手动验证了时区行为 | 自动化回归和嵌套 Evidence 往返在阶段验收补齐 |
| 2026-10-08 | SDD-004 启动 | 按用户节奏开始 StateManager；先定义契约和流转，再实施阶段性验证 | 当前任务：状态流转表、原因记录和证据追加接口 |
| 2026-10-08 | SDD-004 SQLite 实现 | 增加三张表、状态变化 Pydantic 模型、SQLite 数据库类、IncidentRepository，并让 StateManager 通过仓储提交变化 | 未运行测试；应用启动接线和阶段性验收待做 |
| 2026-10-08 | SDD-004 启动接线 | 原 `main.py` 可创建或加载 Incident 并构造 StateManager；入口运行成功；已增加 BLOCKED/FAILED 原因校验 | 状态流转、恢复、持久化和证据去重在阶段性验收时验证；当前已由 Web 工作台承接开发调试 |
| 2026-10-08 | SDD-005 启动 | 开始定义供应商无关的请求/响应模型和 Adapter 接口 | 先稳定结构化契约，再接具体模型调用 |
| 2026-10-08 | SDD-005 决策契约与接口 | 建立 DecisionTask、DecisionRequest、DecisionResponse 与 LLMAdapter 异步接口 | 下一步实现 LLMSettings 和统一错误类型；真实模型调用与阶段验收待后续 |
| 2026-10-10 | 本地事件工作台 | 增加 conversation_entries SQLite 迁移、事件 CRUD、消息处理 API 和本地 Web 工作台；过程记录与事件一起持久化 | 已完成编译和 API 冒烟；真实模型调用依赖本地 LLM_* 配置，MCP 采集闭环仍待 SDD-006/007 |
| 2026-10-19 | SDD-012 高级功能需求 | 记录 Skill ZIP 导入、Skill/Tool 管理页面、CRUD、启停、审计和安全约束 | 仅登记待开发范围，未实现页面或后端功能 |
| 2026-10-20 | Skill 内容库 | 新增 5 个内置 Skill 的 SKILL.md、SOURCES 与分组目录（sre/kubernetes/jenkins） | 内容入库，尚未接入运行时 |
| 2026-10-23 | Skill 体系骨架 | 实现 FileSkillStore/SkillRegistry/SkillToolkit、skill 错误模型；`read_skill` 注册进默认工具表；AgentRuntime 增加 `skill_toolkit` 与 `available_skills` 注入 | 未做系统性验收 |
| 2026-10-27 | SDD-002 暂缓 | 用户裁定 MCP 接入暂缓，原 MCP Server 代码已不在仓库；保留工具候选清单 | 状态转 `BLOCKED`，解除条件见任务明细 |
| 2026-10-27 | SDD-005 真模型验证 | `verify_runtime.py` 以真实 OpenAI-compatible 模型完成最小调用：demo_echo + read_skill 两轮工具调用，`DecisionResponse` 校验通过 | 需补可重复断言；evidence_ids 契约待收紧 |

## 9. 阻塞与风险

| 项目 | 影响 | 解除条件 | 状态 |
| --- | --- | --- | --- |
| 诊断闭环未贯通 | AgentRuntime 主循环与 LLM 调用已验证，但与 Incident 持久化、真实采集工具尚未串成完整闭环 | 完成 SDD-006/007 并接入 StateManager | 开放 |
| 尚未接通大模型 | 阶段一无法进入工具编排 | 完成 SDD-005 并通过结构化调用验收 | 已解除（2026-10-27 真模型最小调用通过） |
| Skill/MCP 修复权限尚未定义 | 阶段二不能安全执行变更 | 为每类修复动作定义权限、确认、幂等、回滚和验证 | 开放 |
| 知识与历史数据边界尚未定义 | 阶段三可能出现越权召回或过期知识 | 完成记忆分层、保留、脱敏和删除策略 | 开放 |
| OODA/ReAct 停止条件尚未定义 | 阶段四可能循环过久或扩大风险 | 定义最大迭代、后置条件、风险阈值和人工升级 | 开放 |
| 当前未建立统一测试目录 | MCP 边界验收缺少自动化证据 | 按任务验收标准补充测试或可重复冒烟 | 开放 |
| Kubernetes/Jenkins 依赖外部环境 | 本地无法覆盖全部集成路径 | 提供受控测试环境或记录人工验证输出 | 开放 |
| verify_runtime 缺可重复断言 | Skill/Runtime 链路验收依赖人眼，回归不可重复 | 补齐弱断言并定案脚本分工 | 开放 |
| DecisionResponse.evidence_ids 契约模糊 | 模型可能把工具 call_id 当作证据引用，污染后续诊断结论的可信度 | 收紧字段描述并回归验证 | 开放 |
