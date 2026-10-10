from typing import Protocol

from sre_agent.models import AgentDecision
from sre_agent.request.decision_request import DecisionRequest

class LLMAdapter(Protocol):

    async def decide(self,request: DecisionRequest) -> AgentDecision:
        pass