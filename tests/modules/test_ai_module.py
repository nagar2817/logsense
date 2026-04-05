import json

import httpx

from app.core.config import Settings
from app.modules.ai.schemas import AIAnalysisRequest
from app.modules.ai.services import AIService


def test_ai_service_uses_fallback_when_llm_disabled() -> None:
    settings = Settings(llm_enabled=False, auto_discover_modules=False)
    service = AIService(settings=settings, client=httpx.Client())

    result = service.analyze(
        AIAnalysisRequest(
            fingerprint="payment:ERROR:abc123",
            service="payment",
            level="ERROR",
            sample_message="Redis timeout after 3 attempts",
            occurrence_count=6,
            reasons=["high_frequency_errors", "repeated_failures"],
        )
    )

    assert result.severity == "high"
    assert "Redis timeout" in result.root_cause
    assert result.suggested_action != ""


def test_ai_service_parses_llm_json_response(monkeypatch) -> None:
    settings = Settings(
        llm_enabled=True,
        llm_api_key="test-key",
        auto_discover_modules=False,
    )

    class DummyResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(
                                {
                                    "title": "Redis failures detected",
                                    "root_cause": "Redis connection pool exhausted",
                                    "severity": "high",
                                    "fix_suggestion": "Increase pool size or add retry logic",
                                }
                            )
                        }
                    }
                ]
            }

    client = httpx.Client()
    monkeypatch.setattr(client, "post", lambda *args, **kwargs: DummyResponse())
    service = AIService(settings=settings, client=client)

    result = service.analyze(
        AIAnalysisRequest(
            fingerprint="payment:ERROR:abc123",
            service="payment",
            level="ERROR",
            sample_message="Redis timeout after 3 attempts",
            occurrence_count=6,
            reasons=["high_frequency_errors"],
        )
    )

    assert result.root_cause == "Redis connection pool exhausted"
    assert result.suggested_action == "Increase pool size or add retry logic"
