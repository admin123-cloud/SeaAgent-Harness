import asyncio
from sre_agent.agent.openai_compatible_llm_adapter import OpenAICompatibleLLMAdapter
from sre_agent.config.llm_settings import LLMSettings
from sre_agent.enums.decision_task import DecisionTask
from sre_agent.request.decision_request import DecisionRequest
from sre_agent.enums.decision_task import DecisionTask
from sre_agent.agent.state_manager import StateManager
from sre_agent.models.incident import Incident
from sre_agent.storage import IncidentRepository, SQLiteDatabase


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
        state = Incident(
            incident_id=incident_id,
            goal="诊断pod启动失败",
            environment={"namespace":"default","pod":"demo"}
        )
        repository.create_incident(state)
    manager = StateManager(state, repository)
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
