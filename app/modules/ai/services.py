import json

import httpx

from app.core.config import Settings
from app.modules.ai.schemas import AIAnalysisRequest, AIAnalysisResult


class AIService:
    def __init__(self, *, settings: Settings, client: httpx.Client | None = None) -> None:
        self.settings = settings
        self.client = client or httpx.Client(timeout=settings.llm_timeout_seconds)

    def fallback_analysis(self, payload: AIAnalysisRequest) -> AIAnalysisResult:
        severity = "high" if payload.level == "ERROR" and payload.occurrence_count >= 5 else "medium"
        return AIAnalysisResult(
            fingerprint=payload.fingerprint,
            title=f"{payload.service.title()} failures detected",
            root_cause=payload.sample_message,
            severity=severity,
            suggested_action="Inspect connection limits, add retries, and verify downstream health.",
        )

    def analyze(self, payload: AIAnalysisRequest) -> AIAnalysisResult:
        if not self.settings.llm_enabled or not self.settings.llm_api_key:
            return self.fallback_analysis(payload)

        response = self.client.post(
            f"{self.settings.llm_base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.settings.llm_api_key}"},
            json={
                "model": self.settings.llm_model,
                "temperature": 0,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Return strict JSON with title, root_cause, severity, and fix_suggestion. "
                            "Severity must be low, medium, or high."
                        ),
                    },
                    {"role": "user", "content": payload.model_dump_json()},
                ],
            },
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
        return AIAnalysisResult(
            fingerprint=payload.fingerprint,
            title=parsed["title"],
            root_cause=parsed["root_cause"],
            severity=parsed["severity"],
            suggested_action=parsed["fix_suggestion"],
        )
