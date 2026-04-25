from __future__ import annotations

import json
import os
import sys
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

import httpx

from gmgn_sdk.auth import QueryValue, build_signature_message, build_url, serialize_body
from gmgn_sdk.config import GMGNConfig, get_config
from gmgn_sdk.constants import (
    CRITICAL_AUTH,
    DEFAULT_HOST,
    DEFAULT_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS,
    DEFAULT_TIMEOUT_SECONDS,
    METHOD_PARITY_SPECS,
    NORMAL_AUTH,
    RATE_LIMIT_RETRY_BUFFER_MS,
    REDACTED_HEADER_NAMES,
    REDACTION_PLACEHOLDER,
    TRENCHES_PLATFORMS,
    TRENCHES_QUOTE_ADDRESS_TYPES,
)
from gmgn_sdk.errors import (
    GMGNAPIError,
    GMGNConfigurationError,
    GMGNTransportError,
    RateLimitReset,
)
from gmgn_sdk.models import (
    CreateTokenParams,
    MethodParitySpec,
    MultiSwapParams,
    StrategyCancelParams,
    StrategyCreateParams,
    SwapParams,
    TokenSignalGroup,
)
from gmgn_sdk.signer import sign_message
from gmgn_sdk.validation import (
    validate_address,
    validate_chain,
    validate_create_token_chain,
    validate_percent,
    validate_positive_int_str,
)


@dataclass(slots=True, frozen=True)
class _PreparedRequest:
    method: str
    path: str
    url: str
    headers: dict[str, str]
    body_text: str | None
    body_bytes: bytes | None


