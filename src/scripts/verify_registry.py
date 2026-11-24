import asyncio
import sys
from typing import Any

from agent.runtime import AgentRuntime
from bootstrap import build_deps
from model.models import ToolCall
from tools.registry import ToolRegistry, ToolSpec, validate_tool_name


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def expect_raises(exc_type: type[BaseException], fn: Any, msg: str) -> BaseException:
    try:
        fn()
    except exc_type as exc:
        return exc
    except Exception as exc:
        raise AssertionError(f"{msg}（期望抛出 {exc_type.__name__}，实际抛出 {type(exc).__name__}: {exc}）") from exc
    raise AssertionError(f"{msg}（未抛出任何异常）")


async def _noop_handler(args: dict[str, Any]) -> dict[str, object]:
    return {"echo": args}


class _DummyLLM:
    async def decide(self, request: Any) -> Any:
        raise RuntimeError("离线测试不应触发真实模型调用")


def check_spec_and_naming() -> None:
    """断言 1–6：ToolSpec 校验、防御性拷贝、重名拒绝与 validate_tool_name 规则。"""
    deps = build_deps()
    # 1. 内置 read_skill 已注册，to_input_schema() 返回合法 JSON Schema 且做防御性拷贝
    read_skill_spec = deps.tool_registry.get("read_skill")
    schema_copy = read_skill_spec.to_input_schema()
    expect(isinstance(schema_copy, dict) and schema_copy.get("type") == "object", "read_skill schema 必须是 object dict")
    expect("load_ref" in (schema_copy.get("properties") or {}), "read_skill schema 缺少 load_ref 属性")
    schema_copy["properties"]["load_ref"]["description"] = "已被污染"
    expect(
        read_skill_spec.to_input_schema()["properties"]["load_ref"]["description"] != "已被污染",
        "to_input_schema() 必须做深拷贝，不能被外部修改污染注册表原件",
    )

    # 2. 重复注册同名工具抛 ValueError
    reg = ToolRegistry()
    spec_ok = ToolSpec(
        name="demo_tool",
        description="示例内置工具",
        input_schema={"type": "object", "properties": {"q": {"type": "string"}}},
        handler=_noop_handler,
        source="builtin",
    )
    reg.register(spec_ok)
    expect_raises(ValueError, lambda: reg.register(spec_ok), "重复注册同名工具必须抛出 ValueError")

    # 3. builtin 工具名含 __ 被 ValueError 拒绝
    expect_raises(
        ValueError,
        lambda: validate_tool_name("foo__bar", "builtin"),
        "builtin 工具名包含 '__' 必须被拒绝",
    )

    # 4. mcp 工具名格式非法或未知 source 被 ValueError 拒绝
    for bad_mcp in ("pods_list", "k8s__pods_get", "mcp__k8s_pods_get", "mcp__k8s__a__b", "mcp__k8s:pods_get"):
        expect_raises(
            ValueError,
            lambda n=bad_mcp: validate_tool_name(n, "mcp"),
            f"非法 MCP 工具名 {bad_mcp!r} 必须被拒绝",
        )
    expect_raises(
        ValueError,
        lambda: validate_tool_name("demo_tool", "unknown"),
        "未知 source 必须被 validate_tool_name 拒绝",
    )

    # 5. 超出 64 字符上限被 ValueError 拒绝
    expect_raises(
        ValueError,
        lambda: validate_tool_name("a" * 65, "builtin"),
        "超过 64 字符的 builtin 工具名必须被拒绝",
    )
    expect_raises(
        ValueError,
        lambda: validate_tool_name("mcp__k8s__" + "a" * 55, "mcp"),
        "超过 64 字符的 mcp 工具名必须被拒绝",
    )

    # 6. 非法 input_schema 或 timeout_seconds 构造 ToolSpec 必须抛 ValueError
    for bad_schema in (None, "not_a_dict", {"type": "string"}):
        expect_raises(
            ValueError,
            lambda s=bad_schema: ToolSpec(
                name="bad_schema_tool",
                description="bad",
                input_schema=s,  # type: ignore[arg-type]
                handler=_noop_handler,
            ),
            f"非法 input_schema={bad_schema!r} 应抛出 ValueError",
        )
    expect_raises(
        ValueError,
        lambda: ToolSpec(
            name="bad_timeout_tool",
            description="bad",
            input_schema={"type": "object"},
            handler=_noop_handler,
            timeout_seconds=0,
        ),
        "timeout_seconds <= 0 应抛出 ValueError",
    )


async def check_execution_and_runtime() -> None:
    """断言 7–9：MCP 工具注册与执行、入参校验、未注册工具错误处理、Runtime _available_tools 集成。"""
    reg = ToolRegistry()
    mcp_spec = ToolSpec(
        name="mcp__k8s__pods_list_in_namespace",
        description="列出指定 namespace 下的 Pod",
        input_schema={
            "type": "object",
            "required": ["namespace"],
            "properties": {
                "namespace": {"type": "string"},
                "limit": {"type": "integer"},
            },
        },
        handler=_noop_handler,
        source="mcp",
    )
    reg.register(mcp_spec)

    # 7a. MCP 工具合法入参可执行成功
    res_ok = await reg.execute(
        ToolCall(
            call_id="c-1",
            tool_name="mcp__k8s__pods_list_in_namespace",
            arguments={"namespace": "sre-drill", "limit": 10},
        )
    )
    expect(res_ok.success and res_ok.data["echo"]["namespace"] == "sre-drill", "MCP 工具合法调用应执行成功")

    # 7b. 缺必填键或 bool 伪装 integer 应拦截为 validation_error
    for bad_args in ({}, {"namespace": "sre-drill", "limit": True}, {"namespace": 123}):
        res_bad = await reg.execute(
            ToolCall(
                call_id="c-bad",
                tool_name="mcp__k8s__pods_list_in_namespace",
                arguments=bad_args,
            )
        )
        expect(
            not res_bad.success and res_bad.error_type == "validation_error",
            f"非法入参 {bad_args!r} 应返回 validation_error，实际为 {res_bad!r}",
        )

    # 8. 未注册工具名返回 tool_not_found_error
    res_missing = await reg.execute(
        ToolCall(call_id="c-404", tool_name="mcp__k8s__not_exists", arguments={})
    )
    expect(
        not res_missing.success and res_missing.error_type == "tool_not_found_error",
        f"未注册工具应返回 tool_not_found_error，实际为 {res_missing!r}",
    )

    # 9. AgentRuntime._available_tools() 同时导出 builtin 与 mcp，且 input_schema 为 dict（非未调用方法）
    deps = build_deps()
    deps.tool_registry.register(mcp_spec)
    runtime = AgentRuntime(
        llm=_DummyLLM(),  # type: ignore[arg-type]
        tool_registry=deps.tool_registry,
        skill_registry=deps.skill_registry,
    )
    available = runtime._available_tools()
    by_name = {item["name"]: item for item in available}
    expect("read_skill" in by_name and "mcp__k8s__pods_list_in_namespace" in by_name, "_available_tools 应同时包含 builtin 与 mcp 工具")
    for tool_name, item in by_name.items():
        expect(isinstance(item["input_schema"], dict), f"{tool_name} 的 input_schema 必须是 dict，实际是 {type(item['input_schema']).__name__}")


def main() -> int:
    check_spec_and_naming()
    asyncio.run(check_execution_and_runtime())
    print("[PASS] verify_registry 全部 9 项离线断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
