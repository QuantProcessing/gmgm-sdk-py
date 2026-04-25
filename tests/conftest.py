from __future__ import annotations

import os
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.helpers.sdk_contract import SDKContract, load_sdk_contract

SRC_PATH = Path(__file__).resolve().parents[1] / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))


@pytest.fixture
def sdk_contract() -> SDKContract:
    return load_sdk_contract()


@pytest.fixture
def live_enabled() -> bool:
    if os.getenv("RUN_LIVE_GMGN") != "1":
        pytest.skip("live tests require RUN_LIVE_GMGN=1")
    return True


@pytest.fixture
def required_live_env(live_enabled: bool) -> Iterator[dict[str, str]]:
    required = {
        "GMGN_API_KEY",
        "GMGN_PRIVATE_KEY",
        "GMGN_SOL_FROM_ADDRESS",
        "GMGN_BSC_FROM_ADDRESS",
        "GMGN_ETH_FROM_ADDRESS",
    }
    missing = sorted(name for name in required if not os.getenv(name))
    if missing:
        pytest.fail(f"RUN_LIVE_GMGN=1 but required env vars are missing: {', '.join(missing)}")

    yield {name: os.environ[name] for name in sorted(required)}
