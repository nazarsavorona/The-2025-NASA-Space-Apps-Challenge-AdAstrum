"""FastAPI backend for the AdAstrum planet visualizer."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List, Optional

from fastapi import APIRouter, BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from backend.services.dreamfusion import (
    DatasetName,
    DreamFusionError,
    DreamFusionService,
    ModelTarget,
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "planets.json"
app = FastAPI(title="AdAstrum Model Generator", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api", tags=["catalog", "generation"])


dreamfusion_service = DreamFusionService()


class DreamFusionRequest(BaseModel):
    dataset: DatasetName
    planet_name: Optional[str] = Field(
        default=None, description="Name of the planet to model; pick automatically when omitted."
    )
    host_name: Optional[str] = Field(
        default=None,
        description="Optional host star name when generating stellar models.",
    )
    workspace_name: Optional[str] = Field(
        default=None, description="Override the Stable DreamFusion workspace folder."
    )
    negative_prompt: Optional[str] = Field(
        default=None, description="Optional negative prompt passed to Stable DreamFusion."
    )
    steps: Optional[int] = Field(
        default=None, ge=50, le=50000, description="Override DreamFusion iteration count."
    )
    extra_args: List[str] = Field(
        default_factory=list, description="Additional Stable DreamFusion CLI flags."
    )
    dry_run: bool = Field(
        default=True, description="When true, skip execution and only return the prompt/command."
    )
    characteristics: Optional[dict[str, Any]] = Field(
        default=None,
        description="Override planetary parameters when the catalog entry is missing or incomplete.",
    )
    llm_model: str = Field(
        default="gpt-5-mini",
        description="OpenAI model identifier to craft the Stable DreamFusion prompt.",
    )
    target: ModelTarget = Field(
        default=ModelTarget.PLANET,
        description="Subject type to generate ('planet' or 'star').",
    )
    use_cuda: bool = Field(
        default=True,
        description="Enable CUDA acceleration (-O) when available; disable for CPU-only runs.",
    )


class DreamFusionResponse(BaseModel):
    dataset: DatasetName
    planet: dict[str, Any]
    target: ModelTarget
    prompt: str
    workspace: str
    command: List[str]
    dry_run: bool
    process_started: bool
    message: str
    model: str
    use_cuda: bool


def _read_planets() -> List[dict[str, Any]]:
    try:
        with DATA_FILE.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:  # pragma: no cover - configuration issue
        raise HTTPException(status_code=500, detail="Planet dataset not found") from exc
    except json.JSONDecodeError as exc:  # pragma: no cover - configuration issue
        raise HTTPException(status_code=500, detail="Planet dataset is malformed") from exc


@api_router.get("/planets", summary="List all planets in the dataset")
def list_planets() -> List[dict[str, Any]]:
    """Return the full planet catalog."""
    return _read_planets()


@api_router.post(
    "/dreamfusion/generate",
    summary="Generate a Stable DreamFusion 3D model for a planet or star",
    response_model=DreamFusionResponse,
)
def generate_dreamfusion(
    request: DreamFusionRequest, background_tasks: BackgroundTasks
) -> DreamFusionResponse:
    try:
        job = dreamfusion_service.prepare_job(
            dataset=request.dataset,
            planet_name=request.planet_name,
            host_name=request.host_name,
            workspace_name=request.workspace_name,
            negative_prompt=request.negative_prompt,
            steps=request.steps,
            extra_args=request.extra_args or None,
            characteristics=request.characteristics,
            llm_model=request.llm_model,
            target=request.target,
            use_cuda=request.use_cuda,
            dry_run=request.dry_run,
        )
    except DreamFusionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    process_started = False

    if not request.dry_run:
        def _launch(job) -> None:  # pragma: no cover - async path
            try:
                dreamfusion_service.run_job(job)
            except DreamFusionError as error:
                print(f"DreamFusion job failed: {error}", flush=True)

        background_tasks.add_task(_launch, job)
        process_started = True

    payload = job.to_response_payload()
    subject_label = "stellar" if request.target is ModelTarget.STAR else "planetary"
    payload.update(
        {
            "process_started": process_started,
            "message": (
                f"Dry run only; {subject_label} DreamFusion command not executed."
                if request.dry_run
                else "DreamFusion job dispatched. Monitor backend logs for progress."
            ),
        }
    )
    return DreamFusionResponse(**payload)


app.include_router(api_router)

@app.get("/", summary="Service metadata")
def root() -> dict[str, str]:
    return {
        "service": "AdAstrum DreamFusion microservice",
        "version": "0.2.0",
        "message": "Use /api/planets for catalog data and /api/dreamfusion/generate for 3D model jobs.",
    }


@app.get("/health", summary="Simple API healthcheck")
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover - manual execution convenience
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
