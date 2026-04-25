# GMGN SDK

Python SDK for the GMGN OpenAPI, ported from the official TypeScript
`gmgn-cli` client surface.

This repository is intentionally SDK-only:

- no Python CLI wrapper
- no mock transport in the main package
- methods return the raw GMGN `data` payload, not the full `{code, message, data}` envelope
- non-zero GMGN envelopes raise structured Python exceptions

The current SDK covers the full 27-method `OpenApiClient` surface from the
official TypeScript implementation, including normal-auth routes, critical-auth
routes, request signing, one-shot rate-limit retry rules, and live swap
verification.

## What This SDK Supports

- Full official GMGN method parity: `27` methods
- Both auth modes:
  - normal auth: `X-APIKEY`
  - critical auth: `X-APIKEY` + `X-Signature`
- Ed25519 and RSA private keys for critical-auth requests
- Sync `httpx` client usage with prepared URL/body/header transport
- Real live swap execution for `sol`, `eth`, and `bsc`
- Custom fee fields and anti-MEV flags on swap-style routes
- `camelCase` parity methods and `snake_case` aliases

## Installation

For local development:

```bash
python3 -m pip install -e '.[dev]'
```

To build distributable artifacts:

```bash
python3 -m build
```

The build creates:

- `dist/gmgn_sdk-0.1.0.tar.gz`
- `dist/gmgn_sdk-0.1.0-py3-none-any.whl`

## Python Version and Dependencies

- Python `>=3.11`
- Runtime dependencies:
  - `httpx`
  - `cryptography`
- Dev dependencies:
  - `pytest`
  - `pytest-mock`
  - `ruff`
  - `mypy`
  - `build`

## Quick Start

```python
from gmgn_sdk import GMGNClient

client = GMGNClient.from_env()
token = client.getTokenInfo("sol", "So11111111111111111111111111111111111111112")
print(token)
client.close()
```

Using a context manager:

```python
from gmgn_sdk import GMGNClient

with GMGNClient.from_env() as client:
    data = client.getUserInfo()
    print(data)
```

Explicit construction:

```python
from gmgn_sdk import GMGNClient

client = GMGNClient(
    api_key="your-api-key",
    private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)
```

Or with a config object:

```python
from gmgn_sdk import GMGNClient, GMGNConfig

config = GMGNConfig(
    api_key="your-api-key",
    private_key_pem="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)

client = GMGNClient(config)
```

## Configuration

Configuration is loaded in this order:

1. `~/.config/gmgn/.env`
2. project `.env`
3. process environment

Later sources override earlier ones.

Supported variables:

- `GMGN_API_KEY`
- `GMGN_PRIVATE_KEY`
- `GMGN_HOST`
- `GMGN_DEBUG`
- `GMGN_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS`

### Required Variables

Always required:

- `GMGN_API_KEY`

Required for critical-auth methods:

- `GMGN_PRIVATE_KEY`

Optional:

- `GMGN_HOST`
  - default: `https://openapi.gmgn.ai`
- `GMGN_DEBUG`
  - truthy values such as `1`, `true`, `yes`, `on`
  - enables redacted request/response debug output
- `GMGN_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS`
  - maximum retry wait for eligible rate-limit responses
  - default is controlled by the SDK constant

### Private Key Formats

The SDK supports all of the following `GMGN_PRIVATE_KEY` styles:

Single-line escaped newline form:

```dotenv
GMGN_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```

Quoted multiline form:

```dotenv
GMGN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----"
```

In-memory string form:

```python
client = GMGNClient(
    api_key="...",
    private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)
```

## Auth Modes

GMGN routes in this SDK are split into two auth modes.

### Normal Auth

Normal-auth requests use:

- query params: `timestamp`, `client_id`
- header: `X-APIKEY`

### Critical Auth

Critical-auth requests use:

- query params: `timestamp`, `client_id`
- headers:
  - `X-APIKEY`
  - `X-Signature`

