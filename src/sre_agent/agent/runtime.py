from sre_agent.agent.llm_adapter import LLMAdapter
from sre_agent.agent.tool_registry import ToolRegistry
from sre_agent.models import FinalDecision
from sre_agent.request.decision_request import DecisionRequest


# AgentRuntime agent运行时

class AgentRuntime:
    def __init__(self,llm: LLMAdapter,registry: ToolRegistry,max_rounds:int = 5):
        self.llm = llm
        self.registry = registry
        self.max_rounds = max_rounds

    async def run(self,request: DecisionRequest,) -> FinalDecision:
        for round_number in range(self.max_rounds):
            decision = await self.llm.decide(request)

            if isinstance(decision, FinalDecision):
                return decision

            results = []

            for tool_call in decision.tool_calls:
                result = await self.registry.execute(tool_call)
                results.append(result)

            request = 更新上下文(request, decision, results)

    raise AgentRuntimeError("超过最大决策轮次")