import json
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from ui.backend.config import TRACE_DIR
from ui.backend.models_config import get_defaults

router = APIRouter()


@router.get("/defaults")
def api_defaults():
    return get_defaults()


@router.get("/traces")
def api_traces():
    TRACE_DIR.mkdir(parents=True, exist_ok=True)
    traces = []
    for f in sorted(TRACE_DIR.glob("explainability_trace_*.json"), reverse=True):
        try:
            data = json.loads(f.read_text())
            meta = data.get("metadata", {})
            traces.append({
                "filename": f.name,
                "model_name": meta.get("model_name", "unknown"),
                "average_score": meta.get("average_score", 0),
                "timestamp": meta.get("timestamp", ""),
                "total_tasks": meta.get("total_tasks", 0),
            })
        except (json.JSONDecodeError, OSError):
            continue
    return traces


@router.get("/traces/{filename}")
def api_trace_detail(filename: str):
    if not re.match(r"^explainability_trace_\d{8}_\d{6}\.json$", filename):
        raise HTTPException(400, "Invalid filename format")
    path = TRACE_DIR / filename
    if not path.is_file():
        raise HTTPException(404, "Trace not found")
    return json.loads(path.read_text())
