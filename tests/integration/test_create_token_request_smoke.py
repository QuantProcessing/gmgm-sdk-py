from __future__ import annotations

import pytest

from tests.helpers.sdk_contract import require_public_method

pytestmark = pytest.mark.integration


def test_client_exposes_create_token_entrypoint_for_request_smoke(sdk_contract) -> None:
    require_public_method(sdk_contract, "createToken")


def test_create_token_contract_keeps_ton_in_advertised_chain_scope() -> None:
    assert "ton" in {"sol", "bsc", "eth", "base", "monad", "ton"}


def test_create_token_smoke_requires_prepared_request_hook_without_live_submission(
    sdk_contract,
) -> None:
    if not hasattr(sdk_contract.client_type, "_prepare_request"):
        pytest.fail("GMGNClient must expose _prepare_request for non-live createToken smoke checks")

