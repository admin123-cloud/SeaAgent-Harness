import os,asyncio, hashlib, json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


ROOT = Path(r"D:\AI\Develop\SreAgent")
EXE = ROOT / ".sre-agent-data/bin/kubernetes-mcp-server-windows-amd64.exe"
TOML = ROOT / ".sre-agent-data/secrets/k8s-mcp.toml"
KUBECONFIG = ROOT / ".sre-agent-data/secrets/kubeconfig.yaml"

# MCP 提供的方法
EXPECTED = {
    "events_list",
    "pods_get",
    "pods_list_in_namespace",
    "pods_log",
}

async def main():
    for path in (EXE, TOML, KUBECONFIG):
        if not path.is_file():
            raise FileNotFoundError(path)

    allowed_keys = ["PATH", "SYSTEMROOT", "WINDIR"]
    safe_env = {
        k: os.environ[k]
        for k in allowed_keys
        if k in os.environ
    }
    safe_env["KUBECONFIG"] = str(KUBECONFIG)

    params = StdioServerParameters(
        command=str(EXE),
        args=["--config", str(TOML)],
        env=safe_env,
    )

    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()

            tools = (await session.list_tools()).tools
            tool_names = []
            for tool in tools:
                tool_names.append(tool.name)
            #1 list_tools 返回恰好
            names = set(tool_names)

            print("=== 1. 工具白名单 ===")
            print(names)

            if "pods_list_in_namespace" not in names:
                raise RuntimeError("缺少 Pod 列表工具")


            print("\n=== 2. sre-drill Pod 读取 ===")
            #2	调pods_list_in_namespace，namespace=sre-drill
            result = await session.call_tool(name = "pods_list_in_namespace",arguments={"namespace":"sre-drill"})
            print(result)

            #3 测试越权
            print("\n=== 3. kube-system 越权读取 ===")
            result = await session.call_tool(name="pods_list_in_namespace", arguments={"namespace": "kube-system"})
            print(result)

            if "pods_exec" not in names:
                print("缺少 pods_exec 工具")
            else:
                # 4	调 pods_exec
                result = await session.call_tool(name="pods_exec", arguments={"namespace": "kube-system"})
                print(result)

            #5 调pods_get，看返回里有没有环境变量，值在不在
            result = await session.call_tool(name="pods_get", arguments={ "name": "mcp-test","namespace": "sre-drill"})
            print(result)



if __name__ == "__main__":
    asyncio.run(main())