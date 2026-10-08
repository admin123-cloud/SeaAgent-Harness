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
from pydantic import ValidationError
from sre_agent.config.llm_settings import LLMSettings
from sre_agent.request.decision_request import DecisionRequest
from sre_agent.response.decision_response import DecisionResponse


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


    async def decide(self,request: DecisionRequest) -> DecisionResponse:
        request_data = request.model_dump(mode="json")
        try:
            # 请求模型 自动添加提示词
            completion = await self.client.chat.completions.create(
                model= self.settings.model,
                messages = [
                #系统提示词
                    {
                        "role":"system",
                        "content":(
                            "你是 SRE 辅助决策模型。"
                            "只返回一个 JSON 对象，不要添加 Markdown 或其他说明。"
                            "对象字段为 summary、findings、evidence_ids、confidence、recommendations。"
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
            raise LLMProviderError(
                f"CETC 网关返回 HTTP {exc.status_code}"
            ) from exc
        if not completion.choices:
            raise LLMOutputError("模型响应没有 choices")
        content = completion.choices[0].message.content
        if not content or not content.strip():
            raise LLMOutputError("模型响应内容为空")

        try:
            return DecisionResponse.model_validate_json(content)
        except ValidationError  as exc:
            raise LLMOutputError("模型响应不符合 DecisionResponse 格式") from exc


    async def aclose(self) -> None:
        await self.client.close()