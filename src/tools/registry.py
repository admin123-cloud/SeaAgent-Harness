import copy,re
import asyncio
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any
from typing import Literal
from pydantic import ValidationError

from model.errors import ToolNotFoundError,ToolInputValidationError,validate_arguments_by_schema
from model.models import ToolCall, ToolResult


# ToolHandler 是一个类型别名，用来说明 Handler 函数应该长什么样。
ToolHandler = Callable[
    # 函数接收一个参数
    [Any],
    # 函数是异步的，最终返回 dict
    Awaitable[dict[str, object]],
]
# claude code风格的mcp name
MCP_TOOL_NAME_RE = re.compile(
    r"^(?=.{1,64}$)mcp__[a-z][a-z0-9-]*(?:_[a-z0-9-]+)*__[a-zA-Z0-9][a-zA-Z0-9-]*(?:_[a-zA-Z0-9-]+)*$"
)
# 每一段（server / tool 名）自身的规则
# server 段：小写字母开头，仅 a-z0-9-
_MCP_SERVER_SEGMENT_RE = re.compile(r"^[a-z][a-z0-9-]*$")
# tool 段：字母数字开头，仅 a-zA-Z0-9-
_MCP_TOOL_SEGMENT_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9-]*$")
# 内置工具name
BUILTIN_TOOL_NAME_RE = re.compile(
    r"^(?=.{1,64}$)[a-z][a-z0-9]*(?:_[a-z0-9]+)*$"
)

def validate_tool_name(name: str, source: str) -> None:
    """
    参考claude code 的工具定义规则
    name   正则 ^[a-zA-Z0-9_-]{1,128}$
    source buildin 或 mcp
    """
    if not isinstance(name, str) or not name:
        raise ValueError(f"tool name must be a non-empty str, got {name!r}")
    if len(name) > 64:
        raise ValueError(f"tool name{name} at most 64 characters")
    if source == "builtin":
        if not BUILTIN_TOOL_NAME_RE.fullmatch(name):
            raise ValueError(
                f"builtin tool name {name!r} must match {BUILTIN_TOOL_NAME_RE.pattern}"
            )
        if "__" in name:
            raise ValueError(f"builtin tool name {name!r} can not contain __")
    elif source == "mcp":
        # 必须以 mcp__ 开头
        prefix = "mcp__"
        if not name.startswith(prefix):
            raise ValueError(f"mcp tool name {name!r} must start with {prefix!r}")
            # 去掉前缀后，必须恰好有 2 段（用 __ 分隔）
        rest = name[len(prefix):]
        parts = rest.split("__")
        if len(parts) != 2:
            raise ValueError(
                f"mcp tool name {name!r} must contain exactly 2 '__'-separated segments "
                f"after 'mcp__', got {len(parts)}: {parts!r}"
            )
        server, tool = parts

        if not server or not _MCP_SERVER_SEGMENT_RE.fullmatch(server):
            raise ValueError(
                f"mcp server segment {server!r} in {name!r} must match "
                f"{_MCP_SERVER_SEGMENT_RE.pattern}"
            )
        if not tool or not _MCP_TOOL_SEGMENT_RE.fullmatch(tool):
            raise ValueError(
                f"mcp tool segment {tool!r} in {name!r} must match "
                f"{_MCP_TOOL_SEGMENT_RE.pattern}"
            )
        if not MCP_TOOL_NAME_RE.fullmatch(name):
            raise ValueError(f"mcp tool name {name!r} must match {MCP_TOOL_NAME_RE.pattern}")

def check_input_schema(tool_call:ToolCall):
    if not isinstance(tool_call.arguments, dict):
        raise ToolInputValidationError()