The signature message format matches the official TypeScript client:

```text
{sub_path}:{sorted_query_string}:{request_body}:{timestamp}
```

Important details:

- query keys are sorted alphabetically for the signature
- array values are serialized as repeated `k=v` pairs and sorted by value for
  the signature
- the actual request URL keeps query insertion order, matching the TypeScript
  implementation
- Ed25519 signs raw message bytes
- RSA uses `RSA-PSS + SHA256` with salt length `32`

## Request and Response Behavior

### Returned Data

On success, SDK methods return:

- the GMGN `data` field only

On failure, they raise:

- `GMGNConfigurationError`
- `GMGNValidationError`
- `GMGNTransportError`
- `GMGNAPIError`

### Retry Policy

The SDK intentionally does not retry everything.

It retries at most once for eligible GMGN rate-limit responses on:

- all normal-auth requests
- critical-auth `GET` requests

It does not auto-retry:

- critical-auth `POST` requests

That means `swap`, `multiSwap`, `createStrategyOrder`, `cancelStrategyOrder`,
and `createToken` are never automatically re-submitted by the SDK.

### Transport Guarantees

Prepared requests are sent with:

- a fully prepared URL
- a fully prepared byte body
- explicit headers

The SDK does not rely on `httpx` convenience serialization such as:

- `params=`
- `json=`

That matters because signed requests must hash the exact bytes that are sent.

## Supported Chains

General route validation supports:

- `sol`
- `bsc`
- `base`
- `eth`
- `monad`

`createToken` additionally allows:

- `ton`

Current live acceptance coverage in this repository is limited to:

- `sol`
- `eth`
- `bsc`

## Public API

The package exports:

- `GMGNClient`
- `GMGNConfig`
- `get_config`
- `load_config`
- `SwapParams`
- `MultiSwapParams`
- `StrategyCreateParams`
- `StrategyCancelParams`
- `StrategyConditionOrder`
- `TokenSignalGroup`
- `CreateTokenParams`
- `GMGNError`
- `GMGNConfigurationError`
- `GMGNValidationError`
- `GMGNTransportError`
- `GMGNAPIError`
- `RateLimitReset`
- `ConfigError`

## Method Parity

The SDK implements all official TypeScript `OpenApiClient` methods.

| Method | HTTP | Path | Auth |
| --- | --- | --- | --- |
| `getTokenInfo` | `GET` | `/v1/token/info` | normal |
| `getTokenSecurity` | `GET` | `/v1/token/security` | normal |
| `getTokenPoolInfo` | `GET` | `/v1/token/pool_info` | normal |
| `getTokenTopHolders` | `GET` | `/v1/market/token_top_holders` | normal |
| `getTokenTopTraders` | `GET` | `/v1/market/token_top_traders` | normal |
| `getTokenKline` | `GET` | `/v1/market/token_kline` | normal |
| `getWalletHoldings` | `GET` | `/v1/user/wallet_holdings` | normal |
| `getWalletActivity` | `GET` | `/v1/user/wallet_activity` | normal |
| `getWalletStats` | `GET` | `/v1/user/wallet_stats` | normal |
| `getWalletTokenBalance` | `GET` | `/v1/user/wallet_token_balance` | normal |
| `getTrenches` | `POST` | `/v1/trenches` | normal |
| `getTrendingSwaps` | `GET` | `/v1/market/rank` | normal |
| `getTokenSignalV2` | `POST` | `/v1/market/token_signal` | normal |
| `getUserInfo` | `GET` | `/v1/user/info` | normal |
| `getFollowWallet` | `GET` | `/v1/trade/follow_wallet` | critical |
| `getKol` | `GET` | `/v1/user/kol` | normal |
| `getSmartMoney` | `GET` | `/v1/user/smartmoney` | normal |
| `getCreatedTokens` | `GET` | `/v1/user/created_tokens` | normal |
| `quoteOrder` | `GET` | `/v1/trade/quote` | critical |
| `swap` | `POST` | `/v1/trade/swap` | critical |
| `multiSwap` | `POST` | `/v1/trade/multi_swap` | critical |
| `queryOrder` | `GET` | `/v1/trade/query_order` | critical |
| `createStrategyOrder` | `POST` | `/v1/trade/strategy/create` | critical |
| `getStrategyOrders` | `GET` | `/v1/trade/strategy/orders` | critical |
| `cancelStrategyOrder` | `POST` | `/v1/trade/strategy/cancel` | critical |
| `getCookingStatistics` | `GET` | `/v1/cooking/statistics` | normal |
| `createToken` | `POST` | `/v1/cooking/create_token` | critical |

