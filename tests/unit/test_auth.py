from __future__ import annotations

from uuid import UUID

import pytest

auth_module = pytest.importorskip("gmgn_sdk.auth")

build_auth_query = auth_module.build_auth_query
build_request_url = auth_module.build_request_url
build_signature_message = auth_module.build_signature_message
build_sorted_query_string = auth_module.build_sorted_query_string
serialize_request_body = auth_module.serialize_request_body


pytestmark = pytest.mark.unit


def test_build_auth_query_uses_unix_seconds_and_uuid() -> None:
    auth_query = build_auth_query(
        now=lambda: 1_712_345_678.987,
        uuid_factory=lambda: UUID("12345678-1234-5678-1234-567812345678"),
    )

    assert auth_query == {
        "timestamp": 1_712_345_678,
        "client_id": "12345678-1234-5678-1234-567812345678",
    }


def test_build_sorted_query_string_sorts_keys_and_repeats_sorted_array_values() -> None:
    query_string = build_sorted_query_string(
        {
            "z": "last",
            "a": ["charlie", "alpha", "bravo"],
            "m": 2,
        }
    )

    assert query_string == "a=alpha&a=bravo&a=charlie&m=2&z=last"


def test_build_request_url_uses_sorted_query_string() -> None:
    request_url = build_request_url(
        "https://openapi.gmgn.ai/v1/trade/quote",
        {"wallet": ["b", "a"], "chain": "sol"},
    )

    assert request_url == (
        "https://openapi.gmgn.ai/v1/trade/quote?chain=sol&wallet=a&wallet=b"
    )


def test_serialize_request_body_returns_compact_json_string_and_bytes() -> None:
    body_string, body_bytes = serialize_request_body({"chain": "sol", "amount": "1"})

    assert body_string == '{"chain":"sol","amount":"1"}'
    assert body_bytes == b'{"chain":"sol","amount":"1"}'


def test_build_signature_message_matches_expected_format() -> None:
    message = build_signature_message(
        sub_path="/v1/trade/swap",
        query_params={
            "client_id": "12345678-1234-5678-1234-567812345678",
            "wallet": ["b", "a"],
            "timestamp": 1_712_345_678,
        },
        request_body='{"amount":"1"}',
        timestamp=1_712_345_678,
    )

    assert message == (
        "/v1/trade/swap:"
        "client_id=12345678-1234-5678-1234-567812345678&timestamp=1712345678&wallet=a&wallet=b:"
        '{"amount":"1"}:1712345678'
    )
