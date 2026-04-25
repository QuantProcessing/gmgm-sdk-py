from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, cast


def _to_payload_value(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {
            key: _to_payload_value(item)
            for key, item in asdict(value).items()
            if item is not None
        }
    if isinstance(value, Mapping):
        return {
            str(key): _to_payload_value(item)
            for key, item in value.items()
            if item is not None
        }
    if isinstance(value, list):
        return [_to_payload_value(item) for item in value if item is not None]
    if isinstance(value, tuple):
        return [_to_payload_value(item) for item in value if item is not None]
    return value


@dataclass(slots=True)
class PayloadModel:
    def to_payload(self) -> dict[str, Any]:
        return cast(dict[str, Any], _to_payload_value(self))


@dataclass(slots=True, frozen=True)
class MethodParitySpec:
    name: str
    http_method: str
    path: str
    auth_mode: str


@dataclass(slots=True)
class StrategyConditionOrder(PayloadModel):
    order_type: str
    side: str
    sell_ratio: str
    price_scale: str | None = None
    drawdown_rate: str | None = None


@dataclass(slots=True)
class SwapParams(PayloadModel):
    chain: str
    from_address: str
    input_token: str
    output_token: str
    input_amount: str
    swap_mode: str | None = None
    input_amount_bps: str | None = None
    output_amount: str | None = None
    slippage: float | None = None
    auto_slippage: bool | None = None
    min_output_amount: str | None = None
    is_anti_mev: bool | None = None
    priority_fee: str | None = None
    tip_fee: str | None = None
    auto_tip_fee: bool | None = None
    max_auto_fee: str | None = None
    gas_price: str | None = None
    max_fee_per_gas: str | None = None
    max_priority_fee_per_gas: str | None = None
    condition_orders: list[StrategyConditionOrder] | None = None
    sell_ratio_type: str | None = None


@dataclass(slots=True)
class MultiSwapParams(PayloadModel):
    chain: str
    accounts: list[str]
    input_token: str
    output_token: str
    input_amount: dict[str, str] | None = None
    input_amount_bps: dict[str, str] | None = None
    output_amount: dict[str, str] | None = None
    swap_mode: str | None = None
    slippage: float | None = None
    auto_slippage: bool | None = None
    is_anti_mev: bool | None = None
    priority_fee: str | None = None
    tip_fee: str | None = None
    auto_tip_fee: bool | None = None
    max_auto_fee: str | None = None
    gas_price: str | None = None
    max_fee_per_gas: str | None = None
    max_priority_fee_per_gas: str | None = None
    condition_orders: list[StrategyConditionOrder] | None = None
    sell_ratio_type: str | None = None


@dataclass(slots=True)
class StrategyCreateParams(PayloadModel):
    chain: str
    from_address: str
    base_token: str
    quote_token: str
    order_type: str
    sub_order_type: str
    check_price: str
    open_price: str | None = None
    amount_in: str | None = None
    amount_in_percent: str | None = None
    limit_price_mode: str | None = None
    price_gap_ratio: str | None = None
    expire_in: int | None = None
    sell_ratio_type: str | None = None
    slippage: float | None = None
    auto_slippage: bool | None = None
    fee: str | None = None
    gas_price: str | None = None
    max_fee_per_gas: str | None = None
    max_priority_fee_per_gas: str | None = None
    is_anti_mev: bool | None = None
    anti_mev_mode: str | None = None
    priority_fee: str | None = None
    tip_fee: str | None = None
    custom_rpc: str | None = None


@dataclass(slots=True)
class StrategyCancelParams(PayloadModel):
    chain: str
    from_address: str
    order_id: str
    order_type: str | None = None
    close_sell_model: str | None = None


@dataclass(slots=True)
class TokenSignalGroup(PayloadModel):
    signal_type: list[int] | None = None
    mc_min: int | None = None
    mc_max: int | None = None
    trigger_mc_min: int | None = None
    trigger_mc_max: int | None = None
    total_fee_min: int | None = None
    total_fee_max: int | None = None
    min_create_or_open_ts: str | None = None
    max_create_or_open_ts: str | None = None


@dataclass(slots=True)
class CreateTokenParams(PayloadModel):
    chain: str
    dex: str
    from_address: str
    name: str
    symbol: str
    buy_amt: str
    image: str | None = None
    image_url: str | None = None
    website: str | None = None
    twitter: str | None = None
    telegram: str | None = None
    slippage: float | None = None
    auto_slippage: bool | None = None
    priority_fee: str | None = None
    tip_fee: str | None = None
    gas_price: str | None = None
    max_priority_fee_per_gas: str | None = None
    max_fee_per_gas: str | None = None
    is_anti_mev: bool | None = None
    anti_mev_mode: str | None = None