You can inspect the parity table programmatically:

```python
from gmgn_sdk import GMGNClient

for item in GMGNClient.method_parity():
    print(item.name, item.http_method, item.path, item.auth_mode)
```

## Snake Case Aliases

In addition to the official `camelCase` parity methods, the SDK exposes common
Python-style aliases such as:

- `get_token_info`
- `get_wallet_holdings`
- `quote_order`
- `multi_swap`
- `create_strategy_order`
- `create_token`

The alias methods call the same underlying implementation.

## Request Models

Complex routes accept dataclass-based payload models.

### SwapParams

Used by `client.swap(...)`.

Core fields:

- `chain`
- `from_address`
- `input_token`
- `output_token`
- `input_amount`

Optional routing and execution fields:

- `swap_mode`
- `input_amount_bps`
- `output_amount`
- `slippage`
- `auto_slippage`
- `min_output_amount`
- `condition_orders`
- `sell_ratio_type`

Optional fee and anti-MEV fields:

- `is_anti_mev`
- `priority_fee`
- `tip_fee`
- `auto_tip_fee`
- `max_auto_fee`
- `gas_price`
- `max_fee_per_gas`
- `max_priority_fee_per_gas`

### MultiSwapParams

Used by `client.multiSwap(...)`.

Core fields:

- `chain`
- `accounts`
- `input_token`
- `output_token`

Amount fields:

- `input_amount`
- `input_amount_bps`
- `output_amount`

It also supports the same fee and anti-MEV fields as `SwapParams`.

### StrategyCreateParams

Used by `client.createStrategyOrder(...)`.

Core fields:

- `chain`
- `from_address`
- `base_token`
- `quote_token`
- `order_type`
- `sub_order_type`
- `check_price`

Optional fields include:

- `amount_in`
- `amount_in_percent`
- `limit_price_mode`
- `price_gap_ratio`
- `expire_in`
- `slippage`
- `auto_slippage`
- `fee`
- `gas_price`
- `max_fee_per_gas`
- `max_priority_fee_per_gas`
- `is_anti_mev`
- `anti_mev_mode`
- `priority_fee`
- `tip_fee`
- `custom_rpc`

### StrategyCancelParams

Used by `client.cancelStrategyOrder(...)`.

Fields:

- `chain`
- `from_address`
- `order_id`
- `order_type`
- `close_sell_model`

### TokenSignalGroup

Used by `client.getTokenSignalV2(...)`.

Fields include:

- `signal_type`
- `mc_min`
- `mc_max`
- `trigger_mc_min`
- `trigger_mc_max`
- `total_fee_min`
- `total_fee_max`
- `min_create_or_open_ts`
- `max_create_or_open_ts`

### CreateTokenParams

Used by `client.createToken(...)`.

Core fields:

- `chain`
- `dex`
- `from_address`
- `name`
- `symbol`
- `buy_amt`

Optional metadata fields:

- `image`
- `image_url`
- `website`
- `twitter`
- `telegram`

Optional execution fields:

- `slippage`
- `auto_slippage`
- `priority_fee`
- `tip_fee`
- `gas_price`
- `max_priority_fee_per_gas`
- `max_fee_per_gas`
- `is_anti_mev`
- `anti_mev_mode`

