from app.core.config import Settings
from app.core.database import initialize_database
from app.modules.analysis.schemas import ClusterSummary
from app.modules.analysis.services import AnalysisService
from app.modules.logs.repository import LogRepository


def test_analysis_service_clusters_similar_logs_and_detects_frequency(tmp_path) -> None:
    settings = Settings(
        sqlite_database_path=str(tmp_path / "logsense.db"),
        error_frequency_threshold=3,
        auto_discover_modules=False,
    )
    initialize_database(settings=settings)
    logs = LogRepository(settings=settings)
    for index in range(3):
        logs.create_log(
            service="payment",
            level="ERROR",
            message=f"Redis timeout after {index + 1} attempts",
            fingerprint="payment:ERROR:redis-timeout",
            timestamp=f"2026-04-05T10:0{index}:00+00:00",
        )

    service = AnalysisService(settings=settings)
    summary = service.build_cluster_summary(log_id=None, fingerprint="payment:ERROR:redis-timeout")
    decision = service.detect_anomaly(summary)

    assert isinstance(summary, ClusterSummary)
    assert summary.occurrence_count == 3
    assert decision.triggered is True
    assert "high_frequency_errors" in decision.reasons
