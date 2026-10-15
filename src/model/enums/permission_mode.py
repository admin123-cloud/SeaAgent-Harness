from enum import StrEnum


class PermissionMode(StrEnum):
    """Agent 会话级工具权限模式。"""

    REQUEST_APPROVAL = "request_approval"
    FULL_ACCESS = "full_access"
