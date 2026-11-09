import json
import hashlib
from dataclasses import dataclass
from model.models.tool_call import ToolCall,ToolResult

""" 用于观测skill或tool是否存在重复调用 
        存的是 hash,不是结果本身。 64 位十六进制的指纹只有几个字节,真正的结果内容已经在 agent_history 里,Tracker 不再存一份。
        按"签名"存,不按"调用次数"存。 状态就是一张字典 signature → (最近一次指纹, 出现次数)。相同调用 100 次,字典里也只有一条。
        作用域是一次 run。 在 runtime.run() 里创建,最多 max_rounds=5 轮,总共不过几十条,不到 10KB,run 结束就回收,不是全局的。
"""

@dataclass
class FingerCount:
    times:int
    fp:str

# 观测对象
class Tracker:
    def __init__(self, round_no: int, repeats: int, stalled_rounds: int):
        self.round_no = round_no
        self.repeats = repeats
        self.stalled_rounds = stalled_rounds

def signature_of(call: ToolCall) -> str:
    # 将skill   格式化  规范化
    # s1 字符串值先 strip;  这样 "skill://a/b " 和 "skill://a/b" 是同一个签名；
    # s2 用json.dumps(..., sort_keys=True, ensure_ascii=False) 将参数排序和保留中文
    payload = {
        "tool_name":call.tool_name.strip(),
        "arguments":call.arguments.items()
    }
    return json.dumps(payload, sort_keys=True, ensure_ascii=False)

def fingerprint_of(result: ToolResult) -> str:
    #对success / error_type / data取hash, 排除call_id、elapsed_ms、summary。
    payload = {
        "success":result.success,
        "error_type":result.error_type,
        "data":result.data,
    }
    # 1. 序列化为 JSON 字符串（强依赖：sort_keys 保证键序稳定）
    # separators=(',', ':') 去除多余空格，default=str 处理无法序列化的类型（如 datetime）
    raw_string = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(',', ':'),
        default=str
    )
    # 2. 计算 SHA-256 哈希
    return hashlib.sha256(raw_string.encode('utf-8')).hexdigest()

class ProgressTracker:
    tool_name:str
    result_finger:str
    observe:str

    def __init__(self, tool_name:str, result_finger:str, observe:str):
        self.tool_name = tool_name
        self.result_finger = result_finger
        self.observe = observe
        self._stalled = 0
        self._seen_round : dict[str,FingerCount]= {}

    def observe_round(self,round_no,pairs: list[tuple[ToolCall, ToolResult]]) -> Tracker:
        #包含 repeats(同签名第几次)和 progressed(指纹相对上次是否变了),并内部累计 stalled_rounds。
        progressed = False
        max_repeats = 0
        for call, result in pairs:
            sig = signature_of(call)
            fp = fingerprint_of(result)
            prev = self._seen_round.get(sig,None)
            if prev is None:
                times = 1
                progressed = True
            else:
                times = prev.times + 1
                if prev.fp != fp:
                    # 同调用但结果变了
                    progressed = True
                self._seen_round[sig] = FingerCount(times=times,fp=fp)
            max_repeats = max(max_repeats, times)
        if progressed:
            self._stalled = 0
        else:
            self._stalled += 1
        return Tracker(round_no, repeats=max_repeats, stalled_rounds=self._stalled)