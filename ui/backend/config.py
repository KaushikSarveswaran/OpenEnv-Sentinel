import os
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / ".env")

UI_PORT = int(os.getenv("UI_PORT", "8501"))
RUN_SERVICE_PORT = int(os.getenv("RUN_SERVICE_PORT", "8502"))
STATIC_DIR = Path(__file__).resolve().parent / "static"
TRACE_DIR = PROJECT_ROOT / "traces"