class GMGNClient:
    METHOD_PARITY: tuple[MethodParitySpec, ...] = METHOD_PARITY_SPECS

    def __init__(
        self,
        config: GMGNConfig | None = None,
        *,
        api_key: str | None = None,
        private_key: str | None = None,
        host: str | None = None,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        http_client: httpx.Client | None = None,
        timestamp_factory: Callable[[], int] | None = None,
        client_id_factory: Callable[[], str] | None = None,
        sleep_func: Callable[[float], None] | None = None,
        auto_retry_max_wait_ms: int | None = None,
    ) -> None:
        if config is not None:
            if api_key is not None or private_key is not None or host is not None:
                raise GMGNConfigurationError(
                    "Pass either GMGNConfig or explicit api_key/private_key/host, not both"
                )
            api_key = config.api_key
            private_key = config.private_key_pem
            host = config.host
        if not api_key:
            raise GMGNConfigurationError("GMGN_API_KEY is required")
        self.api_key = api_key
        self.private_key = private_key
        self.host = (host or DEFAULT_HOST).rstrip("/")
        self._debug = _env_flag("GMGN_DEBUG")
        self._timestamp_factory = timestamp_factory or (lambda: int(time.time()))
        self._client_id_factory = client_id_factory or (lambda: str(uuid.uuid4()))
        self._sleep = sleep_func or time.sleep
        self._auto_retry_max_wait_ms = (
            auto_retry_max_wait_ms
            if auto_retry_max_wait_ms is not None
            else _parse_retry_wait_ms(os.environ.get("GMGN_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS"))
        )
        self._owns_client = http_client is None
        self._client = http_client or httpx.Client(timeout=timeout)

    @classmethod
    def from_env(
        cls,
        *,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        http_client: httpx.Client | None = None,
    ) -> GMGNClient:
        return cls(
            get_config(),
            timeout=timeout,
            http_client=http_client,
        )

    @classmethod
    def method_parity(cls) -> tuple[MethodParitySpec, ...]:
        return cls.METHOD_PARITY

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> GMGNClient:
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.close()

    def getTokenInfo(self, chain: str, address: str) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        return self._normal_request("GET", "/v1/token/info", {"chain": chain, "address": address})

    def getTokenSecurity(self, chain: str, address: str) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        return self._normal_request(
            "GET", "/v1/token/security", {"chain": chain, "address": address}
        )

    def getTokenPoolInfo(self, chain: str, address: str) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        return self._normal_request(
            "GET", "/v1/token/pool_info", {"chain": chain, "address": address}
        )

    def getTokenTopHolders(
        self,
        chain: str,
        address: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        return self._normal_request(
            "GET",
            "/v1/market/token_top_holders",
            {"chain": chain, "address": address, **dict(extra or {})},
        )

    def getTokenTopTraders(
        self,
        chain: str,
        address: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        return self._normal_request(
            "GET",
            "/v1/market/token_top_traders",
            {"chain": chain, "address": address, **dict(extra or {})},
        )

    def getTokenKline(
        self,
        chain: str,
        address: str,
        resolution: str,
        from_: int | None = None,
        to: int | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(address, chain, label="address")
        query: dict[str, QueryValue] = {
            "chain": chain,
            "address": address,
            "resolution": resolution,
        }
        if from_ is not None:
            query["from"] = from_
        if to is not None:
            query["to"] = to
        return self._normal_request("GET", "/v1/market/token_kline", query)

    def getWalletHoldings(
        self,
        chain: str,
        wallet_address: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(wallet_address, chain, label="wallet")
        return self._normal_request(
            "GET",
            "/v1/user/wallet_holdings",
            {"chain": chain, "wallet_address": wallet_address, **dict(extra or {})},
        )

    def getWalletActivity(
        self,
        chain: str,
        wallet_address: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(wallet_address, chain, label="wallet")
        return self._normal_request(
            "GET",
            "/v1/user/wallet_activity",
            {"chain": chain, "wallet_address": wallet_address, **dict(extra or {})},
        )

    def getWalletStats(
        self,
        chain: str,
        wallet_addresses: Sequence[str],
        period: str = "7d",
    ) -> Any:
        validate_chain(chain)
        for wallet_address in wallet_addresses:
            validate_address(wallet_address, chain, label="wallet")
        return self._normal_request(
            "GET",
            "/v1/user/wallet_stats",
            {"chain": chain, "wallet_address": list(wallet_addresses), "period": period},
        )

    def getWalletTokenBalance(self, chain: str, wallet_address: str, token_address: str) -> Any:
        validate_chain(chain)
        validate_address(wallet_address, chain, label="wallet")
        validate_address(token_address, chain, label="token")
        return self._normal_request(
            "GET",
            "/v1/user/wallet_token_balance",
            {
                "chain": chain,
                "wallet_address": wallet_address,
                "token_address": token_address,
            },
        )

    def getTrenches(
        self,
        chain: str,
        types: Sequence[str] | None = None,
        platforms: Sequence[str] | None = None,
        limit: int | None = None,
        filters: Mapping[str, int | str] | None = None,
    ) -> Any:
        validate_chain(chain)
        return self._normal_request(
            "POST",
            "/v1/trenches",
            {"chain": chain},
            _build_trenches_body(chain, types, platforms, limit, filters),
        )

    def getTrendingSwaps(
        self,
        chain: str,
        interval: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        return self._normal_request(
            "GET",
            "/v1/market/rank",
            {"chain": chain, "interval": interval, **dict(extra or {})},
        )

    def getTokenSignalV2(
        self,
        chain: str,
        groups: Sequence[TokenSignalGroup | Mapping[str, Any]],
    ) -> Any:
        validate_chain(chain)
        body_groups = [_coerce_payload(group) for group in groups]
        return self._normal_request(
            "POST",
            "/v1/market/token_signal",
            {},
            {"chain": chain, "groups": body_groups},
        )

    def getUserInfo(self) -> Any:
        return self._normal_request("GET", "/v1/user/info", {})

    def getFollowWallet(self, chain: str, extra: Mapping[str, QueryValue] | None = None) -> Any:
        validate_chain(chain)
        return self._critical_request(
            "GET", "/v1/trade/follow_wallet", {"chain": chain, **dict(extra or {})}, None
        )

    def getKol(self, chain: str | None = None, limit: int | None = None) -> Any:
        query: dict[str, QueryValue] = {}
        if chain is not None:
            validate_chain(chain)
            query["chain"] = chain
        if limit is not None:
            query["limit"] = limit
        return self._normal_request("GET", "/v1/user/kol", query)

    def getSmartMoney(self, chain: str | None = None, limit: int | None = None) -> Any:
        query: dict[str, QueryValue] = {}
        if chain is not None:
            validate_chain(chain)
            query["chain"] = chain
        if limit is not None:
            query["limit"] = limit
        return self._normal_request("GET", "/v1/user/smartmoney", query)

    def getCreatedTokens(
        self,
        chain: str,
        wallet_address: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        validate_address(wallet_address, chain, label="wallet")
        return self._normal_request(
            "GET",
            "/v1/user/created_tokens",
            {"chain": chain, "wallet_address": wallet_address, **dict(extra or {})},
        )

    def quoteOrder(
        self,
        chain: str,
        from_address: str,
        input_token: str,
        output_token: str,
        input_amount: str,
        slippage: float,
    ) -> Any:
        validate_chain(chain)
        validate_address(from_address, chain, label="from_address")
        validate_address(input_token, chain, label="input_token")
        validate_address(output_token, chain, label="output_token")
        validate_positive_int_str(input_amount, label="input_amount")
        validate_percent(slippage, label="slippage")
        return self._critical_request(
            "GET",
            "/v1/trade/quote",
            {
                "chain": chain,
                "from_address": from_address,
                "input_token": input_token,
                "output_token": output_token,
                "input_amount": input_amount,
                "slippage": slippage,
            },
            None,
        )

    def swap(self, params: SwapParams | Mapping[str, Any]) -> Any:
        body = _coerce_payload(params)
        chain = str(body["chain"])
        validate_chain(chain)
        validate_address(str(body["from_address"]), chain, label="from_address")
        return self._critical_request("POST", "/v1/trade/swap", {}, body)

    def multiSwap(self, params: MultiSwapParams | Mapping[str, Any]) -> Any:
        body = _coerce_payload(params)
        chain = str(body["chain"])
        validate_chain(chain)
        accounts = body.get("accounts", [])
        if isinstance(accounts, list):
            for account in accounts:
                validate_address(str(account), chain, label="account")
        return self._critical_request("POST", "/v1/trade/multi_swap", {}, body)

    def queryOrder(self, order_id: str, chain: str) -> Any:
        validate_chain(chain)
        return self._critical_request(
            "GET", "/v1/trade/query_order", {"order_id": order_id, "chain": chain}, None
        )

    def createStrategyOrder(self, params: StrategyCreateParams | Mapping[str, Any]) -> Any:
        body = _coerce_payload(params)
        chain = str(body["chain"])
        validate_chain(chain)
        validate_address(str(body["from_address"]), chain, label="from_address")
        return self._critical_request("POST", "/v1/trade/strategy/create", {}, body)

    def getStrategyOrders(
        self,
        chain: str,
        extra: Mapping[str, QueryValue] | None = None,
    ) -> Any:
        validate_chain(chain)
        return self._critical_request(
            "GET", "/v1/trade/strategy/orders", {"chain": chain, **dict(extra or {})}, None
        )

    def cancelStrategyOrder(self, params: StrategyCancelParams | Mapping[str, Any]) -> Any:
        body = _coerce_payload(params)
        chain = str(body["chain"])
        validate_chain(chain)
        validate_address(str(body["from_address"]), chain, label="from_address")
        return self._critical_request("POST", "/v1/trade/strategy/cancel", {}, body)

    def getCookingStatistics(self) -> Any:
        return self._normal_request("GET", "/v1/cooking/statistics", {})

    def createToken(self, params: CreateTokenParams | Mapping[str, Any]) -> Any:
        body = _coerce_payload(params)
        validate_create_token_chain(str(body["chain"]))
        return self._critical_request("POST", "/v1/cooking/create_token", {}, body)

    get_token_info = getTokenInfo
    get_token_security = getTokenSecurity
    get_token_pool_info = getTokenPoolInfo
    get_token_top_holders = getTokenTopHolders
    get_token_top_traders = getTokenTopTraders
    get_token_kline = getTokenKline
    get_wallet_holdings = getWalletHoldings
    get_wallet_activity = getWalletActivity
    get_wallet_stats = getWalletStats
    get_wallet_token_balance = getWalletTokenBalance
    get_trenches = getTrenches
    get_trending_swaps = getTrendingSwaps
    get_token_signal_v2 = getTokenSignalV2
    get_user_info = getUserInfo
    get_follow_wallet = getFollowWallet
    get_kol = getKol
    get_smart_money = getSmartMoney
    get_created_tokens = getCreatedTokens
    quote_order = quoteOrder
    multi_swap = multiSwap
    query_order = queryOrder
    create_strategy_order = createStrategyOrder
    get_strategy_orders = getStrategyOrders
    cancel_strategy_order = cancelStrategyOrder
    get_cooking_statistics = getCookingStatistics
    create_token = createToken

    def _normal_request(
        self,
        method: str,
        path: str,
        query_extra: Mapping[str, QueryValue],
        body: Mapping[str, Any] | None = None,
    ) -> Any:
        return self._execute_prepared_request(
            lambda: self._prepare_request(method, path, query_extra, body, NORMAL_AUTH),
            auto_retry_on_rate_limit=True,
        )

    def _critical_request(
        self,
        method: str,
        path: str,
        query_extra: Mapping[str, QueryValue],
        body: Mapping[str, Any] | None,
    ) -> Any:
        if not self.private_key:
            raise GMGNConfigurationError(
                "GMGN_PRIVATE_KEY is required for critical-auth methods"
            )
        return self._execute_prepared_request(
            lambda: self._prepare_request(method, path, query_extra, body, CRITICAL_AUTH),
            auto_retry_on_rate_limit=method != "POST",
        )

    def _execute_prepared_request(
        self,
        prepare: Callable[[], _PreparedRequest],
        *,
        auto_retry_on_rate_limit: bool,
    ) -> Any:
        max_attempts = 2 if auto_retry_on_rate_limit else 1
        for attempt in range(1, max_attempts + 1):
            prepared = prepare()
            response = self._send(prepared)
            try:
                return self._parse_response(prepared.method, prepared.path, response, prepared)
            except GMGNAPIError as error:
                retry_delay_ms = self._get_rate_limit_retry_delay_ms(
                    error, attempt, max_attempts, auto_retry_on_rate_limit
                )
                if retry_delay_ms is None:
                    raise
                if self._debug:
                    print(
                        f"[gmgn-sdk] {prepared.method} {prepared.path} hit rate limit, "
                        f"retrying once in {int((retry_delay_ms + 999) // 1000)}s",
                        file=sys.stderr,
                    )
                self._sleep(retry_delay_ms / 1000)
        raise GMGNTransportError("Unexpected retry loop exit")

    def _prepare_request(
        self,
        method: str,
        path: str,
        query_extra: Mapping[str, QueryValue],
        body: Mapping[str, Any] | None,
        auth_mode: str,
    ) -> _PreparedRequest:
        timestamp = self._timestamp_factory()
        client_id = self._client_id_factory()
        query: dict[str, QueryValue] = dict(query_extra)
        query["timestamp"] = timestamp
        query["client_id"] = client_id
        if body is not None:
            body_text = serialize_body(body)
        elif auth_mode == CRITICAL_AUTH:
            body_text = ""
        else:
            body_text = None
        body_bytes = body_text.encode("utf-8") if body_text else None
        headers = {
            "X-APIKEY": self.api_key,
            "Content-Type": "application/json",
        }
        if auth_mode == CRITICAL_AUTH:
            assert self.private_key is not None
            message = build_signature_message(path, query, body_text or "", timestamp)
            headers["X-Signature"] = sign_message(message, self.private_key)
        url = build_url(f"{self.host}{path}", query)
        return _PreparedRequest(
            method=method,
            path=path,
            url=url,
            headers=headers,
            body_text=None if body_text == "" else body_text,
            body_bytes=body_bytes,
        )

    def _send(self, prepared: _PreparedRequest) -> httpx.Response:
        request = self._client.build_request(
            prepared.method,
            prepared.url,
            headers=prepared.headers,
            content=prepared.body_bytes,
        )
        try:
            response = self._client.send(request)
        except httpx.HTTPError as error:
            debug = self._format_debug_request(prepared)
            if self._debug:
                print(f"{debug}\n[error] {type(error).__name__}: {error}", file=sys.stderr)
            message = f"{prepared.method} {prepared.path} fetch failed: {error}"
            raise GMGNTransportError(message) from error
        if self._debug:
            print(
                f"{self._format_debug_request(prepared)}\n{self._format_debug_response(response)}",
                file=sys.stderr,
            )
        return response

    def _parse_response(
        self,
        method: str,
        path: str,
        response: httpx.Response,
        prepared: _PreparedRequest,
    ) -> Any:
        reset = _parse_rate_limit_reset(response.headers.get("x-ratelimit-reset"))
        try:
            text = response.text
        except Exception as error:
            raise GMGNTransportError(
                f"{method} {path} failed: HTTP {response.status_code} "
                f"(failed to read response body: {error})"
            ) from error
        try:
            envelope = json.loads(text)
        except json.JSONDecodeError as error:
            if self._debug:
                print(
                    f"{self._format_debug_request(prepared)}\n"
                    f"{self._format_debug_response(response, body_override=text)}",
                    file=sys.stderr,
                )
            raise GMGNTransportError(
                f"{method} {path} failed: HTTP {response.status_code} (non-JSON response)"
            ) from error
        if not isinstance(envelope, dict):
            raise GMGNTransportError(
                f"{method} {path} failed: HTTP {response.status_code} (unexpected payload shape)"
            )
        if envelope.get("code") != 0:
            raise GMGNAPIError(
                method=method,
                path=path,
                status_code=response.status_code,
                api_code=envelope.get("code"),
                api_error=_string_or_none(envelope.get("error")),
                api_message=_string_or_none(envelope.get("message")),
                rate_limit_reset=reset,
            )
        return envelope.get("data")

    def _get_rate_limit_retry_delay_ms(
        self,
        error: GMGNAPIError,
        attempt: int,
        max_attempts: int,
        auto_retry_on_rate_limit: bool,
    ) -> int | None:
        if not auto_retry_on_rate_limit or attempt >= max_attempts:
            return None
        if error.api_error not in {"RATE_LIMIT_EXCEEDED", "RATE_LIMIT_BANNED"}:
            return None
        if error.reset_at_unix is None:
            return None
        wait_ms = max((error.reset_at_unix * 1000) - int(time.time() * 1000), 0)
        wait_ms += RATE_LIMIT_RETRY_BUFFER_MS
        return wait_ms if wait_ms <= self._auto_retry_max_wait_ms else None

    def _format_debug_request(self, prepared: _PreparedRequest) -> str:
        header_lines = "\n".join(
            f"  {key}: {self._redact_header_value(key, value)}"
            for key, value in prepared.headers.items()
        )
        body = prepared.body_text if prepared.body_text is not None else "(no body)"
        debug = f"[request] {prepared.method} {prepared.url}\n{header_lines}\n\n{body}"
        return self._redact_text(debug, prepared)

    def _format_debug_response(
        self,
        response: httpx.Response,
        *,
        body_override: str | None = None,
    ) -> str:
        header_lines = "\n".join(f"  {key}: {value}" for key, value in response.headers.items())
        body = response.text if body_override is None else body_override
        return self._redact_text(
            f"[response] HTTP {response.status_code}\n{header_lines}\n\n{body or '(no body)'}",
            None,
        )

    def _redact_text(self, text: str, prepared: _PreparedRequest | None) -> str:
        redacted = text
        for secret in (self.api_key, self.private_key):
            if secret:
                redacted = redacted.replace(secret, REDACTION_PLACEHOLDER)
        if prepared is not None:
            signature = prepared.headers.get("X-Signature")
            if signature:
                redacted = redacted.replace(signature, REDACTION_PLACEHOLDER)
        return redacted

    def _redact_header_value(self, key: str, value: str) -> str:
        if key.lower() in REDACTED_HEADER_NAMES:
            return REDACTION_PLACEHOLDER
        return value


def _env_flag(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _parse_retry_wait_ms(raw: str | None) -> int:
    if raw is None or raw == "":
        return DEFAULT_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS
    try:
        parsed = int(raw)
    except ValueError:
        return DEFAULT_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS
    return parsed if parsed >= 0 else DEFAULT_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS


def _coerce_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {
            str(key): _coerce_nested(item)
            for key, item in value.items()
            if item is not None
        }
    if hasattr(value, "to_payload"):
        payload = value.to_payload()
        if isinstance(payload, dict):
            return payload
    raise TypeError(f"Unsupported payload type: {type(value).__name__}")


def _coerce_nested(value: Any) -> Any:
    if hasattr(value, "to_payload"):
        return value.to_payload()
    if isinstance(value, Mapping):
        return {str(key): _coerce_nested(item) for key, item in value.items() if item is not None}
    if isinstance(value, (list, tuple)):
        return [_coerce_nested(item) for item in value if item is not None]
    return value


def _parse_rate_limit_reset(raw: str | None) -> RateLimitReset | None:
    if raw is None or raw.strip() == "":
        return None
    try:
        parsed = int(raw)
    except ValueError:
        return None
    return RateLimitReset(parsed) if parsed > 0 else None


def _string_or_none(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _build_trenches_body(
    chain: str,
    types: Sequence[str] | None,
    platforms: Sequence[str] | None,
    limit: int | None,
    filters: Mapping[str, int | str] | None,
) -> dict[str, Any]:
    selected_types = list(types) if types else ["new_creation", "near_completion", "completed"]
    launchpad_platforms = list(platforms) if platforms else list(TRENCHES_PLATFORMS.get(chain, ()))
    section: dict[str, Any] = {
        "filters": ["offchain", "onchain"],
        "launchpad_platform": launchpad_platforms,
        "quote_address_type": list(TRENCHES_QUOTE_ADDRESS_TYPES.get(chain, ())),
        "launchpad_platform_v2": True,
        "limit": 80 if limit is None else limit,
    }
    if filters:
        section.update(dict(filters))
    body: dict[str, Any] = {"version": "v2"}
    for trench_type in selected_types:
        body[trench_type] = dict(section)
    return body
