from pydantic import BaseModel


class ClusterSummary(BaseModel):
    fingerprint: str
    service: str
    level: str
    sample_message: str
    occurrence_count: int
    first_seen: str
    last_seen: str


class AnomalyDecision(BaseModel):
    triggered: bool
    reasons: list[str]
