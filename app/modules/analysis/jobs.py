from typing import Any

from celery import Task

from app.core.base_job import BaseJob
from app.core.celery_app import celery_app
from app.core.config import Settings
from app.modules.analysis.schemas import ClusterSummary
from app.modules.analysis.services import AnalysisService

settings = Settings()


class ClusterLogsJob(BaseJob):
    name = "analysis.cluster_logs"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AnalysisService(settings=settings)
        summary = service.build_cluster_summary(
            log_id=payload.get("log_id"),
            fingerprint=str(payload["fingerprint"]),
        )
        detect_anomalies_job.delay({"cluster": summary.model_dump()})
        return {"message_key": "analysis.clustered", "cluster": summary.model_dump()}


class DetectAnomaliesJob(BaseJob):
    name = "analysis.detect_anomalies"

    def run(self, payload: dict[str, Any]) -> dict[str, Any]:
        service = AnalysisService(settings=settings)
        cluster = ClusterSummary.model_validate(payload["cluster"])
        decision = service.detect_anomaly(cluster)
        if decision.triggered:
            from app.modules.ai.jobs import ai_analysis_job

            ai_analysis_job.delay({"cluster": cluster.model_dump(), "reasons": decision.reasons})
        return {
            "message_key": "analysis.anomaly_detected" if decision.triggered else "analysis.no_anomaly",
            "cluster": cluster.model_dump(),
            "decision": decision.model_dump(),
        }


cluster_job = ClusterLogsJob(celery_app=celery_app)
detect_job = DetectAnomaliesJob(celery_app=celery_app)


@celery_app.task(bind=True, name="analysis.cluster_logs")
def cluster_logs_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return cluster_job.execute(payload)


@celery_app.task(bind=True, name="analysis.detect_anomalies")
def detect_anomalies_job(self: Task, payload: dict[str, Any]) -> dict[str, Any]:
    return detect_job.execute(payload)
