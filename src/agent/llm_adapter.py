from typing import Protocol

from model.models import AgentDecision
from model.request import DecisionRequest

class LLMAdapter(Protocol):

    async def decide(self,request: DecisionRequest) -> AgentDecision:
        pass