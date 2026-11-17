import ssl

class K8sError(Exception):
    """模型调用错误基类。"""

class K8sConnectError(K8sError):
    """k8s 连接超时或连不上。"""
    """ httpx.ConnectTimeout、httpx.ConnectError """

class K8sTlsError(K8sError):
    """ 证书校验失败 """
    """ 沿着 exc.__cause__ / __context__ 链找 ssl.SSLCertVerificationError """

class K8sUnauthorizedError(K8sError):
    """ 401 response.status_code == 401"""

class K8sForbiddenError(K8sError):
    """ 403 response.status_code == 403"""

class K8sNotFoundError(K8sError):
    """404 及其他状态码"""

class K8sApiError(K8sError):  # 其他状态码
    def __init__(self, message:str, status_code:int):
        super().__init__(message)
        self.status_code = status_code

def _is_cert_error(exc: BaseException | None) -> bool:
    while exc is not None:
        if isinstance(exc, ssl.SSLCertVerificationError):
            return True
        exc = exc.__cause__ or exc.__context__  # 顺着异常链往下找
    return False