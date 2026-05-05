from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required local configuration is missing."""


@dataclass(frozen=True)
class Config:
    bearer_token: str
    xai_api_key: str | None = None
    xai_model: str = "grok-4.20-0309-reasoning"


def _parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip("'").strip('"')
        values[key.strip()] = value
    return values


def load_config(
    env_path: Path | str = ".env",
    environ: dict[str, str] | None = None,
    require_bearer: bool = True,
) -> Config:
    import os

    env = dict(os.environ if environ is None else environ)
    file_values = _parse_env_file(Path(env_path))
    bearer_token = env.get("X_BEARER_TOKEN") or file_values.get("X_BEARER_TOKEN")
    xai_api_key = env.get("XAI_API_KEY") or file_values.get("XAI_API_KEY")
    xai_model = env.get("XAI_MODEL") or file_values.get("XAI_MODEL") or "grok-4.20-0309-reasoning"

    if require_bearer and not bearer_token:
        raise ConfigError("Missing X_BEARER_TOKEN. Add it to .env or export it in the shell.")

    return Config(bearer_token=bearer_token or "", xai_api_key=xai_api_key, xai_model=xai_model)
