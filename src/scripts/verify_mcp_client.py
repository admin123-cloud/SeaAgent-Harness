import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from anyio import ClosedResourceError
from mcp.types import CallToolResult, TextContent

from agent.runtime import AgentRuntime
from bootstrap import build_deps
from model.errors import MCPConnectionError, MCPInvocationError
from model.models import ToolCall
from tools.mcp_client import MCPServerConfig, MCPStdioAdapter


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


async def expect_raises_async(exc_type: type[BaseException], coro_factory: Any, msg: str) -> BaseException:
    try:
        await coro_factory()
    except exc_type as exc:
        return exc
    except Exception as exc:
        raise AssertionError(f"{msg}（期望抛出 {exc_type.__name__}，实际抛出 {type(exc).__name__}: {exc}）") from exc
    raise AssertionError(f"{msg}（未抛出任何异常）")


@dataclass
class _FakeTool:
    name: str
    description: str | None
    input_schema: dict[str, Any] | None


@dataclass
class _FakeListToolsResult:
    tools: list[_FakeTool]


class _FakeSession:
    """离线测试用假 ClientSession：记录每次调用参数并按需模拟正常返回、is_error 与断连异常。"""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.mode = "ok"

    async def list_tools(self) -> _FakeListToolsResult:
        if self.mode == "list_fail":
            raise RuntimeError("http://10.0.0.88:6443 SECRET_LIST_ERR")
        return _FakeListToolsResult(
            tools=[
                # 故意缺少 "type": "object"，验证适配器显式补全 schema.setdefault("type", "object")
                _FakeTool(
                    name="pods_list_in_namespace",
                    description="列出指定 namespace 下的 Pod",
                    input_schema={"properties": {"namespace": {"type": "string"}}, "required": ["namespace"]},
                ),
                _FakeTool(
                    name="pods_log",
                    description="读取 Pod 日志",
                    input_schema={"type": "object", "properties": {"namespace": {"type": "string"}}, "required": ["namespace"]},
                ),
            ]
        )

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> CallToolResult:
        self.calls.append((name, arguments))
        if self.mode == "is_error":
            return CallToolResult(
                content=[TextContent(type="text", text="SA_TOKEN_LEAK_999 permission denied at https://10.1.2.3")],
                is_error=True,
            )
        if self.mode == "closed_stream":
            raise ClosedResourceError("pipe broken: SECRET_PIPE_PATH")
        return CallToolResult(
            content=[TextContent(type="text", text=f"called {name}")],
            structured_content={"tool": name, "args": arguments},
            is_error=False,
        )


class _DummyLLM:
    async def decide(self, request: Any) -> Any:
        raise RuntimeError("离线测试不应触发真实模型调用")


def check_stdio_params_forwarding() -> None:
    """断言 1：_get_stdio_env() 必须原样透传 config.args，而不是 str(tuple) 拼接出双重 --config。"""
    cfg = MCPServerConfig(
        server_name="k8s",
        command="dummy-k8s-mcp.exe",
        args=("--config", "k8s-mcp.toml"),
        kubeconfig=Path("kubeconfig.yaml"),
    )
    adapter = MCPStdioAdapter(cfg)
    params = adapter._get_stdio_env()
    expect(params.command == "dummy-k8s-mcp.exe", f"command 不一致: {params.command!r}")
    expect(
        list(params.args) == ["--config", "k8s-mcp.toml"],
        f"params.args 透传错误，期望 ['--config', 'k8s-mcp.toml']，实际为 {params.args!r}",
    )
    expect(params.env is not None and params.env.get("KUBECONFIG") == "kubeconfig.yaml", "safe_env 缺少 KUBECONFIG")


