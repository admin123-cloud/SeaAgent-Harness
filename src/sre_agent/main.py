from sre_agent.enums.incident_status import IncidentStatus
from sre_agent.models.incident_state import IncidentState


def main():
    """
    本地调试方法
    :return:
    """

    state = IncidentState(
        incident_id="incident-001",
        goal="诊断 Pod 启动失败",
        environment={"namespace": "default", "pod": "demo"},
    )

    assert state.status == IncidentStatus.CREATED
    assert state.stage is None
    assert state.iteration == 0

    payload = state.model_dump(mode="json")
    restored = IncidentState.model_validate(payload)

    assert restored.incident_id == "incident-001"
    print(state)


if __name__ == "__main__":
    main()