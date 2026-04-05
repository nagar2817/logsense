from pydantic import BaseModel


class AIAnalysisRequest(BaseModel):
    fingerprint: str
    service: str
    level: str
    sample_message: str
    occurrence_count: int
    reasons: list[str]


class AIAnalysisResult(BaseModel):
    fingerprint: str
    title: str
    root_cause: str
    severity: str
    suggested_action: str
