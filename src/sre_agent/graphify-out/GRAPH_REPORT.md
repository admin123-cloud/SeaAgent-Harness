# Graph Report - sre_agent  (2026-10-12)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 243 nodes · 426 edges · 23 communities (6 shown, 17 thin omitted)
- Extraction: 84% EXTRACTED · 16% INFERRED · 0% AMBIGUOUS · INFERRED: 69 edges (avg confidence: 0.92)
- Token cost: 21,217 input · 228 output

## Graph Freshness
- Built from commit: `d382df05`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- LLM Adapter Runtime
- Incident Repository
- Agent Decision Flow
- Incident State Management
- Domain Models Module
- Tool Registry Execution
- LLM Error Handling
- Conversation Entry Model
- Evidence Model
- Status Transition Model
- HTTP Request Handler
- Default Demo Tools
- Kubernetes Observation Model

## God Nodes (most connected - your core abstractions)
1. `IncidentRepository` - 27 edges
2. `SREWebApp` - 20 edges
3. `Incident` - 20 edges
4. `Evidence` - 14 edges
5. `OpenAICompatibleLLMAdapter` - 13 edges
6. `StatusTransition` - 13 edges
7. `StateManager` - 12 edges
8. `ToolRegistry` - 12 edges
9. `ConversationEntry` - 12 edges
10. `DecisionRequest` - 11 edges

## Surprising Connections (you probably didn't know these)
- `Evidence` --uses--> `WorkflowStage`  [INFERRED]
  models/evidence.py → enums/workflow_stage.py
- `Incident` --uses--> `WorkflowStage`  [INFERRED]
  models/incident.py → enums/workflow_stage.py
- `StateManager` --uses--> `IncidentRepository`  [INFERRED]
  agent/state_manager.py → storage/incident_repository.py
- `IncidentRepository` --uses--> `IncidentStatus`  [INFERRED]
  storage/incident_repository.py → enums/incident_status.py
- `IncidentRepository` --uses--> `ConversationEntry`  [INFERRED]
  storage/incident_repository.py → models/conversation_entry.py

## Import Cycles
- None detected.

## Communities (23 total, 17 thin omitted)

### Community 1 - "Incident Repository"
Cohesion: 0.10
Nodes (4): WorkflowStage, IncidentNotFoundError, IncidentRepository, SQLiteDatabase

### Community 2 - "Agent Decision Flow"
Cohesion: 0.10
Nodes (8): LLMAdapter, AgentRuntime, DecisionTask, FinalDecision, ToolCallDecision, DecisionRequest, DecisionResponse, SREWebApp

### Community 3 - "Incident State Management"
Cohesion: 0.11
Nodes (5): StateManager, IncidentStatus, Incident, DuplicateEvidenceError, IncidentAlreadyExistsError

### Community 5 - "Tool Registry Execution"
Cohesion: 0.18
Nodes (5): ToolNotFoundError, ToolRegistry, ToolSpec, ToolCall, ToolResult

### Community 6 - "LLM Error Handling"
Cohesion: 0.28
Nodes (8): LLMAuthenticationError, LLMError, LLMOutputError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, OpenAICompatibleLLMAdapter, LLMSettings

### Community 11 - "Default Demo Tools"
Cohesion: 0.32
Nodes (3): build_default_registry(), DemoEchoInput, run_demo_echo()

## Knowledge Gaps
- **17 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SREWebApp` connect `Agent Decision Flow` to `LLM Adapter Runtime`, `Incident Repository`, `Incident State Management`, `LLM Error Handling`, `Conversation Entry Model`?**
  _High betweenness centrality (0.279) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `IncidentStatus`) actually correct?**
  _`IncidentRepository` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `LLM Adapter Runtime` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Why does `IncidentRepository` connect `Incident Repository` to `Incident State Management`, `Domain Models Module`, `Conversation Entry Model`, `Evidence Model`, `Status Transition Model`?**
  _High betweenness centrality (0.138) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `SREWebApp` (e.g. with `OpenAICompatibleLLMAdapter` and `StateManager`) actually correct?**
  _`SREWebApp` has 11 INFERRED edges - model-reasoned connections that need verification._
- **Should `Incident Repository` be split into smaller, more focused modules?**
  _Cohesion score 0.1032258064516129 - nodes in this community are weakly interconnected._
- **Why does `Incident` connect `Incident State Management` to `Incident Repository`, `Agent Decision Flow`, `Domain Models Module`, `Evidence Model`, `Status Transition Model`?**
  _High betweenness centrality (0.130) - this node is a cross-community bridge._