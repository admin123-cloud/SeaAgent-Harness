from pydantic_settings import BaseSettings,SettingsConfigDict
from pydantic import AnyHttpUrl,SecretStr,Field

class LLMSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix = 'LLM_',
        env_file=".env",
        env_file_encoding="utf-8",
        str_strip_whitespace = True,
        extra = "ignore"
    )


    # 模型服务地址
    base_url: AnyHttpUrl
    # 服务模型名称
    model: str = Field(min_length=1)
    # apikey密钥
    api_key: SecretStr
    # 超时时间 默认30秒
    timeout_seconds: float= Field(default=30,gt=0)
    # 超时重试次数
    max_retries: int = Field(default=2,ge=0,le=5)