async def check_offline_guards_and_execution() -> None:
    """断言 2–6：未连接守卫、连接失败脱敏、Schema 兜底与闭包隔离、is_error 脱敏、断连清理。"""
    bad_cfg = MCPServerConfig(
        server_name="k8s",
        command="Z:/not-exists/SECRET_TOKEN_XYZ/k8s-mcp.exe",
        args=("--config", "none.toml"),
        kubeconfig=Path("Z:/not-exists/SECRET_TOKEN_XYZ/kubeconfig.yaml"),
    )
    adapter = MCPStdioAdapter(bad_cfg)

    # 2. 未连接前直接调 list_tool_specs 抛 MCPConnectionError
    await expect_raises_async(
        MCPConnectionError,
        adapter.list_tool_specs,
        "未连接前调用 list_tool_specs 必须抛 MCPConnectionError",
    )

    # 3. 不存在的可执行路径导致连接失败：必须转为固定脱敏文案 MCPConnectionError，保留 __cause__，不泄露路径
    conn_err = await expect_raises_async(
        MCPConnectionError,
        adapter.connect,
        "连接不存在的二进制应捕获底层 OSError/FileNotFoundError 并抛固定脱敏 MCPConnectionError",
    )
    expect("SECRET_TOKEN_XYZ" not in str(conn_err), f"对外报错泄露敏感路径: {conn_err!s}")
    expect(conn_err.__cause__ is not None, "连接失败异常必须通过 raise ... from exc 保留 __cause__")
    expect(adapter._session is None, "连接失败后 _session 必须保持 None")
    await adapter.close()

    # 4. 离线注入假 Session：测缺 type 兜底、注册表/Runtime 导出、与防闭包延迟绑定串工具
    fake_session = _FakeSession()
    adapter._session = fake_session  # type: ignore[assignment]
    specs = await adapter.list_tool_specs()
    expect(len(specs) == 2, f"期望转换出 2 个 ToolSpec，实际 {len(specs)}")

    deps = build_deps()
    for spec in specs:
        deps.tool_registry.register(spec)

    res_list = await deps.tool_registry.execute(
        ToolCall(call_id="m-1", tool_name="mcp__k8s__pods_list_in_namespace", arguments={"namespace": "sre-drill"})
    )
    res_log = await deps.tool_registry.execute(
        ToolCall(call_id="m-2", tool_name="mcp__k8s__pods_log", arguments={"namespace": "sre-drill"})
    )
    expect(res_list.success and res_log.success, f"离线 MCP 工具执行应成功，实际: {res_list!r}, {res_log!r}")
    expect(
        fake_session.calls == [
            ("pods_list_in_namespace", {"namespace": "sre-drill"}),
            ("pods_log", {"namespace": "sre-drill"}),
        ],
        f"闭包绑定错误（怀疑出现延迟绑定串工具）：{fake_session.calls!r}",
    )

    runtime = AgentRuntime(
        llm=_DummyLLM(),  # type: ignore[arg-type]
        tool_registry=deps.tool_registry,
        skill_registry=deps.skill_registry,
    )
    exported = {item["name"]: item for item in runtime._available_tools()}
    expect(
        "mcp__k8s__pods_list_in_namespace" in exported and "mcp__k8s__pods_log" in exported,
        "AgentRuntime._available_tools 应同时包含已注册的 MCP 工具",
    )

    # 5. CallToolResult(is_error=True) 必须转为固定文案报错，绝不把 SA/内网文本透传进 summary 或 data
    fake_session.mode = "is_error"
    res_err = await deps.tool_registry.execute(
        ToolCall(call_id="m-3", tool_name="mcp__k8s__pods_log", arguments={"namespace": "kube-system"})
    )
    expect(not res_err.success and res_err.error_type == "handler_error", f"is_error 应转成失败 ToolResult: {res_err!r}")
    expect("SA_TOKEN_LEAK_999" not in res_err.summary, f"ToolResult.summary 泄露原始报错: {res_err.summary!r}")
    expect("SA_TOKEN_LEAK_999" not in str(res_err.data), f"ToolResult.data 泄露原始报错: {res_err.data!r}")

    # 6. ClosedResourceError 断连异常应触发 close 清理并抛出固定脱敏文案 MCPInvocationError
    fake_session.mode = "closed_stream"
    spec_log = deps.tool_registry.get("mcp__k8s__pods_log")
    inv_err = await expect_raises_async(
        MCPInvocationError,
        lambda: spec_log.handler({"namespace": "sre-drill"}),
        "断连应抛出固定文案 MCPInvocationError",
    )
    expect("SECRET_PIPE_PATH" not in str(inv_err), f"断连异常泄露敏感信息: {inv_err!s}")
    expect(inv_err.__cause__ is not None, "断连异常需保留 __cause__")
    expect(adapter._session is None, "发生 ClosedResourceError 后应清理置空 _session")


async def check_live_k8s_mcp() -> None:
    """可选真实本机拉起检查（传入 --live 时运行，需本机 .sre-agent-data 二进制与配置就绪）。"""
    root = Path(__file__).resolve().parents[2]
    exe = root / ".sre-agent-data/bin/kubernetes-mcp-server-windows-amd64.exe"
    toml = root / ".sre-agent-data/secrets/k8s-mcp.toml"
    kubeconfig = root / ".sre-agent-data/secrets/kubeconfig.yaml"
    for p in (exe, toml, kubeconfig):
        if not p.is_file():
            raise FileNotFoundError(f"缺少本地文件: {p}")

    cfg = MCPServerConfig(
        server_name="k8s",
        command=str(exe),
        args=("--config", str(toml)),
        kubeconfig=kubeconfig,
    )
    adapter = MCPStdioAdapter(cfg)
    await adapter.connect()
    try:
        specs = await adapter.list_tool_specs()
        print(f"[LIVE] 连接成功，共转换 {len(specs)} 个工具:", [s.name for s in specs])
        for s in specs:
            expect(s.name.startswith("mcp__k8s__"), f"工具名前缀异常: {s.name}")
            expect(isinstance(s.to_input_schema(), dict), "to_input_schema 必须返回 dict")
    finally:
        await adapter.close()


def main() -> int:
    check_stdio_params_forwarding()
    asyncio.run(check_offline_guards_and_execution())
    if "--live" in sys.argv:
        asyncio.run(check_live_k8s_mcp())
    print("[PASS] verify_mcp_client 全部离线断言通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
