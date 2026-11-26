
class ToolNotFoundError(Exception):
    """工具不存在。"""

class ToolInputValidationError(Exception):
    """ 工具输入校验失败 """

class MCPConnectionError(Exception):
    """ MCP服务连接失败 """

class MCPInvocationError(Exception):
    """ MCP服务调用失败 """