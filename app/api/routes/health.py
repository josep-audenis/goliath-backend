from fastapi import APIRouter

from app.agent.runtime import llm_enabled
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "llm_enabled": llm_enabled(),
        "llm_provider": settings.llm_provider,
        "cala_live": settings.cala_live,
        "tts_enabled": bool(settings.elevenlabs_api_key),
    }