## Validation Rules

The SDK validates a focused set of client-side invariants before sending
requests.

Built-in validation includes:

- chain membership
- Solana and EVM address format checks
- positive integer checks for raw token amounts
- percent bounds for values such as `slippage`
- live swap native-amount caps in the test harness

Important boundary:

- the SDK validates obvious malformed inputs
- it does not attempt to mirror every CLI-side unit conversion or business rule
- route-specific numeric fields like `gas_price` and `priority_fee` are passed
  through as raw strings

## Fee Tuning and Anti-MEV

The SDK supports custom fee fields and anti-MEV flags on swap-style routes.

For swaps, multi-swaps, strategies, and token creation you can pass:

- `is_anti_mev=True`
- `priority_fee="..."`
- `tip_fee="..."`
- `auto_tip_fee=True`
- `max_auto_fee="..."`
- `gas_price="..."`
- `max_fee_per_gas="..."`
- `max_priority_fee_per_gas="..."`

Example:

```python
from gmgn_sdk import GMGNClient, SwapParams

with GMGNClient.from_env() as client:
    result = client.swap(
        SwapParams(
            chain="bsc",
            from_address="0x...",
            input_token="0x0000000000000000000000000000000000000000",
            output_token="0x...",
            input_amount="10000000000000000",
            slippage=0.01,
            is_anti_mev=True,
            gas_price="50000000",
            tip_fee="1000000000000",
        )
    )
```

Important note:

- this SDK is lower-level than the TypeScript CLI wrapper
- it does not automatically convert user-facing units like `gwei` into raw
  strings for you
- pass fee values in the exact raw unit format expected by GMGN for that route

If you are copying CLI examples, double-check whether the CLI was doing
additional unit conversion before making the API call.

## Examples

### Token Lookup

```python
from gmgn_sdk import GMGNClient

with GMGNClient.from_env() as client:
    info = client.getTokenInfo("sol", "So11111111111111111111111111111111111111112")
    security = client.getTokenSecurity("sol", "So11111111111111111111111111111111111111112")
    pool = client.getTokenPoolInfo("sol", "So11111111111111111111111111111111111111112")
```

### Wallet Holdings

```python
from gmgn_sdk import GMGNClient

with GMGNClient.from_env() as client:
    holdings = client.getWalletHoldings(
        "eth",
        "0x0000000000000000000000000000000000000001",
        extra={"limit": 20, "order_by": "usd_value", "direction": "desc"},
    )
```

### Quote Then Swap

```python
from gmgn_sdk import GMGNClient, SwapParams

with GMGNClient.from_env() as client:
    quote = client.quoteOrder(
        chain="eth",
        from_address="0x0000000000000000000000000000000000000001",
        input_token="0x0000000000000000000000000000000000000000",
        output_token="0x1111111111111111111111111111111111111111",
        input_amount="10000000000000000",
        slippage=0.01,
    )

    result = client.swap(
        SwapParams(
            chain="eth",
            from_address="0x0000000000000000000000000000000000000001",
            input_token="0x0000000000000000000000000000000000000000",
            output_token="0x1111111111111111111111111111111111111111",
            input_amount="10000000000000000",
            slippage=0.01,
        )
    )
```

### Query Order Status

```python
from gmgn_sdk import GMGNClient

with GMGNClient.from_env() as client:
    order = client.queryOrder("your-order-id", "sol")
    print(order)
```

### Create Token

```python
from gmgn_sdk import CreateTokenParams, GMGNClient

with GMGNClient.from_env() as client:
    result = client.createToken(
        CreateTokenParams(
            chain="ton",
            dex="stonfi",
            from_address="wallet-address",
            name="Example",
            symbol="EXM",
            buy_amt="1000",
            is_anti_mev=True,
        )
    )
```

## Error Handling

### GMGNAPIError

