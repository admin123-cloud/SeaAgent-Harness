import json
import hashlib
from model.models.tool_call import ToolCall,ToolResult

""" 用于观测skill或tool是否存在重复调用 
        存的是 hash,不是结果本身。 12 位十六进制的指纹只有几个字节,真正的结果内容已经在 agent_history 里,Tracker 不再存一份。
        按"签名"存,不按"调用次数"存。 状态就是一张字典 signature → (最近一次指纹, 出现次数)。相同调用 100 次,字典里也只有一条。
        作用域是一次 run。 在 runtime.run() 里创建,最多 max_rounds=5 轮,总共不过几十条,不到 10KB,run 结束就回收,不是全局的。
"""

class FingerCount:
    times:int
    fp:str
    def __init__(self,times:int,fp:str):
        self.times = times
        self.fp = fp

# 观测对象
class Tracker:
    def __init__(self, round_no: int, repeats: int, stalled_rounds: int):
        self.round_no = round_no
        self.repeats = repeats
        self.stalled_rounds = stalled_rounds

_seen_round : dict[str,FingerCount]= {}
_stalled = 0

def observe_round(round_no,pairs: list[(call, result)]) -> Tracker:
    # 修复：声明使用全局变量
    global _stalled
    # # 返回一个小对象,至少包含 repeats(同签名第几次)和 progressed(指纹相对上次是否变了),并内部累计 stalled_rounds。
    progressed = False
    max_repeats = 0
    for call, result in pairs:
        sig = signature_of(call)
        fp = fingerprint_of(result)
        prev = _seen_round.get(sig,None)
        if prev is None:
            times = 1
            progressed = True
        else:
            times = prev.times + 1
            if prev.fp != fp:
                # 同调用但结果变了
                progressed = True
            _seen_round[sig] = FingerCount(times=times,fp=fp)
        max_repeats = max(max_repeats, times)
    if progressed:
        _stalled = 0
    else:
        _stalled += 1
    return Tracker(round_no, repeats=max_repeats, stalled_rounds=_stalled)

def signature_of(call: ToolCall) -> str:
    # 将skill   格式化  规范化
    # s1 字符串值先 strip;  这样 "skill://a/b " 和 "skill://a/b" 是同一个签名；
    # s2 用json.dumps(..., sort_keys=True, ensure_ascii=False) 将参数排序和保留中文
    return json.dumps(call.tool_name.strip(), sort_keys=True, ensure_ascii=False)

def fingerprint_of(result: ToolResult) -> str:
    #对success / error_type / data取hash, 排除call_id、elapsed_ms、summary。
    raw_string = repr((result.success, result.error_type, result.data))
    hash_value = hashlib.sha256(raw_string.encode('utf-8')).hexdigest()
    return hash_value

class ProgressTracker:
    tool_name:str
    result_finger:str
    observe:str

    def __init__(self, tool_name:str, result_finger:str, observe:str):
            self.tool_name = tool_name
            self.result_finger = result_finger
            self.observe = observe


# runtime 在每轮工具执行后调用,发出 progress 事件 {round, repeats, stalled_rounds}。只观测,不改变控制流,不熔断。
# 完成后,删掉 verify_runtime.report() 里自己的 seen_tools 逻辑,以 runtime 事件为准(FR-020)。
# 自测用例:
# 同调用同结果两次,repeats=2 且判定为无进展。
# 同调用但结果不同,判定为有进展。
# 参数键序不同、首尾空白不同,签名相同