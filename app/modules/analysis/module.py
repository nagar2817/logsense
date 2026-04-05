from fastapi import APIRouter

from app.modules.analysis.jobs import cluster_logs_job, detect_anomalies_job


class Module:
    name = "analysis"

    def register_routes(self) -> APIRouter:
        return APIRouter(tags=["analysis"])

    def register_tasks(self) -> list[object]:
        return [cluster_logs_job, detect_anomalies_job]