Raised when GMGN returns a non-zero envelope code.

Useful fields:

- `method`
- `path`
- `status_code`
- `api_code`
- `api_error`
- `api_message`
- `rate_limit_reset`
- `reset_at_unix`

Example:

```python
from gmgn_sdk import GMGNAPIError, GMGNClient

try:
    with GMGNClient.from_env() as client:
        client.getUserInfo()
except GMGNAPIError as exc:
    print(exc.status_code, exc.api_error, exc.api_message)
```

### Other Exceptions

- `GMGNConfigurationError`
  - missing API key, mixed constructor styles, missing private key for
    critical-auth flows
- `GMGNValidationError`
  - bad chain, malformed address, invalid percent, invalid raw integer
- `GMGNTransportError`
  - request failed or response could not be parsed

## Live Verification

Live swap verification is documented in
[`docs/live-verification.md`](docs/live-verification.md).

At a high level:

- live tests are gated by `RUN_LIVE_GMGN=1`
- live swap acceptance currently covers only `sol`, `eth`, and `bsc`
- capped native spend limits are enforced in the test harness
- `createToken` is implemented but intentionally excluded from first-pass live
  verification

Expected commands:

```bash
python3 -m pytest tests/unit
python3 -m pytest tests/integration
RUN_LIVE_GMGN=1 python3 -m pytest tests/live/test_live_swaps.py -m live
```

### Live Swap Environment Variables

Global:

- `RUN_LIVE_GMGN=1`
- `GMGN_API_KEY`
- `GMGN_PRIVATE_KEY`
- `GMGN_SOL_FROM_ADDRESS`
- `GMGN_ETH_FROM_ADDRESS`
- `GMGN_BSC_FROM_ADDRESS`

Per chain:

- `GMGN_<CHAIN>_INPUT_TOKEN`
- `GMGN_<CHAIN>_OUTPUT_TOKEN`
- `GMGN_<CHAIN>_INPUT_AMOUNT`
- `GMGN_<CHAIN>_INPUT_AMOUNT_NATIVE`

Optional per-chain execution tuning:

- `GMGN_<CHAIN>_SLIPPAGE`
- `GMGN_<CHAIN>_AUTO_SLIPPAGE`
- `GMGN_<CHAIN>_MIN_OUTPUT_AMOUNT`
- `GMGN_<CHAIN>_IS_ANTI_MEV`
- `GMGN_<CHAIN>_PRIORITY_FEE`
- `GMGN_<CHAIN>_TIP_FEE`
- `GMGN_<CHAIN>_AUTO_TIP_FEE`
- `GMGN_<CHAIN>_MAX_AUTO_FEE`
- `GMGN_<CHAIN>_GAS_PRICE`
- `GMGN_<CHAIN>_MAX_FEE_PER_GAS`
- `GMGN_<CHAIN>_MAX_PRIORITY_FEE_PER_GAS`

## Development and Verification

Lint:

```bash
python3 -m ruff check .
```

Typecheck:

```bash
python3 -m mypy src/gmgn_sdk
```

Tests:

```bash
python3 -m pytest tests -q -rs
```

Build:

```bash
python3 -m build
```

## Practical Notes

- `from_address` should be the wallet address bound to the API key for the
  chain you are trading on
- for native-token buys, GMGN may expect a chain-specific "native token"
  address representation; confirm the exact route convention you want to use in
  production
- returned order payloads vary by chain and route; the SDK intentionally
  preserves GMGN's raw `data` shape
- if a critical-auth request fails before the network call, check private key
  formatting first
- debug output is redacted, but still use `GMGN_DEBUG` carefully in sensitive
  environments

## Current Scope

This repository currently focuses on:

- importable SDK behavior
- parity with the official TypeScript client
- real swap verification

It does not currently provide:

- a Python CLI
- opinionated unit conversion helpers for fee fields
- route-specific convenience wrappers beyond the parity client and payload
  models
