from collections.abc import Callable

from sre_agent.agent.llm_adapter import LLMAdapter
from sre_agent.agent.tool_registry import ToolRegistry
from sre_agent.models import FinalDecision, ToolCallDecision, ToolResult
from sre_agent.request.decision_request import DecisionRequest


class AgentRuntimeError(RuntimeError):
    """Agent Runtime 执行失败。"""

# AgentRuntime agent运行时

RuntimeEventSink = Callable[[str,dict[str,object]], None]

class AgentRuntime:
    def __init__(
            self,
            llm: LLMAdapter,
            registry: ToolRegistry,
            max_rounds:int = 5,
            event_sink : RuntimeEventSink | None = None,
    ):

        if max_rounds < 1:
            raise ValueError("max_rounds 必须大于 0")
        self.llm = llm
        self.registry = registry
        self.max_rounds = max_rounds
        self.event_sink  = event_sink

    def _emit(self,event_type: str,data: dict[str, object]) -> None:
        if self.event_sink is not None:
            self.event_sink(event_type, data)

    def _available_tools(self) -> list[dict[str,object]]:
        return [
            {
                "name":spec.name,
                "description":spec.description,
                "input_schema": spec.input_model.model_json_schema(),
                "readonly":spec.readonly,
                "risk_level": spec.risk_level
            }
            for spec in self.registry.list_specs()
        ]

    def _prepare_request(self, request:DecisionRequest) -> DecisionRequest:
        context = dict(request.context)
        context.setdefault("available_tools", self._available_tools())
        context.setdefault("agent_history", [])

        return request.model_copy(
            update={"context": context}
        )

    def _append_tool_round(
            self,
            request: DecisionRequest,
            round_number: int,
            decision: ToolCallDecision,
            results: list[ToolResult],
    ) -> DecisionRequest:
        context = dict(request.context)
        history = list(context.get("agent_history", []))

        history.extend(
            [
                {
                    "round": round_number,
                    "kind":"tool_call",
                    "tool_calls":decision.model_dump(mode="json")["tool_calls"],
                },
                {
                    "round": round_number,
                    "kind": "tool_result",
                    "results": [
                        result.model_dump(mode="json")
                        for result in results
                    ],
                }
            ]
        )

        context["agent_history"] = history

        return request.model_copy(
            update={"context": context}
        )

    async def run(self,request: DecisionRequest,) -> FinalDecision:
        current_request = self._prepare_request(request)

        for round_number in range(1,self.max_rounds+1):
            decision = await self.llm.decide(current_request)

            if isinstance(decision, FinalDecision):
                return decision

            if not isinstance(decision, ToolCallDecision):
                raise AgentRuntimeError(f"不支持的决策类型{type(decision).__name__}")


            results: list[ToolResult] = []
            # 工具调用前  生成触发事件类型 ToolCalling
            self._emit(
                "tool_call",
                {
                    "round": round_number,
                    "tool_calls": decision.model_dump(mode="json")["tool_calls"],
                },
            )
            for tool_call in decision.tool_calls:
                result = await self.registry.execute(tool_call)
                results.append(result)
            # 工具调用后  生成触发事件类型 ToolCallingResult
            self._emit(
                "tool_result",
                {
                    "round": round_number,
                    "results": [
                        result.model_dump(mode="json")
                        for result in results
                    ],
                },
            )

            current_request = self._append_tool_round(current_request, round_number,decision, results)

        raise AgentRuntimeError(f"超过最大决策轮次{self.max_rounds}")