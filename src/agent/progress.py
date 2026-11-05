""" 用于观测skill或tool是否存在重复调用 """

class ProgressTracker:
    # 签名 (tool_name, 规范化的 arguments)  用json.dumps(..., sort_keys=True, ensure_ascii=False)，字符串值先 strip，这样 "skill://a/b " 和 "skill://a/b" 是同一个签名；
    tool_name:str
    result_finger:str
    observe:str

    def __init__(self, tool_name:str, result_finger:str, observe:str):
            self.tool_name = tool_name
            self.result_finger = result_finger
            self.observe = observe

