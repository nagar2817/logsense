from fastapi import APIRouter, status

from app.core.config import Settings
from app.core.responses.base import success_response
from app.modules.logs.jobs import start_log_pipeline_job
from app.modules.logs.messages import LogMessageKeys
from app.modules.logs.schemas import LogIngestRequest
from app.modules.logs.services import LogService

router = APIRouter(tags=["logs"])
settings = Settings()


def get_service() -> LogService:
    return LogService(settings=settings)


@router.post("/logs/ingest", status_code=status.HTTP_202_ACCEPTED)
def ingest_logs(payload: LogIngestRequest) -> dict[str, object]:
    record = get_service().ingest(payload)
    async_result = start_log_pipeline_job.delay({"log_id": record.id, "fingerprint": record.fingerprint})
    return success_response(
        message="Log ingested and pipeline triggered",
        message_key=LogMessageKeys.INGESTED,
        data={"log": record.model_dump(), "task_id": async_result.id},
    )


@router.get("/logs")
def list_logs() -> dict[str, object]:
    return success_response(
        message="Logs retrieved",
        message_key=LogMessageKeys.LISTED,
        data=get_service().list_logs().model_dump(),
    )
