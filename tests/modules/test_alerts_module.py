from app.modules.alerts.interfaces import AlertDispatcher


def test_alert_dispatcher_contract_is_placeholder_only() -> None:
    assert hasattr(AlertDispatcher, "send_incident")