# @dataclass 自动生成构造函数
@dataclass(frozen=True)
class ToolSpec:
    """工具元数据与执行入口。"""
    # 工具注册名，例如 read_skill
    name: str
    # 提供给模型看的工具说明
    description: str
    # 工具参数的json体
    input_schema: dict[str, Any]
    # 可选参数 参数示例
    #input_example: dict[str, Any] | None = None

    # 真正执行工具的函数
    handler: ToolHandler
    # 权限能力标识，例如 k8s.pods.read；当前仅记录元数据，尚未拦截执行。
    required_permissions: frozenset[str] = frozenset()
    # 工具来源  默认内置工具  可以使mcp工具
    source: Literal["builtin", "mcp"] = "builtin"
    # 风险等级仅用于说明、审批提示和审计，不作为授权依据。
    risk_level: str = "low"
    # 单次执行超时时间
    timeout_seconds: float = 5.0

    """ 检查input_schema 是dict json 且非空"""
    def __post_init__(self):
        validate_tool_name(self.name, self.source)
        if self.source not in ("builtin", "mcp"):
            raise ValueError(f"source {self.source!r} must be one of 'builtin', 'mcp'")
        if self.timeout_seconds <= 0:
            raise ValueError(f"timeout_seconds {self.timeout_seconds!r} must be > 0")
        if self.input_schema is None:
            raise ValueError("input_schema must be defined")
        if self.input_schema.get("type") is not "object":
            raise ValueError("input_schema type must be object")
        if not isinstance(self.input_schema, dict):
            raise ValueError(f"input_schema{self.input_schema} must be dict")
        object.__setattr__(self, "input_schema", copy.deepcopy(self.input_schema))

    def to_input_schema(self):
        return copy.deepcopy(self.input_schema)

class ToolRegistry:
    """
    工具注册和执行
        规则：
            - 禁止重复注册同名工具；
            - 查询不存在的工具时返回明确错误；
            - 执行前先校验工具参数；
            - 执行必须有超时；
            - 工具异常不能直接打穿 Agent Runtime；
            - 最终统一转换成 ToolResult。
    """
    def __init__(self):
        self._specs : dict[str, ToolSpec] = {}

    def register(self,spec:ToolSpec) -> None:
        validate_tool_name(spec.name, spec.source)
        if spec.name in self._specs:
            raise ValueError(f"Tool {spec.name} already registered")
        self._specs[spec.name] = spec

    def get(self,name:str) -> ToolSpec:
        if name in self._specs:
            return self._specs[name]
        raise ToolNotFoundError(f"Tool {name} not registered yet")

    def list_specs(self) -> list[ToolSpec]:
        return list(self._specs.values())


    async def execute(self,tool_call:ToolCall)-> ToolResult:
        # step1 启动耗时
        started = perf_counter()
        try:
            # step2 查询工具
            toolspec = self.get(tool_call.tool_name)
            # step3 校验参数辅助函数（检查isinstance(tool_call.arguments, dict)、required必填键存在、基础类型匹配）；
            validate_arguments_by_schema(tool_call.arguments, toolspec.input_schema)
            # step4 执行工具调用
            data = await asyncio.wait_for(
                toolspec.handler(tool_call.arguments),
                timeout=toolspec.timeout_seconds
            )

            return ToolResult(
                call_id = tool_call.call_id,
                tool_name = tool_call.tool_name,
                data = data,
                elapsed_ms = int((perf_counter() - started) * 1000),
                success=True,
                summary = "工具执行成功"
            )
        except ToolNotFoundError:
            return self._failure_result(
                tool_call,
                started,
                "工具未注册",
                "tool_not_found_error",
            )
        except ToolInputValidationError,ValidationError:
            """ 工具入参校验失败 应该转大模型"""
            return self._failure_result(
                tool_call,
                started,
                "参数校验失败",
                "validation_error",
            )
        except asyncio.TimeoutError:
            return self._failure_result(
                tool_call,
                started,
                "工具调用超时",
                "timeout",
            )
        except Exception as exc:
            return self._failure_result(
                tool_call,
                started,
                f"处理异常: {exc}",
                "handler_error",
            )

    @staticmethod
    def _failure_result(
            tool_call: ToolCall,
            started: float,
            summary: str,
            error_type: str,
    ) -> ToolResult:
        return ToolResult(
            call_id=tool_call.call_id,
            tool_name=tool_call.tool_name,
            success=False,
            summary=summary,
            data={},
            error_type=error_type,
            elapsed_ms=int((perf_counter() - started) * 1000),
        )