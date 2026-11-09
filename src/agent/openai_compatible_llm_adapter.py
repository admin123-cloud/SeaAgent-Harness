import json
from typing import TypedDict, Literal
from dataclasses import dataclass
from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
)
from model.errors.llm_errors import (
    LLMAuthenticationError,
    LLMProviderError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMOutputError,
)
from pydantic import TypeAdapter,ValidationError
from config.llm_settings import LLMSettings
from model.models import AgentDecision
from model.request import DecisionRequest

# 语法错误时重试次数  先写常量，之后再进 settings
MAX_FORMAT_ATTEMPTS = 2
# 创建解析器
_AGENT_DECISION_ADAPTER = TypeAdapter(AgentDecision)


@dataclass
class FormatStats:
    decisions: int = 0  # decide() 被调用的次数
    retried: int = 0  # 至少触发过一次重试的决策数
    failed: int = 0  # 最终仍然格式失败的决策数

class Message(TypedDict):
    role:Literal["system", "user", "assistant","tool"]
    content:str

def _build_message(request) -> list[Message]:
    request_data = request.model_dump(mode="json")
    return [
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
                        '"tool_name":"read_skill",'
                        '"arguments":{"load_ref":"skill://<skill_id>"}}'
                        "]}\n\n"
                        
                        "格式二：可以直接给出结论时：\n"
                        '{"kind":"final","response":{'
                        '"summary":"诊断结论",'
                        '"findings":["发现1","发现2"],'
                        '"evidence_ids":[],'
                        '"confidence":0.9,'
                        '"recommendations":["建议1"]'
                        "}}\n"
                        "findings、recommendations、evidence_ids 的每个元素都必须是字符串，不要使用对象。\n\n"
                        
                        "上下文中的 available_skills 是可用的 Skill 手册目录。\n"
                        "agent_history 是已经执行过的工具调用及其结果；已经在其中出现过的 skill 不要重复加载，直接按其指引给出 final\n"
                        "当问题匹配某个 skill 的 description 时，先用 tool_call 调用 read_skill 工具"
                        "（参数用该 skill 的 load_ref）加载完整指引，再按指引组织诊断。\n\n"
                        
                        "需要外部信息时返回 kind=tool_call；"
                        "信息足够时返回 kind=final。"
                        "字符串内部不要出现英文双引号，需要引用用「」"
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(request_data, ensure_ascii=False),
                },
            ]

def _parse(content, finish_reason) -> AgentDecision:
    try:
        return _AGENT_DECISION_ADAPTER.validate_json(content)
    except ValidationError  as exc:
        summary = []
        for e in exc.errors()[:5]:
            loc = ".".join(str(p) for p in e["loc"]) or "<root>"
            item = f"{loc}:{e['type']}"
            if e["type"] == "json_invalid":
                # 只含位置信息，不含输入内容
                item += f" ({e['msg']})"
            summary.append(item)
        raise LLMOutputError(
        "模型响应不符合 AgentDecision  格式",
            raw_preview=content[:300],
            raw_tail=content[-200:],
            raw_length=len(content),
            finish_reason=finish_reason,
            error_summary=summary,
        ) from exc

def _correction_message(error_summary: list[str]) -> str:
    problems = "；".join(error_summary) or "无法解析为合法 JSON"
    return (
        f"你上一条回复无法被解析，问题位置：{problems}。\n"
        "请重新输出，只返回一个合法 JSON 对象，"
        "格式必须与系统提示中的两种格式之一完全一致，"
        "不要添加 Markdown、代码块或任何解释。"
    )

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
        self.stats = FormatStats()


    async def _complete(self,messages:list[Message]) -> tuple[str, str]:
        try:
            # d2 发送请求
            completion = await  self.client.chat.completions.create(
                model=self.settings.model,
                messages=messages,
                stream=False
            )
        except APITimeoutError as exc:
            raise LLMTimeoutError(f"模型请求超时:{exc}") from exc
        except (AuthenticationError, PermissionDeniedError) as exc:
            raise LLMAuthenticationError(f"密钥无效或无访问权限：{exc}") from exc
        except RateLimitError as exc:
            raise LLMRateLimitError(f"网关限流:{exc}") from exc
        except APIConnectionError as exc:
            raise LLMProviderError(f"无法连接网关：{exc}") from exc
        except APIStatusError as exc:
            raise LLMProviderError(f"网关返回 HTTP {exc.status_code}") from exc

        # 到这里 completion 一定存在
        if not completion.choices:
            raise LLMProviderError("模型响应没有 choices")

        choice = completion.choices[0]
        content = choice.message.content or ""
        if not content or not content.strip():
            raise LLMOutputError("模型响应内容为空")
        return content, choice.finish_reason or "stop"


    async def decide(self,request: DecisionRequest) -> AgentDecision:
        self.stats.decisions += 1
        # d1 请求模型 自动添加提示词
        messages = _build_message(request)
        # d2 对模型请求记录次数 语法问题兜底自动重试
        for attempt in range(1,MAX_FORMAT_ATTEMPTS+1):
            content,finish_reason = await self._complete(messages)
            try:
                # d3 解析大模型的相应信息
                decision = _parse(content,finish_reason)
                return decision
            except LLMOutputError as exc:
                if finish_reason == "length" or  attempt == MAX_FORMAT_ATTEMPTS:
                    exc.attempts = attempt
                    self.stats.failed += 1
                    raise
                if attempt == 1:
                    self.stats.retried += 1
                #  消息中添加错误信息  新建列表，不改原列表
                messages = messages + [
                    Message(role="assistant",content= content),
                    Message(role="user", content= _correction_message(exc.error_summary)),
                ]
        raise LLMOutputError("格式重试次数耗尽")

    async def aclose(self) -> None:
        await self.client.close()