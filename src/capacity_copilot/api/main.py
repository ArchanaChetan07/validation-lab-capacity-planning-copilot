from __future__ import annotations

import logging
import os
import time

from fastapi import FastAPI, Header, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from capacity_copilot.analysis.sensitivity_v2 import diagnose
from capacity_copilot.reasoning.parser import parse_query
from capacity_copilot.reasoning.reasoner import explain, ReasonerError
from capacity_copilot.reasoning.spec_builder import build_default_spec, summarize

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger("capacity_copilot")

app = FastAPI(title="Validation Lab Capacity-Planning Copilot")

# CORS: open by default so the bundled chat UI works from any deploy host.
# If you expose this API to browsers on OTHER origins in real production use,
# tighten allow_origins to your actual frontend domain(s) instead of "*".
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

REQUEST_COUNT = Counter("copilot_requests_total", "Total /ask requests")
REQUEST_ERRORS = Counter("copilot_request_errors_total", "Total /ask errors", ["kind"])
REQUEST_LATENCY = Histogram("copilot_request_latency_seconds", "Latency of /ask requests")

# Optional shared-secret auth: if COPILOT_API_KEY is set in the environment,
# /ask requires header `X-API-Key: <value>`. Unset by default so the demo
# stays open; set it before exposing this publicly if you want to control
# who can consume your Anthropic API budget.
_API_KEY = os.environ.get("COPILOT_API_KEY")


def _check_api_key(x_api_key: str | None) -> None:
    if _API_KEY and x_api_key != _API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key header.")


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)


class AskResponse(BaseModel):
    answer: str
    completion_time_hours: float
    binding_constraint: str
    improvement_pct: float
    notes: list[str] = []


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Never leak stack traces to clients; log full detail server-side instead."""
    logger.exception("Unhandled error on %s", request.url.path)
    REQUEST_ERRORS.labels(kind="unhandled").inc()
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest, x_api_key: str | None = Header(default=None)) -> AskResponse:
    _check_api_key(x_api_key)
    REQUEST_COUNT.inc()
    start = time.time()
    try:
        params = parse_query(req.query)
        spec = build_default_spec(params)

        # Trial count scales down for larger campaigns to keep request latency
        # bounded even within the clamped test_count range (see parser.py bounds).
        trials = 15 if params.test_count <= 2000 else (8 if params.test_count <= 5000 else 5)

        report = diagnose(spec, trials=trials)
        try:
            answer = explain(
                scenario_summary=summarize(params),
                baseline_completion_hours=report.baseline_p90_hours,
                binding_constraint=report.binding_constraint,
                perturbed_completion_hours=report.perturbed_p90_hours,
                improvement_pct=report.improvement_pct,
            )
        except ReasonerError as e:
            REQUEST_ERRORS.labels(kind="reasoner").inc()
            # Simulation succeeded even though the LLM explanation failed — still
            # return the grounded numbers rather than failing the whole request.
            answer = (
                f"(Explanation service unavailable: {e}) "
                f"Simulation result: binding constraint is '{report.binding_constraint}', "
                f"relieving it would reduce completion time by {report.improvement_pct:.1f}% "
                f"({report.baseline_p90_hours:.1f}h -> {report.perturbed_p90_hours:.1f}h)."
            )

        return AskResponse(
            answer=answer,
            completion_time_hours=report.baseline_p90_hours,
            binding_constraint=report.binding_constraint,
            improvement_pct=report.improvement_pct,
            notes=params.notes,
        )
    except HTTPException:
        raise
    except Exception:
        REQUEST_ERRORS.labels(kind="ask").inc()
        raise
    finally:
        REQUEST_LATENCY.observe(time.time() - start)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness check: confirms the API key is configured, without making a
    live upstream call on every probe."""
    return {"status": "ok", "llm_configured": bool(os.environ.get("ANTHROPIC_API_KEY"))}


@app.get("/metrics")
def metrics():
    """Prometheus scrape endpoint (no trailing slash required)."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Serve the chat UI at "/" — keep this mount LAST so it doesn't shadow /ask, /health, /metrics
app.mount("/", StaticFiles(directory="static", html=True), name="static")
