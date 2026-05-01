import asyncio
import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from ui.backend.config import RUN_SERVICE_PORT
from ui.backend.models_config import RunRequest
from ui.backend.runner import runner

app = FastAPI(title="OpenEnv Sentinel Run Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/run")
async def api_run(req: RunRequest):
    if runner.status["status"] == "running":
        raise HTTPException(400, "A run is already in progress")
    if not req.models:
        raise HTTPException(400, "No models provided")

    asyncio.create_task(runner.run_models(req.models, req.env_url))
    return {"status": "started", "total_models": len(req.models)}


@app.get("/api/run/stream")
async def api_run_stream():
    async def event_generator():
        offset = 0
        while True:
            lines = runner.get_output_since(offset)
            if lines:
                offset += len(lines)
                for line in lines:
                    data = json.dumps({"type": "output", "data": line.rstrip("\n")})
                    yield f"data: {data}\n\n"

            status = runner.status
            data = json.dumps({"type": "status", "data": status})
            yield f"data: {data}\n\n"

            if status["status"] in ("completed", "failed", "cancelled", "idle"):
                if not lines:
                    break

            await asyncio.sleep(0.3)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/run/cancel")
def api_run_cancel():
    if runner.status["status"] != "running":
        raise HTTPException(400, "No run in progress")
    runner.cancel()
    return {"status": "cancelled"}


@app.get("/api/run/status")
def api_run_status():
    return runner.status


def main():
    import uvicorn
    uvicorn.run(
        "ui.backend.run_service:app",
        host="0.0.0.0",
        port=RUN_SERVICE_PORT,
        reload=True,
    )


if __name__ == "__main__":
    main()
