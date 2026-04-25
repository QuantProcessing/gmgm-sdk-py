"""Authentication query, serialization, and redaction helpers."""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import Callable, Mapping, Sequence
from typing import Any, cast
from urllib.parse import urlencode

QueryScalar = str | int | float | bool
QueryValue = QueryScalar | Sequence[QueryScalar]
QueryParams = Mapping[str, QueryValue]

REDACTED = "***REDACTED***"
SENSITIVE_HEADERS = {"x-apikey", "x-signature", "authorization"}
SENSITIVE_ENV_KEYS = {"GMGN_API_KEY", "GMGN_PRIVATE_KEY"}


def build_auth_query(
    timestamp: int | None = None,
    client_id: str | None = None,
    *,
    now: Callable[[], float] = time.time,
    uuid_factory: Callable[[], uuid.UUID] = uuid.uuid4,
) -> dict[str, int | str]:
    return {
        "timestamp": int(now()) if timestamp is None else timestamp,
        "client_id": str(uuid_factory()) if client_id is None else client_id,
    }


def _is_array_value(value: object) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes | bytearray)


def stringify_query_value(value: QueryScalar) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def iter_query_pairs(
    query: QueryParams,
    *,
    sort_keys: bool = False,
    sort_array_values: bool = False,
) -> list[tuple[str, str]]:
    keys = sorted(query) if sort_keys else list(query)
    pairs: list[tuple[str, str]] = []
    for key in keys:
        value = query[key]
        if _is_array_value(value):
            values = [stringify_query_value(item) for item in cast(Sequence[QueryScalar], value)]
            if sort_array_values:
                values.sort()
            pairs.extend((key, item) for item in values)
        else:
            pairs.append((key, stringify_query_value(cast(QueryScalar, value))))
    return pairs


def encode_query(
    query: QueryParams,
    *,
    sort_keys: bool = False,
    sort_array_values: bool = False,
) -> str:
    return urlencode(
        iter_query_pairs(query, sort_keys=sort_keys, sort_array_values=sort_array_values),
        doseq=True,
    )


def build_sorted_query_string(query: QueryParams) -> str:
    return "&".join(
        f"{key}={value}"
        for key, value in iter_query_pairs(query, sort_keys=True, sort_array_values=True)
    )


def build_url(base: str, query: QueryParams) -> str:
    return f"{base}?{encode_query(query)}"


def build_request_url(base: str, query: QueryParams) -> str:
    if not query:
        return base
    sorted_query = encode_query(query, sort_keys=True, sort_array_values=True)
    return f"{base}?{sorted_query}"


def serialize_body(body: Any) -> str | None:
    if body is None:
        return None
    return json.dumps(body, separators=(",", ":"), ensure_ascii=False)


def serialize_request_body(body: Any) -> tuple[str, bytes]:
    body_string = serialize_body(body)
    if body_string is None:
        return "", b""
    return body_string, body_string.encode("utf-8")


def build_signature_message(
    sub_path: str,
    query_params: QueryParams,
    request_body: str,
    timestamp: int,
) -> str:
    sorted_query = build_sorted_query_string(query_params)
    return f"{sub_path}:{sorted_query}:{request_body}:{timestamp}"


def redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {
        key: REDACTED if key.lower() in SENSITIVE_HEADERS else value
        for key, value in headers.items()
    }


def redact_value(key: str, value: str | None) -> str | None:
    if value is None:
        return None
    return REDACTED if key in SENSITIVE_ENV_KEYS else value


def format_curl(method: str, url: str, headers: Mapping[str, str], body: str | None) -> str:
    redacted = redact_headers(headers)
    header_args = " \\\n".join(f"  -H '{key}: {value}'" for key, value in redacted.items())
    escaped_body = body.replace("'", "'\\''") if body else ""
    body_arg = f" \\\n  -d '{escaped_body}'" if body else ""
    return f"\n[curl]\ncurl -X {method} '{url}' \\\n{header_args}{body_arg}\n"
