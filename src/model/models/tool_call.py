from pydantic import BaseModel, Field,field_validator


class ToolCall(BaseModel):
    """ 模型请求调用外部工具 的总称"""

    # 调用id
    call_id: str = Field(min_length =1)
    # 调用工具名称
    tool_name : str = Field(min_length=1)
    # 调用工具参数
    arguments: dict[str,object] = Field(default_factory=dict)

    @field_validator("call_id","tool_name")
    @classmethod
    def require_non_blank(cls,value:str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

class ToolResult(BaseModel):
    """ 工具调用结果 """
    # 调用id
    call_id: str = Field(min_length=1)
    # 工具名称
    tool_name: str = Field(min_length=1)
    # 是否成功
    success: bool
    # 调用总结
    summary:str = Field(min_length=1)
    # 数据
    data:dict[str,object] = Field(default_factory=dict)

    # 失败类型
    error_type: str | None = None
    # 调用耗时
    elapsed_ms: int = Field(ge=0)

    @field_validator("call_id","tool_name","summary")
    @classmethod
    def require_non_blank(cls,value:str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("不能为空")
        return value

