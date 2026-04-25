"""Configuration loading and secret redaction for GMGN SDK."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

DEFAULT_HOST = "https://openapi.gmgn.ai"
REDACTED = "***REDACTED***"
PRIVATE_KEY_REQUIRED_MSG = (
    "GMGN_PRIVATE_KEY is required for critical-auth commands "
    "(swap, order, and follow-wallet commands)"
)
_SENSITIVE_MAPPING_KEYS = {
    "gmgn_api_key",
    "gmgn_private_key",
    "x-apikey",
    "x-signature",
}


class ConfigError(ValueError):
    """Raised when the runtime configuration is incomplete or invalid."""


@dataclass(frozen=True)
class GMGNConfig:
    api_key: str
    host: str = DEFAULT_HOST
    private_key_pem: str | None = None

    @property
    def private_key(self) -> str | None:
        return self.private_key_pem


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0
    while index < len(lines):
        raw_line = lines[index]
        index += 1
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if value[:1] in {"'", '"'}:
            quote = value[0]
            value = value[1:]
            collected = [value]
            while collected[-1].endswith(quote) is False and index < len(lines):
                collected.append(lines[index])
                index += 1
            value = "\n".join(collected)
            if value.endswith(quote):
                value = value[:-1]
        else:
            value = value.strip('"').strip("'")
        values[key.strip()] = value
    return values


def load_env_values(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
) -> dict[str, str]:
    env = dict(environ if environ is not None else os.environ)
    base_home = home if home is not None else Path.home()
    base_cwd = cwd if cwd is not None else Path.cwd()

    values: dict[str, str] = {}
    values.update(parse_env_file(base_home / ".config" / "gmgn" / ".env"))
    values.update(parse_env_file(base_cwd / ".env"))
    values.update(env)
    return values


def get_config(
    require_private_key: bool = False,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    cwd: Path | None = None,
) -> GMGNConfig:
    values = load_env_values(environ=environ, home=home, cwd=cwd)
    api_key = values.get("GMGN_API_KEY")
    if not api_key:
        raise ConfigError("GMGN_API_KEY is required. Set it in your .env file or environment.")

    raw_private_key = values.get("GMGN_PRIVATE_KEY")
    private_key_pem = raw_private_key.replace("\\n", "\n") if raw_private_key else None
    if require_private_key and not private_key_pem:
        raise ConfigError(PRIVATE_KEY_REQUIRED_MSG)

    host = values.get("GMGN_HOST") or DEFAULT_HOST
    return GMGNConfig(api_key=api_key, private_key_pem=private_key_pem, host=host)


def load_config(
    *,
    require_private_key: bool = False,
    environ: Mapping[str, str] | None = None,
    home_directory: Path | None = None,
    project_directory: Path | None = None,
) -> GMGNConfig:
    """Load config with explicit global/project directory override hooks for tests."""

    return get_config(
        require_private_key=require_private_key,
        environ=environ,
        home=home_directory,
        cwd=project_directory,
    )


def redact_sensitive_mapping(values: Mapping[str, str]) -> dict[str, str]:
    """Redact sensitive config and auth values for logs and reports."""

    return {
        key: REDACTED if key.lower() in _SENSITIVE_MAPPING_KEYS else value
        for key, value in values.items()
    }
