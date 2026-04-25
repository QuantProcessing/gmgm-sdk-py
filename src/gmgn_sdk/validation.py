from __future__ import annotations

import re
from decimal import Decimal

from gmgn_sdk.constants import (
    CREATE_TOKEN_VALID_CHAINS,
    EVM_CHAINS,
    LIVE_NATIVE_SPEND_CAPS,
    VALID_CHAINS,
)
from gmgn_sdk.errors import GMGNValidationError

SOL_ADDRESS_RE = re.compile(r"^[1-9A-HJ-NP-Za-km-z]{32,44}$")
EVM_ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
POSITIVE_INT_RE = re.compile(r"^\d+$")


def validate_chain(chain: str, *, label: str = "chain") -> str:
    if chain not in VALID_CHAINS:
        allowed = ", ".join(sorted(VALID_CHAINS))
        raise GMGNValidationError(f'Invalid {label}: "{chain}". Must be one of: {allowed}')
    return chain


def validate_create_token_chain(chain: str) -> str:
    if chain not in CREATE_TOKEN_VALID_CHAINS:
        allowed = ", ".join(sorted(CREATE_TOKEN_VALID_CHAINS))
        raise GMGNValidationError(
            f'Invalid createToken chain: "{chain}". Must be one of: {allowed}'
        )
    return chain


def validate_address(address: str, chain: str, *, label: str) -> str:
    is_evm = chain in EVM_CHAINS
    valid = EVM_ADDRESS_RE.fullmatch(address) if is_evm else SOL_ADDRESS_RE.fullmatch(address)
    if valid is None:
        raise GMGNValidationError(f'Invalid {label} address for chain "{chain}": "{address}"')
    return address


def validate_positive_int_str(value: str, *, label: str) -> str:
    if POSITIVE_INT_RE.fullmatch(value) is None or int(value) <= 0:
        raise GMGNValidationError(f'Invalid {label}: "{value}". Must be a positive integer.')
    return value


def validate_percent(value: float, *, label: str = "percent") -> float:
    if value <= 0 or value > 100:
        raise GMGNValidationError(
            f'Invalid {label}: {value}. Must be between 0 (exclusive) and 100 (inclusive).'
        )
    return value


def validate_live_amount_cap(chain: str, amount_native: Decimal) -> Decimal:
    cap = LIVE_NATIVE_SPEND_CAPS.get(chain)
    if cap is None:
        allowed = ", ".join(sorted(LIVE_NATIVE_SPEND_CAPS))
        raise GMGNValidationError(f"Live swap caps are only defined for: {allowed}")
    if amount_native <= 0:
        raise GMGNValidationError("Live swap amount must be positive")
    cap_amount = Decimal(cap)
    if amount_native > cap_amount:
        raise GMGNValidationError(
            f"Live swap amount {amount_native} exceeds {chain} cap {cap_amount}"
        )
    return amount_native
