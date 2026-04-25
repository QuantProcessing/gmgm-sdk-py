from __future__ import annotations

import pytest

from tests.helpers.contracts import LIVE_REPORT_PATH, LIVE_SPEND_CAPS, METHOD_CONTRACTS

pytestmark = pytest.mark.unit


def test_method_contract_table_covers_all_expected_sdk_methods() -> None:
    assert len(METHOD_CONTRACTS) == 27


def test_method_contract_table_uses_unique_method_names() -> None:
    names = [contract.name for contract in METHOD_CONTRACTS]
    assert len(names) == len(set(names))


def test_method_contract_table_uses_only_known_auth_modes() -> None:
    assert {contract.auth_mode for contract in METHOD_CONTRACTS} == {"normal", "critical"}


def test_live_spend_caps_match_consensus_limits() -> None:
    assert LIVE_SPEND_CAPS == {
        "sol": "0.1 SOL",
        "eth": "0.01 ETH",
        "bsc": "0.01 BNB",
    }


def test_live_report_path_points_to_redacted_omx_artifact() -> None:
    assert LIVE_REPORT_PATH.as_posix() == ".omx/reports/gmgn-sdk-live-verification.md"

