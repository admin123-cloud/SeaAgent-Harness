# Graph Report - src  (2026-10-16)

## Corpus Check
- 50 files · ~14,626 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1 file(s) not represented in the graph (top: (none) 1)

## Summary
- 480 nodes · 890 edges · 28 communities (14 shown, 14 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 99 edges (avg confidence: 0.91)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9d52f135`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `python scripts/graphify_project.py update` after code changes (no API cost).

## Community Hubs (Navigation)
- IncidentRepository
- IncidentRepository
- SREWebApp
- Humanizer: remove AI writing patterns
- web_app.py
- pydantic
- LLM Error Handling
- Incident
- Changelog
- AgentRuntime
- HTTP Request Handler
- Humanizer
- Kubernetes Observation Model
- plugin.json
- marketplace.json
- Guide for agents
- SQLiteDatabase
- model/models/kubernetes_observation.py

## God Nodes (most connected - your core abstractions)
1. `IncidentRepository` - 28 edges
2. `Changelog` - 28 edges
3. `IncidentRepository` - 27 edges
4. `SREWebApp` - 24 edges
5. `Incident` - 20 edges
6. `Incident` - 19 edges
7. `StateManager` - 18 edges
8. `Evidence` - 17 edges
9. `ConversationEntry` - 16 edges
10. `StatusTransition` - 16 edges

## Surprising Connections (you probably didn't know these)
- `LLMAdapter` --uses--> `DecisionRequest`  [INFERRED]
  src/agent/llm_adapter.py → request/decision_request.py
- `OpenAICompatibleLLMAdapter` --uses--> `DecisionRequest`  [INFERRED]
  src/agent/openai_compatible_llm_adapter.py → request/decision_request.py
- `SREWebApp` --uses--> `DecisionTask`  [INFERRED]
  src/web_app.py → enums/decision_task.py
- `SREWebApp` --uses--> `IncidentStatus`  [INFERRED]
  src/web_app.py → enums/incident_status.py
- `SREWebApp` --uses--> `Incident`  [INFERRED]
  src/web_app.py → models/incident.py

## Import Cycles
- None detected.

## Communities (28 total, 14 thin omitted)

### Community 0 - "IncidentRepository"
Cohesion: 0.07
Nodes (9): DuplicateEvidenceError, IncidentAlreadyExistsError, IncidentNotFoundError, IncidentRepository, IncidentStatusConflictError, SQLiteDatabase, WorkflowStage, read_package_file() (+1 more)

### Community 1 - "IncidentRepository"
Cohesion: 0.08
Nodes (9): StateManager, IncidentStatus, WorkflowStage, Evidence, Incident, StatusTransition, DuplicateEvidenceError, IncidentNotFoundError (+1 more)

### Community 2 - "SREWebApp"
Cohesion: 0.08
Nodes (7): ConversationEntry, utc_now(), ConversationEntry, FinalDecision, ToolCallDecision, DecisionResponse, SREWebApp

### Community 3 - "Humanizer: remove AI writing patterns"
Cohesion: 0.05
Nodes (39): 10. Hyphenated pairs everywhere, 11. Passive voice and missing subjects, 12. Overused AI words, 13. Inflated significance, 14. Vague connection or association, 15. Shallow -ing riders, 16. Sales language, 17. Borrowed authority (+31 more)

### Community 4 - "web_app.py"
Cohesion: 0.08
Nodes (3): IncidentAlreadyExistsError, IncidentStatusConflictError, main()

### Community 5 - "pydantic"
Cohesion: 0.06
Nodes (18): LLMAdapter, ToolNotFoundError, ToolRegistry, ToolSpec, demo_tool(), FinalDecision, ToolCallDecision, ToolCall (+10 more)

### Community 6 - "LLM Error Handling"
Cohesion: 0.24
Nodes (8): LLMAuthenticationError, LLMError, LLMOutputError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, OpenAICompatibleLLMAdapter, LLMSettings

### Community 7 - "Incident"
Cohesion: 0.08
Nodes (7): IncidentStatus, Evidence, utc_now(), Incident, utc_now(), StatusTransition, utc_now()

### Community 8 - "Changelog"
Cohesion: 0.07
Nodes (28): 1.0.0, 2.0.0, 2.10.0, 2.10.1, 2.10.2, 2.11.0, 2.11.1, 2.11.2 (+20 more)

### Community 9 - "AgentRuntime"
Cohesion: 0.11
Nodes (7): AgentRuntime, AgentRuntimeError, DecisionTask, DecisionTask, PermissionMode, DecisionRequest, DecisionRequest

### Community 11 - "Humanizer"
Cohesion: 0.09
Nodes (21): A. Staging instead of stating, B. Rhythm by rule, C. Inflation and borrowed authority, Claude.ai and Claude Desktop, Claude Code, Codex, D. Formatting by rule, E. Leftovers from the chat and the draft (+13 more)

### Community 13 - "plugin.json"
Cohesion: 0.15
Nodes (12): author, name, url, description, homepage, keywords, license, name (+4 more)

### Community 15 - "marketplace.json"
Cohesion: 0.25
Nodes (7): description, name, owner, name, url, plugins, $schema

### Community 23 - "Guide for agents"
Cohesion: 0.29
Nodes (6): Editing the skill, Guide for agents, Key files, Rules for changes, What this repo contains, Writing style

## Knowledge Gaps
- **14 thin communities (<3 nodes) omitted from report** — run `python scripts/graphify_project.py query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SREWebApp` connect `SREWebApp` to `IncidentRepository`, `IncidentRepository`, `web_app.py`, `pydantic`, `LLM Error Handling`, `AgentRuntime`?**
  _High betweenness centrality (0.064) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `SQLiteDatabase`) actually correct?**
  _`IncidentRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `IncidentRepository` be split into smaller, more focused modules?**
  _Cohesion score 0.06857142857142857 - nodes in this community are weakly interconnected._
- **Why does `StateManager` connect `IncidentRepository` to `IncidentRepository`, `SREWebApp`, `web_app.py`, `Incident`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `IncidentStatus`) actually correct?**
  _`IncidentRepository` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `IncidentRepository` be split into smaller, more focused modules?**
  _Cohesion score 0.08405797101449275 - nodes in this community are weakly interconnected._
- **Why does `IncidentRepository` connect `IncidentRepository` to `IncidentRepository`, `SREWebApp`, `web_app.py`, `Incident`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._