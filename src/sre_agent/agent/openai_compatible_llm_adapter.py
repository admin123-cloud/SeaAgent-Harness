import json
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)
from sre_agent.agent.llm_errors import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMOutputError,
)
from pydantic import TypeAdapter,ValidationError
from sre_agent.config.llm_settings import LLMSettings
from sre_agent.models import AgentDecision
from sre_agent.request.decision_request import DecisionRequest

# 创建解析器
_AGENT_DECISION_ADAPTER = TypeAdapter(AgentDecision)

class OpenAICompatibleLLMAdapter:
    """ openai类型大模型适配器 """
    def __init__(self,settings: LLMSettings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.api_key.get_secret_value(),
            base_url=str(settings.base_url),
            timeout=settings.timeout_seconds,
            max_retries=settings.max_retries,
        )


    async def decide(self,request: DecisionRequest) -> AgentDecision:
        request_data = request.model_dump(mode="json")
        try:
            # 请求模型 自动添加提示词
            completion = await self.client.chat.completions.create(
                model= self.settings.model,
                messages = [
                #系统提示词
                    {
                        "role": "system",
                        "content": (
                            "你是 SRE 辅助决策模型。\n"
                            "只返回一个合法 JSON 对象，不要返回 Markdown、代码块或其他说明。\n"
                            "根对象只能使用以下两种格式之一。\n\n"

                            "格式一：需要调用工具时：\n"
                            '{"kind":"tool_call","tool_calls":['
                            '{"call_id":"call-001",'
                            '"tool_name":"demo_echo",'
                            '"arguments":{"message":"hello"}}'
                            "]}\n\n"

                            "格式二：可以直接给出结论时：\n"
                            '{"kind":"final","response":{'
                            '"summary":"诊断结论",'
                            '"findings":[],'
                            '"evidence_ids":[],'
                            '"confidence":0.9,'
                            '"recommendations":[]'
                            "}}\n\n"

                            "需要外部信息时返回 kind=tool_call；"
                            "信息足够时返回 kind=final。"
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(request_data, ensure_ascii=False),
                    },
                ],
                stream= False
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError("CETC 请求超时") from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            raise LLMAuthenticationError("CETC 密钥无效或无访问权限") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError("CETC 网关限流") from exc
        except APIConnectionError as exc:
            raise LLMProviderError("无法连接 CETC 网关") from exc
        except APIStatusError as exc:
            raise LLMProviderError(f"CETC 网关返回 HTTP {exc.status_code}") from exc
        if not completion.choices:
            raise LLMOutputError("模型响应没有 choices")
        content = completion.choices[0].message.content
        if not content or not content.strip():
            raise LLMOutputError("模型响应内容为空")

        try:
            return _AGENT_DECISION_ADAPTER.validate_json(content)
        except ValidationError  as exc:
            raise LLMOutputError("模型响应不符合 AgentDecision  格式") from exc


    async def aclose(self) -> None:
        await self.client.close()