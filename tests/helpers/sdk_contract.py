from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Any

import pytest


@dataclass
class SDKContract:
    module: Any
    client_type: type[Any]


def load_sdk_contract() -> SDKContract:
    try:
        module = importlib.import_module("gmgn_sdk")
    except ModuleNotFoundError as exc:
        pytest.skip(f"gmgn_sdk package is not present in this workspace snapshot: {exc}")

    client_type = getattr(module, "GMGNClient", None)
    if client_type is None:
        pytest.skip("gmgn_sdk.GMGNClient is not available yet")

    return SDKContract(module=module, client_type=client_type)


def require_public_method(contract: SDKContract, name: str) -> None:
    if not hasattr(contract.client_type, name):
        pytest.fail(f"GMGNClient is missing required public method {name!r}")

