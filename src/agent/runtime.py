from collections.abc import Callable

from agent.llm_adapter import LLMAdapter
from tools.registry import ToolRegistry
from model.enums import PermissionMode
from model.models import FinalDecision, ToolCallDecision, ToolResult
from model.request import DecisionRequest
from model.errors import AgentRuntimeError
from skills import SkillToolkit


# AgentRuntime agent运行时

RuntimeEventSink = Callable[[str,dict[str,object]], None]

class AgentRuntime:
    def __init__(
            self,
            llm: LLMAdapter,
            # tool注册
            tool_registry: ToolRegistry,
            # skill注册
            skill_toolkit: SkillToolkit,

            max_rounds:int = 5,
            event_sink : RuntimeEventSink | None = None,
            permission_mode: PermissionMode = PermissionMode.REQUEST_APPROVAL,
    ):

        if max_rounds < 1:
            raise ValueError("max_rounds 必须大于 0")
        self.llm = llm
        self.registry = tool_registry
        self.skill_toolkit = skill_toolkit
        self.max_rounds = max_rounds
        self.event_sink  = event_sink
        # 会话级权限模式；真正的审批/放行逻辑由后续 PermissionPolicy 接入。
        self.permission_mode = permission_mode

    def _emit(self,event_type: str,data: dict[str, object]) -> None:
        if self.event_sink is not None:
            self.event_sink(event_type, data)

    def _available_tools(self) -> list[dict[str,object]]:
        return [
            {
                "name":spec.name,
                "description":spec.description,
                "input_schema": spec.input_model.model_json_schema(),
                "required_permissions": sorted(spec.required_permissions),
                "risk_level": spec.risk_level
            }
            for spec in self.registry.list_specs()
        ]

    # 注入  available_tools / available_skills / agent_history=[]
    def _prepare_request(self, request:DecisionRequest) -> DecisionRequest:
        context = dict(request.context)
        context.setdefault("available_tools", self._available_tools())
        context.setdefault("agent_history", [])

        if "available_skills" not in context:
            available_skills = []
            for skill in self.skill_toolkit.catalog():
                skill_data = skill.model_dump(mode="json")
                available_skills.append(skill_data)
            context["available_skills"] = available_skills

        return request.model_copy(
            update={"context": context}
        )

    def _append_tool_round(self,request: DecisionRequest,round_number: int,decision: ToolCallDecision,
                           results: list[ToolResult]) -> DecisionRequest:
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
        # R1.调用模型前准备参数
        current_request = self._prepare_request(request)

        for round_number in range(1,self.max_rounds+1):
            decision = await self.llm.decide(current_request)

            if isinstance(decision, FinalDecision):
                return decision

            if not isinstance(decision, ToolCallDecision):
                raise AgentRuntimeError(f"不支持的决策类型{type(decision).__name__}")

            # R2 调用工具逻辑 & 工具调用前
            results: list[ToolResult] = []
            self._emit(
                "tool_call",
                {
                    "round": round_number,
                    "permission_mode": self.permission_mode.value,
                    "tool_calls": decision.model_dump(mode="json")["tool_calls"],
                },
            )
            # R3.工具调用
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
