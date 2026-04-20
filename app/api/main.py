from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.core.config import get_settings
from app.core.logging import setup_logging
from app.core.utils import to_jsonable
from app.models.schemas import GenerateRequest, GenerateResponse, HealthResponse
from app.services.pipeline import manifest_to_response, run_generation


setup_logging()
settings = get_settings()

app = FastAPI(
    title="序蓝酱读书内容生成器",
    description="Generate title, description, narration audio, cover, subtitles, and manifest for reading content.",
    version="0.1.0",
)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.post("/generate", response_model=GenerateResponse)
def generate(request: GenerateRequest) -> GenerateResponse:
    try:
        manifest = run_generation(request, settings=settings)
        return manifest_to_response(manifest)
    except Exception as exc:
        raise HTTPException(status_code=500, detail={"message": str(exc)}) from exc


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    manifest_path = settings.jobs_dir / job_id / "manifest.json"
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail={"message": f"Job not found: {job_id}"})
    try:
        payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=500, detail={"message": "Manifest is not valid JSON."}) from exc
    return to_jsonable(payload)

