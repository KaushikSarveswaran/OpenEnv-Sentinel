import atexit
import signal
import subprocess
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from ui.backend.config import UI_PORT, RUN_SERVICE_PORT, STATIC_DIR


def create_app() -> FastAPI:
    app = FastAPI(title="OpenEnv Sentinel UI")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from ui.backend.routes import router
    app.include_router(router, prefix="/api")

    if STATIC_DIR.is_dir():
        app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")

    return app


app = create_app()

_run_service_proc: subprocess.Popen | None = None


def _start_run_service():
    global _run_service_proc
    _run_service_proc = subprocess.Popen(
        [sys.executable, "-m", "ui.backend.run_service"],
        cwd=str(STATIC_DIR.parent.parent.parent),
    )


def _stop_run_service():
    global _run_service_proc
    if _run_service_proc and _run_service_proc.poll() is None:
        _run_service_proc.terminate()
        try:
            _run_service_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _run_service_proc.kill()
    _run_service_proc = None


def main():
    import uvicorn

    _start_run_service()
    atexit.register(_stop_run_service)
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))

    try:
        print(f"Run service started on :{RUN_SERVICE_PORT}")
        uvicorn.run("ui.backend.app:app", host="0.0.0.0", port=UI_PORT, reload=True)
    finally:
        _stop_run_service()


if __name__ == "__main__":
    main()
