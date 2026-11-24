from typing import Any
from collections.abc import Callable


_JSON_TYPE_CHECKERS: dict[str, Callable[[Any], bool]] = {
    "string": lambda v: isinstance(v, str),
    # 关键坑：在 Python 里 isinstance(True, int) 为 True！必须排除 bool
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "array": lambda v: isinstance(v, list),
    "object": lambda v: isinstance(v, dict),
    "null": lambda v: v is None,
}

class ToolNotFoundError(Exception):
    """工具不存在。"""

class ToolInputValidationError(Exception):
    """ 工具输入校验失败 """

def validate_arguments_by_schema(arguments: Any, schema: dict[str, Any]) -> None:
    # 1) 顶层必须是 dict
    if not isinstance(arguments, dict):
        raise ToolInputValidationError("arguments 必须是 JSON object (dict)")

    # 2) 检查 required 必填键是否齐全
    required = schema.get("required") or []
    missing = [key for key in required if key not in arguments]
    if missing:
        raise ToolInputValidationError(f"缺少必填参数: {', '.join(missing)}")

    # 3) 遍历已传入的每个参数，核对 properties 里声明的 type
    properties = schema.get("properties") or {}
    for key, value in arguments.items():
        prop_schema = properties.get(key)
        if not isinstance(prop_schema, dict):
            continue  # 未在 properties 声明的键暂跳过（若需严禁额外键可再查 additionalProperties is False）

        expected = prop_schema.get("type")
        if expected is None:
            continue  # 复杂结构如 anyOf / oneOf 暂不在此轻量层硬拦

        # JSON Schema 允许 type 为单个字符串或列表（如 ["string", "null"]）
        allowed_types = [expected] if isinstance(expected, str) else list(expected)
        checkers = [_JSON_TYPE_CHECKERS[t] for t in allowed_types if t in _JSON_TYPE_CHECKERS]
        if checkers and not any(check(value) for check in checkers):
            raise ToolInputValidationError(f"参数 {key!r} 类型不匹配，期望 {expected!r}")