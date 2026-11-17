import ssl
import httpx
from pathlib import Path
from pydantic import SecretStr
from tools import K8sReadClient



def handler_timeout(request):
    raise httpx.ConnectTimeout("t")          # 期望 K8sConnectError

def handler_tls(request):
    err = ssl.SSLCertVerificationError("bad cert")
    raise httpx.ConnectError("x") from err   # 期望 K8sTlsError，不是 K8sConnectError

client = K8sReadClient("https://k8s.example", SecretStr("tok"), Path("unused"),
                       transport=httpx.MockTransport(handler_tls))