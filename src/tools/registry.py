import asyncio
from dataclasses import dataclass
from collections.abc import Awaitable, Callable
from time import perf_counter
from typing import Any

from pydantic import BaseModel, ValidationError

from model.errors import ToolNotFoundError
from model.models import ToolCall, ToolResult


# ToolHandler 是一个类型别名，用来说明 Handler 函数应该长什么样。
ToolHandler = Callable[
    # 函数接收一个参数
    [Any],
    # 函数是异步的，最终返回 dict
    Awaitable[dict[str, object]],
]

# @dataclass 自动生成构造函数
@dataclass(frozen=True)
class ToolSpec:
    """工具元数据与执行入口。"""
    # 工具注册名，例如 read_skill
    name: str
    # 提供给模型看的工具说明
    description: str
    # 工具参数的 Pydantic 模型 ?
    input_model: type[BaseModel]
    # 真正执行工具的函数
    handler: ToolHandler
    # 权限能力标识，例如 k8s.pods.read；当前仅记录元数据，尚未拦截执行。
    required_permissions: frozenset[str] = frozenset()
    # 风险等级仅用于说明、审批提示和审计，不作为授权依据。
    risk_level: str = "low"
    # 单次执行超时时间
    timeout_seconds: float = 5.0


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
            # step3 校验参数
            arguments  = toolspec.input_model.model_validate(tool_call.arguments)

            # step4 执行工具调用
            data = await asyncio.wait_for(
                toolspec.handler(arguments),
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
        except ValidationError:
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