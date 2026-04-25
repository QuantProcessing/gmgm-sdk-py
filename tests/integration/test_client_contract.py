from __future__ import annotations

import time
from collections import deque
from typing import Any

import httpx
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

from gmgn_sdk import CreateTokenParams, GMGNAPIError, GMGNClient, SwapParams

SOL_ADDRESS = "So11111111111111111111111111111111111111112"
EVM_ADDRESS = "0x0000000000000000000000000000000000000001"


def _generate_private_key_pem() -> str:
    key = ed25519.Ed25519PrivateKey.generate()
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")


class SpyClient(httpx.Client):
    def __init__(self, responses: list[dict[str, Any]]) -> None:
        self.build_calls: list[dict[str, Any]] = []
        self.requests: list[httpx.Request] = []
        self._responses = deque(responses)
        super().__init__(transport=httpx.MockTransport(self._handle))

    def build_request(self, method: str, url: str, **kwargs: Any) -> httpx.Request:
        self.build_calls.append({"method": method, "url": url, **kwargs})
        return super().build_request(method, url, **kwargs)

    def _handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        payload = self._responses.popleft()
        return httpx.Response(
            payload["status_code"],
            headers=payload.get("headers"),
            json=payload.get("json"),
            request=request,
        )


def test_normal_request_uses_prepared_url_and_retries_on_rate_limit() -> None:
    spy = SpyClient(
        [
            {
                "status_code": 429,
                "headers": {"x-ratelimit-reset": str(int(time.time()) + 1)},
                "json": {"code": 17, "error": "RATE_LIMIT_EXCEEDED", "message": "slow down"},
            },
            {"status_code": 200, "json": {"code": 0, "data": {"ok": True}}},
        ]
    )
    sleeps: list[float] = []
    client = GMGNClient(
        api_key="secret-api-key",
        http_client=spy,
        timestamp_factory=lambda: 1_700_000_000,
        client_id_factory=lambda: "client-1",
        sleep_func=sleeps.append,
        auto_retry_max_wait_ms=10_000,
    )

    result = client.getUserInfo()

    assert result == {"ok": True}
    assert len(spy.requests) == 2
    assert sleeps
    assert "params" not in spy.build_calls[0]
    assert "json" not in spy.build_calls[0]
    assert spy.build_calls[0]["content"] is None
    assert str(spy.requests[0].url) == (
        "https://openapi.gmgn.ai/v1/user/info?timestamp=1700000000&client_id=client-1"
    )
    assert spy.requests[0].headers["X-APIKEY"] == "secret-api-key"


def test_normal_post_uses_prepared_body_and_retries() -> None:
    spy = SpyClient(
        [
            {
                "status_code": 429,
                "headers": {"x-ratelimit-reset": str(int(time.time()) + 1)},
                "json": {"code": 18, "error": "RATE_LIMIT_BANNED", "message": "back off"},
            },
            {"status_code": 200, "json": {"code": 0, "data": {"posted": True}}},
        ]
    )
    client = GMGNClient(
        api_key="secret-api-key",
        http_client=spy,
        timestamp_factory=lambda: 1_700_000_000,
        client_id_factory=lambda: "client-1",
        sleep_func=lambda _: None,
        auto_retry_max_wait_ms=10_000,
    )

    result = client.getTrenches("sol")

    assert result == {"posted": True}
    assert len(spy.requests) == 2
    assert "params" not in spy.build_calls[0]
    assert "json" not in spy.build_calls[0]
    assert spy.build_calls[0]["content"] is not None
    assert b'"version":"v2"' in spy.build_calls[0]["content"]
    assert str(spy.requests[0].url) == (
        "https://openapi.gmgn.ai/v1/trenches?chain=sol&timestamp=1700000000&client_id=client-1"
    )


def test_critical_get_retries_and_signs_prepared_request() -> None:
    spy = SpyClient(
        [
            {
                "status_code": 429,
                "headers": {"x-ratelimit-reset": str(int(time.time()) + 1)},
                "json": {"code": 19, "error": "RATE_LIMIT_EXCEEDED", "message": "wait"},
            },
            {"status_code": 200, "json": {"code": 0, "data": {"following": True}}},
        ]
    )
    client = GMGNClient(
        api_key="secret-api-key",
        private_key=_generate_private_key_pem(),
        http_client=spy,
        timestamp_factory=lambda: 1_700_000_000,
        client_id_factory=lambda: "client-1",
        sleep_func=lambda _: None,
        auto_retry_max_wait_ms=10_000,
    )

    result = client.getFollowWallet("eth", {"wallet_address": EVM_ADDRESS})

    assert result == {"following": True}
    assert len(spy.requests) == 2
    assert "X-Signature" in spy.requests[0].headers
    assert str(spy.requests[0].url) == (
        "https://openapi.gmgn.ai/v1/trade/follow_wallet?"
        "chain=eth&wallet_address="
        "0x0000000000000000000000000000000000000001"
        "&timestamp=1700000000&client_id=client-1"
    )


def test_critical_post_does_not_retry_and_allows_create_token_ton_pass_through() -> None:
    spy = SpyClient(
        [
            {
                "status_code": 429,
                "headers": {"x-ratelimit-reset": str(int(time.time()) + 1)},
                "json": {"code": 20, "error": "RATE_LIMIT_EXCEEDED", "message": "no retry"},
            }
        ]
    )
    client = GMGNClient(
        api_key="secret-api-key",
        private_key=_generate_private_key_pem(),
        http_client=spy,
        timestamp_factory=lambda: 1_700_000_000,
        client_id_factory=lambda: "client-1",
        sleep_func=lambda _: None,
        auto_retry_max_wait_ms=10_000,
    )

    with pytest.raises(GMGNAPIError) as exc_info:
        client.createToken(
            CreateTokenParams(
                chain="ton",
                dex="stonfi",
                from_address="ton-wallet-address",
                name="Example",
                symbol="EXM",
                buy_amt="1000",
            )
        )

    assert exc_info.value.api_error == "RATE_LIMIT_EXCEEDED"
    assert len(spy.requests) == 1
    assert "params" not in spy.build_calls[0]
    assert "json" not in spy.build_calls[0]
    assert spy.build_calls[0]["content"] is not None
    assert b'"chain":"ton"' in spy.build_calls[0]["content"]


def test_api_error_exposes_rate_limit_reset_data() -> None:
    spy = SpyClient(
        [
            {
                "status_code": 429,
                "headers": {"x-ratelimit-reset": "1700000010"},
                "json": {"code": 21, "error": "RATE_LIMIT_BANNED", "message": "try later"},
            }
        ]
    )
    client = GMGNClient(
        api_key="secret-api-key",
        private_key=_generate_private_key_pem(),
        http_client=spy,
        timestamp_factory=lambda: 1_700_000_000,
        client_id_factory=lambda: "client-1",
        sleep_func=lambda _: None,
        auto_retry_max_wait_ms=0,
    )

    with pytest.raises(GMGNAPIError) as exc_info:
        client.swap(
            SwapParams(
                chain="eth",
                from_address=EVM_ADDRESS,
                input_token=EVM_ADDRESS,
                output_token="0x0000000000000000000000000000000000000002",
                input_amount="1000",
            )
        )

    error = exc_info.value
    assert error.status_code == 429
    assert error.api_code == 21
    assert error.api_error == "RATE_LIMIT_BANNED"
    assert error.reset_at_unix == 1_700_000_010
    assert "1700000010" in str(error)
