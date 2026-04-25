from __future__ import annotations

from pathlib import Path

import pytest

config_module = pytest.importorskip("gmgn_sdk.config")

ConfigError = config_module.ConfigError
load_config = config_module.load_config
redact_sensitive_mapping = config_module.redact_sensitive_mapping


pytestmark = pytest.mark.unit


def _write_env_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_load_config_applies_global_then_project_then_environment(tmp_path: Path) -> None:
    home_dir = tmp_path / "home"
    project_dir = tmp_path / "project"

    _write_env_file(
        home_dir / ".config/gmgn/.env",
        "GMGN_API_KEY=global-key\nGMGN_PRIVATE_KEY=global-private\nGMGN_HOST=https://global.example\n",
    )
    _write_env_file(
        project_dir / ".env",
        "GMGN_API_KEY=project-key\nGMGN_PRIVATE_KEY=project-private\nGMGN_HOST=https://project.example\n",
    )

    config = load_config(
        environ={"GMGN_API_KEY": "env-key"},
        home_directory=home_dir,
        project_directory=project_dir,
    )

    assert config.api_key == "env-key"
    assert config.private_key_pem == "project-private"
    assert config.host == "https://project.example"


def test_load_config_normalizes_private_key_and_defaults_host(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _write_env_file(
        project_dir / ".env",
        "GMGN_API_KEY=project-key\nGMGN_PRIVATE_KEY=line-one\\nline-two\n",
    )

    config = load_config(project_directory=project_dir)

    assert config.api_key == "project-key"
    assert config.private_key_pem == "line-one\nline-two"
    assert config.host == "https://openapi.gmgn.ai"


def test_load_config_supports_quoted_multiline_private_key(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _write_env_file(
        project_dir / ".env",
        "GMGN_API_KEY=project-key\n"
        'GMGN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n'
        "abc\n"
        '-----END PRIVATE KEY-----"\n',
    )

    config = load_config(project_directory=project_dir)

    assert config.private_key_pem == "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----"


def test_load_config_requires_private_key_for_critical_auth(tmp_path: Path) -> None:
    project_dir = tmp_path / "project"
    _write_env_file(project_dir / ".env", "GMGN_API_KEY=project-key\n")

    with pytest.raises(ConfigError, match="GMGN_PRIVATE_KEY is required"):
        load_config(project_directory=project_dir, require_private_key=True)


def test_redact_sensitive_mapping_hides_known_secret_keys() -> None:
    redacted = redact_sensitive_mapping(
        {
            "GMGN_API_KEY": "api-key",
            "GMGN_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----",
            "X-Signature": "signature-value",
            "safe": "visible",
        }
    )

    assert redacted == {
        "GMGN_API_KEY": "***REDACTED***",
        "GMGN_PRIVATE_KEY": "***REDACTED***",
        "X-Signature": "***REDACTED***",
        "safe": "visible",
    }


def test_client_accepts_loaded_config_object(tmp_path: Path) -> None:
    from gmgn_sdk import GMGNClient

    project_dir = tmp_path / "project"
    _write_env_file(
        project_dir / ".env",
        "GMGN_API_KEY=project-key\nGMGN_PRIVATE_KEY=project-private\n",
    )

    client = GMGNClient(load_config(project_directory=project_dir))

    assert client.api_key == "project-key"
    assert client.private_key == "project-private"
    assert client.host == "https://openapi.gmgn.ai"
