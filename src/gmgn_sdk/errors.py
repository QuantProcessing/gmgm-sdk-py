from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


class GMGNError(Exception):
    """Base exception for SDK errors."""


class GMGNConfigurationError(GMGNError):
    """Raised when client configuration is invalid or incomplete."""


class GMGNValidationError(GMGNError):
    """Raised when request validation fails before transport."""


class GMGNTransportError(GMGNError):
    """Raised when a request cannot be sent or parsed."""


@dataclass(slots=True, frozen=True)
class RateLimitReset:
    unix_seconds: int

    @property
    def iso8601(self) -> str:
        return datetime.fromtimestamp(self.unix_seconds, tz=UTC).isoformat()


class GMGNAPIError(GMGNError):
    """Structured GMGN API error for non-zero envelope codes."""

    def __init__(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        api_code: int | str | None = None,
        api_error: str | None = None,
        api_message: str | None = None,
        rate_limit_reset: RateLimitReset | None = None,
    ) -> None:
        self.method = method
        self.path = path
        self.status_code = status_code
        self.api_code = api_code
        self.api_error = api_error
        self.api_message = api_message
        self.rate_limit_reset = rate_limit_reset
        super().__init__(self._build_message())

    @property
    def reset_at_unix(self) -> int | None:
        return None if self.rate_limit_reset is None else self.rate_limit_reset.unix_seconds

    def _build_message(self) -> str:
        parts = [f"{self.method} {self.path} failed: HTTP {self.status_code}"]
        if self.api_code is not None:
            parts.append(f"code={self.api_code}")
        if self.api_error:
            parts.append(f"error={self.api_error}")
        if self.api_message:
            parts.append(f"message={self.api_message}")

        message = " ".join(parts)
        if self.status_code != 429 or self.rate_limit_reset is None:
            return message

        reset_text = f"{self.rate_limit_reset.iso8601} (unix={self.rate_limit_reset.unix_seconds})"
        if self.api_error == "ERROR_RATE_LIMIT_BLOCKED":
            return f"{message}. Temporary business-error block until {reset_text}."
        if self.api_error in {"RATE_LIMIT_EXCEEDED", "RATE_LIMIT_BANNED"}:
            return f"{message}. Rate limit resets at {reset_text}."
        return f"{message}. Retry after {reset_text}."
