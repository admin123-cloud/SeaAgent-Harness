import asyncio
from sre_agent.enums.incident_status import IncidentStatus
from src.sre_agent.agent.openai_compatible_llm_adapter import OpenAICompatibleLLMAdapter
from src.sre_agent.config.llm_settings import LLMSettings
from src.sre_agent.enums.decision_task import DecisionTask
from src.sre_agent.request.decision_request import DecisionRequest
from src.sre_agent.enums.decision_task import DecisionTask
from src.sre_agent.agent.state_manager import StateManager
from src.sre_agent.models.incident import Incident
from src.sre_agent.storage import IncidentRepository, SQLiteDatabase


async def main():
    """
    本地调试方法
    :return:
    """
    database = SQLiteDatabase()
    repository = IncidentRepository(database)
    repository.initialize()

    incident_id = "incident-001"
    state = repository.get_incident(incident_id)

    if state is None:
    # 创建 事件
        state = Incident(
            incident_id=incident_id,
            goal="诊断pod启动失败",
            environment={"namespace":"default","pod":"demo"}
        )
        repository.create_incident(state)
    # 创建状态数据 默认CREATED
    manager = StateManager(state, repository)
    if state.status == IncidentStatus.CREATED:
        manager.transition_to(IncidentStatus.PLANNING)
    elif state.status == IncidentStatus.PLANNING:
        manager.transition_to(IncidentStatus.DIAGNOSING)
    settings = LLMSettings()
    adapter = OpenAICompatibleLLMAdapter(settings)

    try:
        request = DecisionRequest(
            task= DecisionTask.DIAGNOSE,
            incident_id=incident_id,
            goal= state.goal,
            context= {
                "environment": state.environment,
                "incident_status": state.status.value,
                "kubernetes_observations": {
                    "pod_phase": None,
                    "events": [],
                    "container_statuses": [],
                },
                "evidence":[
                    {
                        "evidence_id":evidence_item.evidence_id,
                        "kind":evidence_item.kind,
                        "summary":evidence_item.summary,
                    }
                    for evidence_item in state.evidence
                ],
            },
        )
        response = await adapter.decide(request)
        print(response.model_dump_json(indent=2, ensure_ascii=False))

    finally:
        await adapter.aclose()

if __name__ == "__main__":
    asyncio.run(main())
