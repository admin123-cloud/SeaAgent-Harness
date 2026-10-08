from typing import Protocol

from sre_agent.request.decision_request import DecisionRequest
from sre_agent.response.decision_response import DecisionResponse


class LLMAdapter(Protocol):
    async def decide(
            self,
            request: DecisionRequest,
    ) -> DecisionResponse:
        pass