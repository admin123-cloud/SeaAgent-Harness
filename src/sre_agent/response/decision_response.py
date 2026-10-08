from pydantic import BaseModel, Field,field_validator
""" 决策契约响应体 """

class DecisionResponse(BaseModel):
    summary: str = Field(min_length=1)
    findings: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float| None = Field(default=None,ge=0.0 ,le=1.0)
    recommendations: list[str] = Field(default_factory=list)

    @field_validator("summary")
    @classmethod
    def summary_must_not_be_blank(cls,value:str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("summary 不能为空")
        return value

