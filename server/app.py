"""FastAPI application for the Sentinel Environment."""

from openenv.core.env_server import create_app

from models import SentinelAction, SentinelObservation
from server.sentinel_environment import SentinelEnvironment

app = create_app(
    SentinelEnvironment,
    SentinelAction,
    SentinelObservation,
    env_name="sentinel_env",
)


def main():
    """Entry point for direct execution."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
