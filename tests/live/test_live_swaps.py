from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path

import pytest

from gmgn_sdk import GMGNClient, SwapParams
from gmgn_sdk.validation import validate_live_amount_cap
from tests.helpers.contracts import LIVE_REPORT_PATH, LIVE_SPEND_CAPS

pytestmark = pytest.mark.live

LIVE_CHAINS = ("sol", "bsc", "eth")


def _append_report_line(line: str) -> None:
    LIVE_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LIVE_REPORT_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"{line}\n")


def _required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.fail(f"RUN_LIVE_GMGN=1 but {name} is missing")
    return value


def _optional_bool(name: str) -> bool | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _build_swap_params(chain: str) -> SwapParams:
    prefix = f"GMGN_{chain.upper()}"
    raw_amount = _required_env(f"{prefix}_INPUT_AMOUNT")
    declared_native_amount = _required_env(f"{prefix}_INPUT_AMOUNT_NATIVE")
    validate_live_amount_cap(chain, Decimal(declared_native_amount))

    return SwapParams(
        chain=chain,
        from_address=_required_env(f"{prefix}_FROM_ADDRESS"),
        input_token=_required_env(f"{prefix}_INPUT_TOKEN"),
        output_token=_required_env(f"{prefix}_OUTPUT_TOKEN"),
        input_amount=raw_amount,
        slippage=float(os.getenv(f"{prefix}_SLIPPAGE", "0.01")),
        auto_slippage=_optional_bool(f"{prefix}_AUTO_SLIPPAGE"),
        min_output_amount=os.getenv(f"{prefix}_MIN_OUTPUT_AMOUNT"),
        is_anti_mev=_optional_bool(f"{prefix}_IS_ANTI_MEV"),
        priority_fee=os.getenv(f"{prefix}_PRIORITY_FEE"),
        tip_fee=os.getenv(f"{prefix}_TIP_FEE"),
        auto_tip_fee=_optional_bool(f"{prefix}_AUTO_TIP_FEE"),
        max_auto_fee=os.getenv(f"{prefix}_MAX_AUTO_FEE"),
        gas_price=os.getenv(f"{prefix}_GAS_PRICE"),
        max_fee_per_gas=os.getenv(f"{prefix}_MAX_FEE_PER_GAS"),
        max_priority_fee_per_gas=os.getenv(f"{prefix}_MAX_PRIORITY_FEE_PER_GAS"),
    )


def test_live_swap_harness_declares_consensus_spend_caps(live_enabled: bool) -> None:
    assert LIVE_SPEND_CAPS == {
        "sol": "0.1 SOL",
        "eth": "0.01 ETH",
        "bsc": "0.01 BNB",
    }


def test_live_swap_harness_uses_redacted_report_path(live_enabled: bool) -> None:
    assert Path(".omx/reports/gmgn-sdk-live-verification.md") == LIVE_REPORT_PATH


def test_live_swap_harness_requires_core_credentials(required_live_env: dict[str, str]) -> None:
    assert sorted(required_live_env) == [
        "GMGN_API_KEY",
        "GMGN_BSC_FROM_ADDRESS",
        "GMGN_ETH_FROM_ADDRESS",
        "GMGN_PRIVATE_KEY",
        "GMGN_SOL_FROM_ADDRESS",
    ]


@pytest.mark.parametrize("chain", LIVE_CHAINS)
def test_live_swap_executes_real_gmgn_swap(
    chain: str,
    required_live_env: dict[str, str],
) -> None:
    params = _build_swap_params(chain)
    client = GMGNClient(
        api_key=required_live_env["GMGN_API_KEY"],
        private_key=required_live_env["GMGN_PRIVATE_KEY"],
    )

    _append_report_line(f"## Live swap: {chain}")
    _append_report_line(f"- Cap: {LIVE_SPEND_CAPS[chain]}")
    _append_report_line("- createToken: implemented but not live-tested in this acceptance pass")

    try:
        result = client.swap(params)
    except Exception as error:
        _append_report_line(f"- Status: failed ({type(error).__name__}: {error})")
        raise
    finally:
        client.close()

    _append_report_line(f"- Status: success ({type(result).__name__})")
    assert result is not None
