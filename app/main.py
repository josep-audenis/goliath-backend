import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import audio, health, reports, runs
from app.core.config import settings


def _configure_logging() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    for noisy in ("httpx", "httpcore", "mcp.client.streamable_http"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


_configure_logging()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    # Local hackathon: allow any origin so the frontend dev server can call in.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(runs.router)
    app.include_router(reports.router)
    app.include_router(audio.router)
    return app


app = create_app()
