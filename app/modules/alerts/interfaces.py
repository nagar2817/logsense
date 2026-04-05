from typing import Protocol


class AlertDispatcher(Protocol):
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None: ...


class EmailAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Email alert delivery is out of scope for the MVP")


class SlackAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Slack alert delivery is out of scope for the MVP")


class WebhookAlertDispatcher:
    def send_incident(self, *, incident_id: str, severity: str, summary: str) -> None:
        raise NotImplementedError("Webhook alert delivery is out of scope for the MVP")
