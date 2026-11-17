import re
import ssl
import httpx
from pathlib import Path
from pydantic import SecretStr
from model.errors.k8s_errors import K8sConnectError,K8sTlsError,K8sUnauthorizedError,K8sForbiddenError,K8sNotFoundError,K8sApiError,_is_cert_error


_NS_RE = re.compile(r"[a-z0-9]([-a-z0-9]*[a-z0-9])?")
def _check_namespace(ns: str) -> str:
    if len(ns) > 63 or not _NS_RE.fullmatch(ns):
        raise ValueError("namespace 格式不合法")
    return ns

class K8sReadClient:
    def __init__(self,
                 server: str,
                 token: SecretStr,
                 ca_file: Path,
                 *,
                 # 1. 默认值设为 None，类型支持 float 或 httpx.Timeout
                 timeout:  float | httpx.Timeout | None = None,
                 transport: httpx.AsyncBaseTransport | None = None):
        kwargs = {}
        if transport is None:  # 测试时传了 MockTransport，就不用也不能建真实证书上下文
            kwargs["verify"] = ssl.create_default_context(cafile=str(ca_file))

        # 2. 判断是否传了 timeout。不传(None)则用默认值
        _timeout = timeout if timeout is not None else httpx.Timeout(10.0, connect=3.0)

        self._client = httpx.AsyncClient(
            base_url=server.rstrip("/"),
            headers={"Authorization": f"Bearer {token.get_secret_value()}"},
            timeout=_timeout,
            transport=transport,
            **kwargs,
        )

    async def _get(self, path: str, params: dict[str, str] | None = None) -> httpx.Response:
        try:
            resp = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:  # 连接超时、读取超时
            raise K8sConnectError("请求 API Server 超时") from exc
        except httpx.ConnectError as exc:
            if _is_cert_error(exc):  # 必须先查证书，再当普通连接错误
                raise K8sTlsError("证书校验失败") from exc
            raise K8sConnectError("无法连接 API Server") from exc
        except httpx.HTTPError as exc:  # 其余传输层错误，兜底
            raise K8sConnectError("访问 API Server 失败") from exc

        code = resp.status_code
        if code == 200:
            return resp
        if code == 401:
            raise K8sUnauthorizedError("token 无效或已过期（HTTP 401）")
        if code == 403:
            raise K8sForbiddenError("无权限访问该资源（HTTP 403）")
        if code == 404:
            raise K8sNotFoundError("资源不存在（HTTP 404）")
        raise K8sApiError(f"API Server 返回 HTTP {code}", code)


    async def list_pods(self, namespace: str, label_selector: str | None = None) -> dict: ...
    async def get_pod(self, namespace: str, name: str) -> dict: ...
    async def list_events(self, namespace: str, field_selector: str | None = None) -> dict: ...
    async def get_pod_log(self, namespace: str, name: str, *, container: str | None = None,
                          tail_lines: int = 100, previous: bool = False) -> str: ...
    async def aclose(self) -> None: ...