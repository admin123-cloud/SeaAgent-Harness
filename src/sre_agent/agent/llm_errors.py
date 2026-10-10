class ToolNotFoundError(Exception):
    """工具不存在。"""

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