class LLMError(Exception):
    """模型调用错误基类。"""

class LLMTimeoutError(LLMError):
    """调用超时。"""

class LLMAuthenticationError(LLMError):
    """认证失败。"""


class LLMRateLimitError(LLMError):
    """服务限流。"""


class LLMProviderError(LLMError):
    """连接失败或其他服务端错误。"""


class LLMOutputError(LLMError):
    """响应无法解析或不符合 DecisionResponse。"""

    def __init__(self, message: str, *, raw_preview: str | None = None,
                 raw_tail: str | None = None, raw_length: int | None = None,
                 finish_reason: str | None = None,
                 error_summary: list[str] | None = None,
                 attempts: int = 1,) -> None :
        super().__init__(message)
        self.raw_preview = raw_preview
        self.raw_tail = raw_tail
        self.raw_length = raw_length
        self.finish_reason = finish_reason
        self.error_summary = error_summary or []
        self.attempts = attempts