from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import routes_forecasts, routes_sources, routes_summaries, routes_trends
from backend.app.core.database import init_db
from backend.app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title="Real-Time Tech Intelligence Copilot",
    description="Live technology and company trend intelligence with Kafka, LangGraph, TimesFM, and LLM summaries.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_trends.router)
app.include_router(routes_sources.router)
app.include_router(routes_summaries.router)
app.include_router(routes_forecasts.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
