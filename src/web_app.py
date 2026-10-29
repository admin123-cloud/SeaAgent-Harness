"""本地 SRE 事件工作台。

启动：python -m web_app
页面只使用标准库 HTTP 服务，事件和过程记录复用 SQLite 仓储。
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
from pathlib import Path
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse
from uuid import uuid4

from pydantic import ValidationError
from agent import AgentRuntime
from agent.openai_compatible_llm_adapter import OpenAICompatibleLLMAdapter
from agent.state_manager import StateManager
from config import LLMSettings
from model.enums import DecisionTask
from model.enums import IncidentStatus
from model.models import ConversationEntry
from model.models import AgentDecision, FinalDecision, ToolCallDecision
from model.models import Incident
from model.request import DecisionRequest
from model.response.decision_response import DecisionResponse
from database import IncidentRepository, SQLiteDatabase
from bootstrap import build_deps

_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
  <title>SRE Agent 工作台</title>
  <style>
    :root{font-family:Inter,"Segoe UI",Arial,sans-serif;color:#182230;background:#f4f6fa}
    *{box-sizing:border-box}body{margin:0;height:100vh;overflow:hidden}.app{display:grid;grid-template-columns:290px 1fr;height:100vh}
    aside{background:#111827;color:#dbe5f0;padding:18px 14px;display:flex;flex-direction:column;gap:14px}
    .brand{font-size:19px;font-weight:700;padding:4px 8px 14px}.brand small{display:block;color:#8fa1b8;font-size:12px;font-weight:400;margin-top:5px}
    button{border:0;border-radius:8px;padding:9px 12px;cursor:pointer;font:inherit}.new{background:#3b82f6;color:white;width:100%;font-weight:600}.new:hover{background:#2563eb}
    #incident-list{overflow:auto;display:flex;flex-direction:column;gap:5px}.incident{padding:11px 10px;border-radius:8px;cursor:pointer;border:1px solid transparent}.incident:hover,.incident.active{background:#1f2937;border-color:#334155}.incident .title{font-size:13px;font-weight:600;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.incident .meta{font-size:11px;color:#93a4b9;margin-top:6px;display:flex;justify-content:space-between}.status{font-size:10px;border-radius:12px;padding:2px 7px;background:#334155}.status-DIAGNOSING{background:#854d0e;color:#fde68a}.status-RESOLVED{background:#166534;color:#bbf7d0}.status-BLOCKED,.status-FAILED{background:#991b1b;color:#fecaca}
    main{display:grid;grid-template-rows:auto 1fr;min-width:0}.topbar{background:#fff;border-bottom:1px solid #e5e7eb;padding:17px 24px;display:flex;justify-content:space-between;align-items:center}.topbar h1{font-size:18px;margin:0}.topbar .id{font-size:12px;color:#64748b;margin-top:4px}.layout{display:grid;grid-template-columns:minmax(360px,1.25fr) minmax(300px,.75fr);min-height:0}.workspace{padding:22px 24px;overflow:auto}.side{border-left:1px solid #e5e7eb;background:#fff;padding:20px;overflow:auto}.empty{height:100%;display:grid;place-items:center;color:#64748b}.empty div{text-align:center}.empty strong{display:block;color:#334155;font-size:18px;margin-bottom:7px}.chat{display:flex;flex-direction:column;gap:12px;max-width:900px}.bubble{max-width:86%;padding:12px 14px;border-radius:12px;line-height:1.55;font-size:14px;white-space:pre-wrap}.bubble.user{align-self:flex-end;background:#2563eb;color:#fff;border-bottom-right-radius:3px}.bubble.assistant{align-self:flex-start;background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:3px}.bubble .time{display:block;font-size:10px;opacity:.62;margin-top:7px}.composer{display:flex;gap:9px;margin-top:20px;position:sticky;bottom:0;background:#f4f6fa;padding-top:8px}.composer textarea{flex:1;resize:vertical;min-height:52px;max-height:160px;border:1px solid #cbd5e1;border-radius:9px;padding:11px;font:inherit}.send{background:#0f766e;color:#fff;align-self:flex-end}.send:disabled{opacity:.5;cursor:wait}.section-title{font-size:12px;letter-spacing:.05em;color:#64748b;text-transform:uppercase;margin:0 0 10px}.panel{margin-bottom:23px}.timeline{display:flex;flex-direction:column;gap:10px}.trace{border-left:2px solid #cbd5e1;padding:1px 0 5px 13px}.trace .trace-head{font-size:12px;font-weight:650;color:#334155}.trace .trace-body{font-size:12px;line-height:1.5;color:#64748b;margin-top:4px;white-space:pre-wrap}.trace .trace-time{font-size:10px;color:#94a3b8;margin-top:4px}.kv{display:grid;grid-template-columns:88px 1fr;gap:7px;font-size:12px}.kv b{color:#64748b;font-weight:500}.evidence{padding:9px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;font-size:12px;margin-bottom:7px}.evidence b{display:block;color:#334155}.danger{color:#b91c1c;background:#fee2e2}.delete{background:transparent;color:#ef4444;font-size:12px;padding:5px 7px}.modal{position:fixed;inset:0;background:#0f172a99;display:grid;place-items:center}.modal.hidden{display:none}.form{background:#fff;border-radius:12px;padding:22px;width:min(480px,calc(100vw - 30px));box-shadow:0 20px 55px #0f172a33}.form h2{margin:0 0 15px;font-size:18px}.form label{display:block;font-size:12px;color:#475569;margin:11px 0 5px}.form input,.form textarea{width:100%;border:1px solid #cbd5e1;border-radius:7px;padding:9px;font:inherit}.form textarea{min-height:90px}.actions{display:flex;justify-content:flex-end;gap:8px;margin-top:16px}.cancel{background:#e2e8f0}.create{background:#2563eb;color:#fff}
  </style>
</head>
<body><div class="app"><aside><div class="brand">SRE Agent 工作台<small>按事件保留完整定位过程</small></div><button class="new" id="new-btn">＋ 新建事件</button><div id="incident-list"></div></aside><main><div class="topbar"><div><h1 id="page-title">选择一个事件开始</h1><div class="id" id="page-id"></div></div><button class="delete" id="delete-btn" hidden>删除事件</button></div><div class="layout"><section class="workspace" id="workspace"><div class="empty"><div><strong>还没有打开事件</strong>从左侧新建或选择一个 SRE 事件</div></div></section><section class="side"><div class="panel"><h3 class="section-title">处理状态</h3><div id="incident-meta">选择事件后显示</div></div><div class="panel"><h3 class="section-title">Agent 处理过程</h3><div class="timeline" id="timeline"><div style="font-size:12px;color:#94a3b8">暂无过程记录</div></div></div><div class="panel"><h3 class="section-title">证据</h3><div id="evidence-list"><div style="font-size:12px;color:#94a3b8">暂无证据</div></div></div></section></div></main></div>
<div class="modal hidden" id="modal"><form class="form" id="new-form"><h2>新建 SRE 事件</h2><label>事件目标</label><textarea id="goal" required placeholder="例如：诊断 default/demo Pod 启动失败"></textarea><label>Namespace（可选）</label><input id="namespace" placeholder="default"><label>Pod / Job（可选）</label><input id="resource" placeholder="demo"><div class="actions"><button type="button" class="cancel" id="cancel-btn">取消</button><button class="create">创建事件</button></div></form></div>
<script>
const state={incidents:[],current:null}; const $=id=>document.getElementById(id);
const statusLabel={CREATED:'已创建',PLANNING:'规划中',DIAGNOSING:'诊断中',ACTING:'执行中',VERIFYING:'验证中',RESOLVED:'已解决',BLOCKED:'已阻塞',FAILED:'失败'};
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function time(v){return v?new Date(v).toLocaleString('zh-CN',{hour12:false}):''}
async function api(path,opt={}){const r=await fetch(path,{headers:{'Content-Type':'application/json'},...opt});const d=await r.json();if(!r.ok)throw Error(d.error||'请求失败');return d}
async function loadList(){state.incidents=await api('/api/incidents');$('incident-list').innerHTML=state.incidents.map(i=>`<div class="incident ${state.current&&state.current.incident.incident_id===i.incident_id?'active':''}" data-id="${esc(i.incident_id)}"><div class="title">${esc(i.goal)}</div><div class="meta"><span>${esc(i.incident_id.slice(0,8))}</span><span class="status status-${esc(i.status)}">${statusLabel[i.status]||i.status}</span></div></div>`).join('');document.querySelectorAll('.incident').forEach(x=>x.onclick=()=>openIncident(x.dataset.id));}
async function openIncident(id){state.current=await api('/api/incidents/'+encodeURIComponent(id));render();loadList()}
function render(){const c=state.current;if(!c)return;$('page-title').textContent=c.incident.goal;$('page-id').textContent=c.incident.incident_id;$('delete-btn').hidden=false;$('incident-meta').innerHTML=`<div class="kv"><b>状态</b><span class="status status-${esc(c.incident.status)}">${statusLabel[c.incident.status]||c.incident.status}</span><b>阶段</b><span>${esc(c.incident.stage||'尚未开始')}</span><b>环境</b><span>${esc(Object.entries(c.incident.environment||{}).map(([k,v])=>k+'='+v).join('，')||'未填写')}</span><b>更新时间</b><span>${time(c.incident.updated_at)}</span></div>`;const msgs=c.entries.filter(e=>e.kind==='message');$('workspace').innerHTML=`<div class="chat">${msgs.map(m=>`<div class="bubble ${m.role==='user'?'user':'assistant'}">${esc(m.content)}<span class="time">${time(m.created_at)}</span></div>`).join('')||'<div class="empty" style="height:180px"><div>发送第一条消息，开始本次事件定位</div></div>'}</div><div class="composer"><textarea id="message" placeholder="补充现象、日志或想让 Agent 核查的目标…"></textarea><button class="send" id="send">发送</button></div>`;$('send').onclick=sendMessage;$('message').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage()}});const entries=c.entries.filter(e=>e.kind!=='message');const transitions=(c.incident.status_history||[]).map(t=>({content:`状态：${statusLabel[t.from_status]||t.from_status} → ${statusLabel[t.to_status]||t.to_status}`,data:t.reason?{reason:t.reason}:{},created_at:t.changed_at}));const traces=entries.map(e=>({content:e.content,data:e.data,created_at:e.created_at})).concat(transitions).sort((a,b)=>new Date(a.created_at)-new Date(b.created_at));$('timeline').innerHTML=traces.map(e=>`<div class="trace"><div class="trace-head">${esc(e.content)}</div>${Object.keys(e.data||{}).length?`<div class="trace-body">${esc(JSON.stringify(e.data,null,2))}</div>`:''}<div class="trace-time">${time(e.created_at)}</div></div>`).join('')||'<div style="font-size:12px;color:#94a3b8">暂无过程记录</div>';$('evidence-list').innerHTML=c.incident.evidence.map(e=>`<div class="evidence"><b>${esc(e.kind)} · ${esc(e.evidence_id)}</b>${esc(e.summary)}</div>`).join('')||'<div style="font-size:12px;color:#94a3b8">暂无证据</div>'}
async function sendMessage(){const input=$('message'),content=input.value.trim(),btn=$('send');if(!content)return;btn.disabled=true;try{state.current=await api('/api/incidents/'+encodeURIComponent(state.current.incident.incident_id)+'/messages',{method:'POST',body:JSON.stringify({content})});render();loadList()}catch(e){alert(e.message)}finally{btn.disabled=false}}
$('new-btn').onclick=()=>{$('modal').classList.remove('hidden');$('goal').focus()};$('cancel-btn').onclick=()=>{$('modal').classList.add('hidden')};$('new-form').onsubmit=async e=>{e.preventDefault();try{const environment={};if($('namespace').value.trim())environment.namespace=$('namespace').value.trim();if($('resource').value.trim())environment.resource=$('resource').value.trim();const d=await api('/api/incidents',{method:'POST',body:JSON.stringify({goal:$('goal').value,environment})});$('modal').classList.add('hidden');e.target.reset();await loadList();await openIncident(d.incident_id)}catch(err){alert(err.message)}};$('delete-btn').onclick=async()=>{if(!state.current||!confirm('确定删除该事件及其全部过程记录吗？'))return;try{await api('/api/incidents/'+encodeURIComponent(state.current.incident.incident_id),{method:'DELETE'});state.current=null;$('delete-btn').hidden=true;$('page-title').textContent='选择一个事件开始';$('page-id').textContent='';$('workspace').innerHTML='<div class="empty"><div><strong>还没有打开事件</strong>从左侧新建或选择一个 SRE 事件</div></div>';$('timeline').innerHTML='<div style="font-size:12px;color:#94a3b8">暂无过程记录</div>';$('incident-meta').textContent='选择事件后显示';$('evidence-list').innerHTML='<div style="font-size:12px;color:#94a3b8">暂无证据</div>';await loadList()}catch(e){alert(e.message)}};loadList();
</script></body></html>'''


class SREWebApp:
    def __init__(self) -> None:
        self.database = SQLiteDatabase()
        self.repository = IncidentRepository(self.database)
        self.repository.initialize()
        self.lock = threading.Lock()

        deps = build_deps()
        self.toolkit = deps.skill_toolkit
        self.registry = deps.tool_registry

    @staticmethod
    def _public_incident(incident: Incident) -> dict[str, object]:
        return incident.model_dump(mode="json", exclude={"evidence", "status_history"})

    def list_incidents(self) -> list[dict[str, object]]:
        return [self._public_incident(i) for i in self.repository.list_incidents()]

    def get_incident(self, incident_id: str) -> dict[str, object]:
        incident = self.repository.get_incident(incident_id)
        if incident is None:
            raise KeyError("事件不存在")
        return {
            "incident": incident.model_dump(mode="json"),
            "entries": [e.model_dump(mode="json") for e in self.repository.get_conversation_entries(incident_id)],
        }

    def create_incident(self, payload: dict[str, object]) -> dict[str, str]:
        goal = str(payload.get("goal", "")).strip()
        if not goal:
            raise ValueError("事件目标不能为空")
        environment = payload.get("environment") or {}
        if not isinstance(environment, dict):
            raise TypeError("environment 必须是对象")
        incident = Incident(
            incident_id=f"incident-{uuid4().hex[:12]}",
            goal=goal,
            environment={str(k): str(v) for k, v in environment.items()},
        )
        self.repository.create_incident(incident)
        self.repository.add_conversation_entry(
            incident.incident_id,
            ConversationEntry(role="agent", kind="process", content="事件已创建，等待开始处理"),
        )
        return {"incident_id": incident.incident_id}

    def delete_incident(self, incident_id: str) -> None:
        if not self.repository.delete_incident(incident_id):
            raise KeyError("事件不存在")

    def add_message(self, incident_id: str, content: str) -> dict[str, object]:
        content = content.strip()
        if not content:
            raise ValueError("消息不能为空")
        with self.lock:
            incident = self.repository.get_incident(incident_id)
            if incident is None:
                raise KeyError("事件不存在")
            self.repository.add_conversation_entry(
                incident_id, ConversationEntry(role="user", kind="message", content=content)
            )
            manager = StateManager(incident, self.repository)
            if incident.status == IncidentStatus.CREATED:
                manager.transition_to(IncidentStatus.PLANNING)
                incident = self.repository.get_incident(incident_id) or incident
                self.repository.add_conversation_entry(
                    incident_id, ConversationEntry(role="agent", kind="process", content="进入 PLANNING：整理事件目标和环境")
                )
            if incident.status == IncidentStatus.PLANNING:
                manager = StateManager(incident, self.repository)
                manager.transition_to(IncidentStatus.DIAGNOSING)
                incident = self.repository.get_incident(incident_id) or incident
                self.repository.add_conversation_entry(
                    incident_id, ConversationEntry(role="agent", kind="process", content="进入 DIAGNOSING：准备结构化诊断请求")
                )

            context = {
                "environment": incident.environment,
                "incident_status": incident.status.value,
                "evidence": [
                    {"evidence_id": e.evidence_id, "kind": e.kind, "summary": e.summary}
                    for e in incident.evidence
                ],
                "conversation_message": content,
            }
            # 记录会话
            self.repository.add_conversation_entry(
                incident_id,
                ConversationEntry(
                    role="agent",
                    kind="llm_request",
                    content="提交诊断请求到模型适配器",
                    data={"task": DecisionTask.DIAGNOSE.value, "context": context},
                ),
            )
            try:
                raw_decision = asyncio.run(
                    self.run_agent(
                        DecisionRequest(
                            task=DecisionTask.DIAGNOSE,
                            incident_id=incident_id,
                            goal=incident.goal,
                            context=context,
                        )
                    )
                )

                # 兼容适配器迁移期间的旧 DecisionResponse 返回值。
                if isinstance(raw_decision, DecisionResponse):
                    decision: AgentDecision = FinalDecision(response=raw_decision)
                elif isinstance(raw_decision, (FinalDecision, ToolCallDecision)):
                    decision = raw_decision
                else:
                    raise TypeError(
                        f"LLM Adapter 返回了不支持的决策类型：{type(raw_decision).__name__}"
                    )

                result_data = decision.model_dump(mode="json")
                self.repository.add_conversation_entry(
                    incident_id,
                    ConversationEntry(
                        role="agent",
                        kind="llm_response",
                        content="模型返回结构化决策",
                        data=result_data,
                    ),
                )

                if isinstance(decision, FinalDecision):
                    response = decision.response
                    assistant_text = response.summary
                    if response.findings:
                        assistant_text += "\n\n发现：\n" + "\n".join(
                            f"- {item}" for item in response.findings
                        )
                    if response.recommendations:
                        assistant_text += "\n\n建议：\n" + "\n".join(
                            f"- {item}" for item in response.recommendations
                        )
                else:
                    requested_tools = "\n".join(
                        f"- {tool_call.tool_name}（调用 ID：{tool_call.call_id}）"
                        for tool_call in decision.tool_calls
                    )
                    assistant_text = (
                        "模型决定先调用以下工具：\n"
                        f"{requested_tools}\n\n"
                        "当前工具执行流程尚未接入，因此本次只记录了工具调用决策，没有实际执行工具。"
                    )
                self.repository.add_conversation_entry(
                    incident_id, ConversationEntry(role="assistant", kind="message", content=assistant_text)
                )
            except Exception as exc:  # noqa: BLE001 - 页面要保留可诊断错误，不把服务打崩
                error = f"模型调用未完成：{type(exc).__name__}: {exc}"
                failed_state = self.repository.get_incident(incident_id)

                if failed_state and failed_state.status in {
                    IncidentStatus.PLANNING,
                    IncidentStatus.DIAGNOSING,
                    IncidentStatus.ACTING,
                    IncidentStatus.VERIFYING,
                }:
                    StateManager(
                        failed_state,
                        self.repository,
                    ).transition_to(
                        IncidentStatus.FAILED,
                        reason=error[:500],
                    )

                self.repository.add_conversation_entry(
                    incident_id,
                    ConversationEntry(
                        role="agent",
                        kind="error",
                        content=error,
                    ),
                )
        return self.get_incident(incident_id)

    async def run_agent(self,request:DecisionRequest,) -> FinalDecision:
        #  src目录和root目录 找到skill
        src_dir = Path(__file__).resolve().parents[1]
        # 内置skill和上传的skill
        skill_registry = SkillRegistry(
            builtin=FileSkillStore(src_dir / "skills", source="builtin", read_only=True),
            team=FileSkillStore(src_dir.parent / ".sre-agent-data" / "skills"),
        )
        settings = LLMSettings()
        adapter = OpenAICompatibleLLMAdapter(settings)
        toolkit = SkillToolkit(skill_registry)

        # tool_registry = build_default_registry(toolkit)
        try:
            runtime = AgentRuntime(
                llm=adapter,
                registry=self.registry,
                skill_toolkit=toolkit,
                max_rounds=5,
                event_sink= lambda event_type, data: (
                    self.record_runtime_event(
                        request.incident_id,
                        event_type,
                        data,
                    )
                ),
            )

            return await runtime.run(request)
        finally:
            await adapter.aclose()

    def record_runtime_event(self,incident_id:str,event_type: str,data: dict[str, object],) -> None:
        labels = {
            "tool_call": "Runtime 请求调用工具",
            "tool_result": "Runtime 收到工具结果",
        }

        self.repository.add_conversation_entry(
            incident_id,
            ConversationEntry(
                role="agent",
                kind="process",
                content=labels.get(
                    event_type,
                    f"Runtime 事件：{event_type}",
                ),
                data=data,
            ),
        )

class RequestHandler(BaseHTTPRequestHandler):
    app: SREWebApp

    def log_message(self, format: str, *args: object) -> None:
        print(f"[web] {format % args}")

    def _send(self, status: int, payload: object, content_type: str = "application/json") -> None:
        body = payload.encode("utf-8") if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json_body(self) -> dict[str, object]:
        length = int(self.headers.get("Content-Length", "0"))
        if length > 1_000_000:
            raise ValueError("请求体过大")
        return json.loads(self.rfile.read(length) or b"{}")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/":
                self._send(HTTPStatus.OK, _HTML, "text/html")
            elif path == "/api/incidents":
                self._send(HTTPStatus.OK, self.app.list_incidents())
            elif path.startswith("/api/incidents/"):
                incident_id = unquote(path.split("/", 3)[3])
                self._send(HTTPStatus.OK, self.app.get_incident(incident_id))
            else:
                self._send(HTTPStatus.NOT_FOUND, {"error": "路径不存在"})
        except KeyError as exc:
            self._send(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - HTTP 边界统一返回 JSON 错误
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            payload = self._json_body()
            if path == "/api/incidents":
                self._send(HTTPStatus.CREATED, self.app.create_incident(payload))
            elif path.startswith("/api/incidents/") and path.endswith("/messages"):
                incident_id = unquote(path[len("/api/incidents/"):-len("/messages")])
                self._send(HTTPStatus.OK, self.app.add_message(incident_id, str(payload.get("content", ""))))
            else:
                self._send(HTTPStatus.NOT_FOUND, {"error": "路径不存在"})
        except (ValueError, TypeError, ValidationError) as exc:
            self._send(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        except KeyError as exc:
            self._send(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - HTTP 边界统一返回 JSON 错误
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        try:
            if path.startswith("/api/incidents/"):
                self.app.delete_incident(unquote(path.split("/", 3)[3]))
                self._send(HTTPStatus.OK, {"ok": True})
            else:
                self._send(HTTPStatus.NOT_FOUND, {"error": "路径不存在"})
        except KeyError as exc:
            self._send(HTTPStatus.NOT_FOUND, {"error": str(exc)})
        except Exception as exc:  # noqa: BLE001 - HTTP 边界统一返回 JSON 错误
            self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})


def main() -> None:
    host = os.getenv("SRE_AGENT_WEB_HOST", "127.0.0.1")
    port = int(os.getenv("SRE_AGENT_WEB_PORT", "8765"))
    app = SREWebApp()
    RequestHandler.app = app
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"SRE Agent 工作台已启动: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nSRE Agent 工作台已停止")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
