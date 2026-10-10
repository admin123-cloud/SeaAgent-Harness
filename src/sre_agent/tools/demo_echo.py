from pydantic import BaseModel, Field


# 具体工具实现
class DemoEchoInput(BaseModel):
    message: str = Field(min_length=1)

async def run_demo_echo(arguments: DemoEchoInput) -> dict[str, object]:
    return {
        "message": arguments.message,
    }