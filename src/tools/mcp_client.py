from contextlib import AsyncExitStack
from dataclasses import dataclass
import os, json,hashlib
from typing import Any
from pathlib import Path

from anyio import ClosedResourceError
from mcp_types import CallToolResult

from .registry import ToolHandler
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from model.errors import MCPConnectionError, MCPInvocationError
from tools.registry import ToolSpec

_ALLOWED_ENV_KEYS = ("PATH", "SYSTEMROOT", "WINDIR")


@dataclass(frozen=True)
class MCPServerConfig:
    server_name: str       # 例如 "k8s" -> 生成 mcp__k8s__<tool>
    command: str           # EXE 路径
    args: tuple[str, ...]  # ("--config", toml_path)
    kubeconfig: Path

def _call_result_to_dict(result:CallToolResult) -> dict[str, object]:
    return {"structured_content": result.structured_content, "content": [getattr(item, "text", str(item)) for item in result.content]}

class MCPStdioAdapter:

    def __init__(self, config: MCPServerConfig) -> None:
        self._config = config
        self._stack = AsyncExitStack()
        self._session: ClientSession | None = None

    def _get_stdio_env(self) -> StdioServerParameters:
        # t1 构建安全环境信息
        safe_env = {
            k: os.environ[k]
            for k in _ALLOWED_ENV_KEYS
            if k in os.environ
        }

        safe_env["KUBECONFIG"] = str(self._config.kubeconfig)

        return StdioServerParameters(
            command=str(self._config.command),
            args=[*self._config.args],
            env=safe_env,
        )

    async def connect(self) -> None:
        # T1 防止重复 connect
        if self._session is None:
            params =self._get_stdio_env()
            try:
                r, w = await self._stack.enter_async_context(stdio_client(params))
                session = await self._stack.enter_async_context(ClientSession(r, w))
                await session.initialize()
                self._session = session
            except MCPConnectionError as ex:
                await self.close()
                raise MCPConnectionError(f"MCP网络连接失败") from ex
            except MCPInvocationError as ex:
                await self.close()
                raise MCPInvocationError(f"MCP调用失败") from ex

    async def list_tool_specs(self) -> list[ToolSpec]:
        if self._session is None:
            raise MCPConnectionError("MCP 服务调用异常，连接可能已中断")
        # 由于_session not None 或 initialize_result 无法判断连接是否正常 干脆在调用中处理
        try:
            cmp_tools = []
            tools = (await self._session.list_tools()).tools
            for tool in tools:
                schema = dict(tool.input_schema or {"type": "object", "properties": {}})
                schema.setdefault("type", "object")  # 写进正式代码里真正执行：缺 "type" 时自动补为 "object"
                tool_spec = ToolSpec(
                    name= f"mcp__{self._config.server_name}__{tool.name}",
                    description=tool.description or "",
                    # 确保 schema.setdefault("type", "object")
                    input_schema= dict(tool.input_schema or {"type": "object", "properties": {}}),
                    source="mcp",
                    handler= self._make_tool_handel(tool.name)
                )
                cmp_tools.append(tool_spec)
            return cmp_tools
        except Exception as exc:
            await self.close()
            raise MCPConnectionError("MCP 服务连接或初始化失败") from exc


    # what is 闭包函数？
    def _make_tool_handel(self,raw_name:str) -> ToolHandler:
        # 注意：必须单独拆成方法！如果在 for tool in tools 里直接 def handler(raw_args): 用外层循环变量 tool.name，
        # Python 的“闭包延迟绑定”会导致 4 个工具最终全去调最后一个工具！
        async def _invoke(raw_args: dict[str, Any]) -> dict[str, object]:
            if self._session is None:
                raise MCPConnectionError("MCP 服务尚未连接或连接已中断")
            try:
                result = await self._session.call_tool(name=raw_name, arguments=raw_args)
            except Exception as exc:
                # 注意：单次工具参数错误也可能导致 MCPError，不必每次报错都杀掉整个子进程；
                # 如需区分断连再在后续版本针对 ClosedResourceError / BrokenPipeError 触发 close()
                if isinstance(exc, ClosedResourceError):
                    await self.close()
                raise MCPInvocationError("MCP 工具调用失败") from exc
            if result.is_error:
                # 固定安全文案：绝不把 result.content 原文直接拼进异常（可能含 SA/内网路径）
                raise MCPInvocationError("MCP 工具执行返回错误")

            return _call_result_to_dict(result)

        return _invoke

    async def handler(self,name:str,arguments:dict) -> dict[str, object] :
        result = await self._session.call_tool(name = name,arguments=arguments)
        if result.is_error:
            raise MCPInvocationError()
        return _call_result_to_dict(result)


    async def close(self) -> None:
        await self._stack.aclose()
        self._session = None