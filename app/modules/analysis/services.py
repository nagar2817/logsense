from app.core.config import Settings
from app.modules.analysis.schemas import AnomalyDecision, ClusterSummary
from app.modules.logs.repository import LogRepository


class AnalysisService:
    def __init__(self, *, settings: Settings) -> None:
        self.settings = settings
        self.log_repository = LogRepository(settings=settings)

    def build_cluster_summary(self, *, log_id: str | None, fingerprint: str) -> ClusterSummary:
        records = self.log_repository.list_by_fingerprint(fingerprint=fingerprint, limit=100)
        latest = records[0]
        oldest = records[-1]
        return ClusterSummary(
            fingerprint=fingerprint,
            service=latest.service,
            level=latest.level,
            sample_message=latest.message,
            occurrence_count=len(records),
            first_seen=oldest.timestamp,
            last_seen=latest.timestamp,
        )

    def detect_anomaly(self, summary: ClusterSummary) -> AnomalyDecision:
        reasons: list[str] = []
        if summary.level == "ERROR" and summary.occurrence_count >= self.settings.error_frequency_threshold:
            reasons.append("high_frequency_errors")
        if summary.occurrence_count >= int(self.settings.error_frequency_threshold * self.settings.spike_multiplier):
            reasons.append("sudden_spike")
        if summary.level in {"ERROR", "CRITICAL"} and summary.occurrence_count >= 2:
            reasons.append("repeated_failures")
        return AnomalyDecision(triggered=bool(reasons), reasons=reasons)
