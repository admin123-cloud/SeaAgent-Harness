# Graph Report - src  (2026-10-19)

## Corpus Check
- 50 files · ~14,640 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 1 file(s) not represented in the graph (top: (none) 1)

## Summary
- 481 nodes · 904 edges · 27 communities (13 shown, 14 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 97 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a0ad194d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `python scripts/graphify_project.py update` after code changes (no API cost).

## Community Hubs (Navigation)
- database/sqlite_database.py
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

## Communities (27 total, 14 thin omitted)

### Community 0 - "database/sqlite_database.py"
Cohesion: 0.12
Nodes (3): read_package_file(), require_match(), SQLiteDatabase

### Community 1 - "IncidentRepository"
Cohesion: 0.08
Nodes (10): StateManager, IncidentStatus, WorkflowStage, Evidence, Incident, StatusTransition, DuplicateEvidenceError, IncidentNotFoundError (+2 more)

### Community 2 - "SREWebApp"
Cohesion: 0.08
Nodes (8): ConversationEntry, utc_now(), ConversationEntry, FinalDecision, ToolCallDecision, DecisionResponse, main(), SREWebApp

### Community 3 - "Humanizer: remove AI writing patterns"
Cohesion: 0.05
Nodes (39): 10. Hyphenated pairs everywhere, 11. Passive voice and missing subjects, 12. Overused AI words, 13. Inflated significance, 14. Vague connection or association, 15. Shallow -ing riders, 16. Sales language, 17. Borrowed authority (+31 more)

### Community 5 - "pydantic"
Cohesion: 0.06
Nodes (18): LLMAdapter, ToolNotFoundError, ToolRegistry, ToolSpec, demo_tool(), FinalDecision, ToolCallDecision, ToolCall (+10 more)

### Community 6 - "LLM Error Handling"
Cohesion: 0.19
Nodes (8): LLMAuthenticationError, LLMError, LLMOutputError, LLMProviderError, LLMRateLimitError, LLMTimeoutError, OpenAICompatibleLLMAdapter, LLMSettings

### Community 7 - "Incident"
Cohesion: 0.05
Nodes (14): DuplicateEvidenceError, IncidentAlreadyExistsError, IncidentNotFoundError, IncidentRepository, IncidentStatusConflictError, SQLiteDatabase, IncidentStatus, WorkflowStage (+6 more)

### Community 8 - "Changelog"
Cohesion: 0.07
Nodes (28): 1.0.0, 2.0.0, 2.10.0, 2.10.1, 2.10.2, 2.11.0, 2.11.1, 2.11.2 (+20 more)

### Community 9 - "AgentRuntime"
Cohesion: 0.12
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

- **Why does `SREWebApp` connect `SREWebApp` to `IncidentRepository`, `web_app.py`, `pydantic`, `LLM Error Handling`, `Incident`, `AgentRuntime`?**
  _High betweenness centrality (0.063) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `SQLiteDatabase`) actually correct?**
  _`IncidentRepository` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Should `database/sqlite_database.py` be split into smaller, more focused modules?**
  _Cohesion score 0.11904761904761904 - nodes in this community are weakly interconnected._
- **Why does `StateManager` connect `IncidentRepository` to `SREWebApp`, `web_app.py`, `Incident`?**
  _High betweenness centrality (0.052) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `IncidentRepository` (e.g. with `StateManager` and `IncidentStatus`) actually correct?**
  _`IncidentRepository` has 9 INFERRED edges - model-reasoned connections that need verification._
- **Should `IncidentRepository` be split into smaller, more focused modules?**
  _Cohesion score 0.08140610545790934 - nodes in this community are weakly interconnected._
- **Why does `IncidentRepository` connect `IncidentRepository` to `database/sqlite_database.py`, `SREWebApp`, `web_app.py`, `Incident`?**
  _High betweenness centrality (0.043) - this node is a cross-community bridge._