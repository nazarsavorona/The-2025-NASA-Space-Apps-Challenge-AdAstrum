"""FastAPI backend for the AdAstrum planet visualizer."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, List

from fastapi import APIRouter, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "data" / "planets.json"
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
TEXTURES_DIR = BASE_DIR.parent / "frontend" / "public" / "textures"

app = FastAPI(title="AdAstrum Planetarium API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount textures directory for static file serving
if TEXTURES_DIR.exists():
    app.mount("/textures", StaticFiles(directory=TEXTURES_DIR), name="textures")

api_router = APIRouter(prefix="/api", tags=["planets"])


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


app.include_router(api_router)


# Backwards compatibility for the earlier frontend that queried `/planets`
@app.get("/planets", include_in_schema=False)
def legacy_planet_list() -> List[dict[str, Any]]:
    return _read_planets()


if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST, html=True),
        name="frontend",
    )
else:
    @app.get("/", summary="Healthcheck when frontend is missing")
    def root() -> dict[str, str]:
        return {"message": "Frontend build not found. Run `npm run build` inside frontend/."}


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
