from pydantic import BaseModel, Field
from typing import Annotated, Literal

from sre_agent.models.tool_call import ToolCall
from sre_agent.response.decision_response import DecisionResponse


# 决策 调用工具
class ToolCallDecision(BaseModel):
    kind: Literal["tool_call"] = "tool_call"
    tool_calls: list[ToolCall] = Field(min_length=1)

# 最终结论
class FinalDecision(BaseModel):
    kind: Literal["final"] = "final"
    response: DecisionResponse

# 联合类型
AgentDecision = Annotated[
    ToolCallDecision | FinalDecision,
    Field(discriminator="kind"),
]