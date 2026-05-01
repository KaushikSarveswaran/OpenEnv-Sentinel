import asyncio
import os
import signal
import subprocess
import sys
from pathlib import Path

from ui.backend.config import PROJECT_ROOT, TRACE_DIR
from ui.backend.models_config import ModelQueueItem


class InferenceRunner:
    def __init__(self):
        self._process: subprocess.Popen | None = None
        self._current_model_index: int = 0
        self._total_models: int = 0
        self._status: str = "idle"  # idle | running | completed | failed | cancelled
        self._output_lines: list[str] = []
        self._lock = asyncio.Lock()

    @property
    def status(self) -> dict:
        return {
            "status": self._status,
            "model_index": self._current_model_index,
            "total_models": self._total_models,
            "output_lines": len(self._output_lines),
        }

    def _build_env(self, item: ModelQueueItem, env_url: str) -> dict:
        env = os.environ.copy()
        env["ENV_URL"] = env_url
        env["TRACE_DIR"] = str(TRACE_DIR)

        # Set ALL provider env vars to empty so load_dotenv() in the
        # subprocess won't restore them from .env (it skips existing keys).
        for key in (
            "AZURE_OPENAI_API_KEY", "AZURE_OPENAI_ENDPOINT",
            "AZURE_OPENAI_DEPLOYMENT", "AZURE_OPENAI_API_VERSION",
            "OPENROUTER_API_KEY", "OpenRouter_API",
            "API_BASE_URL",
        ):
            env[key] = ""

        if item.provider == "azure":
            env["AZURE_OPENAI_ENDPOINT"] = item.config.get("endpoint", "")
            env["AZURE_OPENAI_DEPLOYMENT"] = item.model_name
            env["AZURE_OPENAI_API_KEY"] = item.config.get("api_key", "")
            env["AZURE_OPENAI_API_VERSION"] = item.config.get("api_version", "2025-04-01-preview")
            env["MODEL_NAME"] = item.model_name
        elif item.provider == "openrouter":
            env["OPENROUTER_API_KEY"] = item.config.get("api_key", "")
            env["MODEL_NAME"] = item.model_name
            env["API_BASE_URL"] = "https://openrouter.ai/api/v1"
            if item.config.get("site_url"):
                env["OPENROUTER_SITE_URL"] = item.config["site_url"]
            if item.config.get("site_name"):
                env["OPENROUTER_SITE_NAME"] = item.config["site_name"]
        return env

    async def run_models(self, models: list[ModelQueueItem], env_url: str):
        async with self._lock:
            self._total_models = len(models)
            self._status = "running"
            self._output_lines = []

        TRACE_DIR.mkdir(parents=True, exist_ok=True)

        for i, item in enumerate(models):
            async with self._lock:
                if self._status == "cancelled":
                    break
                self._current_model_index = i

            header = f"\n{'='*50}\nRunning model {i+1}/{len(models)}: {item.model_name}\n{'='*50}\n"
            self._output_lines.append(header)

            env = self._build_env(item, env_url)
            inference_path = str(PROJECT_ROOT / "inference.py")

            try:
                self._process = subprocess.Popen(
                    [sys.executable, inference_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    env=env,
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    bufsize=1,
                )

                for line in iter(self._process.stdout.readline, ""):
                    self._output_lines.append(line)
                    await asyncio.sleep(0)

                self._process.wait()
                exit_code = self._process.returncode
                if exit_code != 0:
                    self._output_lines.append(f"\n[Process exited with code {exit_code}]\n")
            except Exception as e:
                self._output_lines.append(f"\n[Error: {e}]\n")
            finally:
                self._process = None

            async with self._lock:
                if self._status == "cancelled":
                    break

        async with self._lock:
            if self._status != "cancelled":
                self._status = "completed"

    def cancel(self):
        self._status = "cancelled"
        if self._process and self._process.poll() is None:
            self._process.send_signal(signal.SIGTERM)
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()

    def get_output_since(self, offset: int) -> list[str]:
        return self._output_lines[offset:]


runner = InferenceRunner()
