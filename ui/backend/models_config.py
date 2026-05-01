import os
from dataclasses import dataclass, field

from pydantic import BaseModel


OPENROUTER_FREE_MODELS = [
    {"id": "google/gemma-4-31b-it:free", "name": "Google: Gemma 4 31B", "context": "262K"},
    {"id": "google/gemma-4-26b-a4b-it:free", "name": "Google: Gemma 4 26B A4B", "context": "262K"},
    {"id": "qwen/qwen3-coder:free", "name": "Qwen: Qwen3 Coder 480B A35B", "context": "262K"},
    {"id": "qwen/qwen3-next-80b-a3b-instruct:free", "name": "Qwen: Qwen3 Next 80B A3B", "context": "262K"},
    {"id": "nvidia/nemotron-3-super-120b-a12b:free", "name": "NVIDIA: Nemotron 3 Super", "context": "262K"},
    {"id": "inclusionai/ling-2.6-1t:free", "name": "inclusionAI: Ling-2.6-1T", "context": "262K"},
    {"id": "inclusionai/ling-2.6-flash:free", "name": "inclusionAI: Ling-2.6-flash", "context": "262K"},
    {"id": "meta-llama/llama-3.3-70b-instruct:free", "name": "Meta: Llama 3.3 70B Instruct", "context": "65K"},
    {"id": "openai/gpt-oss-120b:free", "name": "OpenAI: gpt-oss-120b", "context": "131K"},
    {"id": "openai/gpt-oss-20b:free", "name": "OpenAI: gpt-oss-20b", "context": "131K"},
    {"id": "nousresearch/hermes-3-llama-3.1-405b:free", "name": "Nous: Hermes 3 405B Instruct", "context": "131K"},
    {"id": "minimax/minimax-m2.5:free", "name": "MiniMax: MiniMax M2.5", "context": "196K"},
]


class AzureOpenAIConfig(BaseModel):
    provider: str = "azure"
    endpoint: str = ""
    deployment: str = ""
    api_key: str = ""
    api_version: str = "2025-04-01-preview"


class OpenRouterConfig(BaseModel):
    provider: str = "openrouter"
    api_key: str = ""
    model_id: str = "google/gemma-4-31b-it:free"
    site_url: str = ""
    site_name: str = ""


class ModelQueueItem(BaseModel):
    provider: str  # "azure" or "openrouter"
    model_name: str
    config: dict


class RunRequest(BaseModel):
    models: list[ModelQueueItem]
    env_url: str = "http://localhost:8000"


def get_defaults() -> dict:
    env_model = os.getenv("MODEL_NAME", "")
    default_openrouter_model = "google/gemma-4-31b-it:free"
    if env_model and any(m["id"] == env_model for m in OPENROUTER_FREE_MODELS):
        default_openrouter_model = env_model

    return {
        "azure": {
            "endpoint": os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            "deployment": os.getenv("AZURE_OPENAI_DEPLOYMENT", ""),
            "api_key": os.getenv("AZURE_OPENAI_API_KEY", ""),
            "api_version": os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview"),
        },
        "openrouter": {
            "api_key": os.getenv("OPENROUTER_API_KEY", "") or os.getenv("OpenRouter_API", ""),
            "model_id": default_openrouter_model,
            "site_url": os.getenv("OPENROUTER_SITE_URL", ""),
            "site_name": os.getenv("OPENROUTER_SITE_NAME", ""),
            "free_models": OPENROUTER_FREE_MODELS,
        },
        "env_url": os.getenv("ENV_URL", "http://localhost:8000"),
    }
