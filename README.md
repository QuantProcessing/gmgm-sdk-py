# GMGN SDK

[English](README.md) | [简体中文](README.zh-CN.md)

Python SDK for the GMGN OpenAPI, ported from the official TypeScript
`gmgn-cli` client surface.

This is an unofficial community project. It is not published by GMGN, and it
should not be presented as an official GMGN SDK.

The implementation was developed with strong AI assistance using OpenAI Codex,
then exercised against the real GMGN API in this repository's verification
workflow.

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

In addition to the official `camelCase` parity methods, the SDK exposes
Python-style aliases.

| Official Method | Python Alias |
| --- | --- |
| `getTokenInfo` | `get_token_info` |
| `getTokenSecurity` | `get_token_security` |
| `getTokenPoolInfo` | `get_token_pool_info` |
| `getTokenTopHolders` | `get_token_top_holders` |
| `getTokenTopTraders` | `get_token_top_traders` |
| `getTokenKline` | `get_token_kline` |
| `getWalletHoldings` | `get_wallet_holdings` |
| `getWalletActivity` | `get_wallet_activity` |
| `getWalletStats` | `get_wallet_stats` |
| `getWalletTokenBalance` | `get_wallet_token_balance` |
| `getTrenches` | `get_trenches` |
| `getTrendingSwaps` | `get_trending_swaps` |
| `getTokenSignalV2` | `get_token_signal_v2` |
| `getUserInfo` | `get_user_info` |
| `getFollowWallet` | `get_follow_wallet` |
| `getKol` | `get_kol` |
| `getSmartMoney` | `get_smart_money` |
| `getCreatedTokens` | `get_created_tokens` |
| `quoteOrder` | `quote_order` |
| `swap` | `swap` |
| `multiSwap` | `multi_swap` |
| `queryOrder` | `query_order` |
| `createStrategyOrder` | `create_strategy_order` |
| `getStrategyOrders` | `get_strategy_orders` |
| `cancelStrategyOrder` | `cancel_strategy_order` |
| `getCookingStatistics` | `get_cooking_statistics` |
| `createToken` | `create_token` |

The alias methods call the same underlying implementation.

## Detailed SDK Method Usage Guide

This section describes every SDK method, the most common scenario for using it,
and the parameters that usually matter in production scripts.

All examples use the official `camelCase` names for parity with the GMGN
TypeScript client. You can replace them with the snake-case aliases listed
above.

### Choosing the Right Market Discovery Method

GMGN exposes several market-style routes that can look similar at first glance.
Use the route that matches the lifecycle stage you are screening.

| Goal | Use | Why |
| --- | --- | --- |
| Inspect one known token by address | `getTokenInfo`, `getTokenSecurity`, `getTokenPoolInfo` | Direct token lookup. Best when you already have a contract address. |
| Find newly created, near-completion, or just-graduated launchpad tokens | `getTrenches` | Launchpad discovery window. Best for very new tokens. |
| Find already listed tokens that are actively trading now | `getTrendingSwaps` | Ranking feed by interval. Best for older or already migrated tokens. |
| Find signal-triggered tokens by market-cap or event groups | `getTokenSignalV2` | Signal feed. Best for smart-money, large-buy, price-spike, and trigger workflows. |

Important boundary:

- `getTrenches` is not a full historical token database.
- `getTrenches(..., limit=80)` returns a current window per category, so older
  Pump.fun tokens can be absent even if they still have high market cap and high
  trading volume.
- For a token such as an older Pump.fun coin that is already actively trading,
  use `getTrendingSwaps`, then apply client-side filters such as
  `market_cap >= 10_000_000`.

### Response Shape Helpers

Most methods return the GMGN `data` payload directly. Some GMGN market payloads
can still contain a nested `data` object because that is the raw upstream
payload returned by the endpoint. For rank-style responses, use a defensive
helper:

```python
def extract_rank(payload: dict) -> list[dict]:
    if isinstance(payload.get("rank"), list):
        return payload["rank"]
    nested = payload.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("rank"), list):
        return nested["rank"]
    return []
```

### Token Research Methods

Use these methods when you already know the token address.

#### `getTokenInfo(chain, address)`

Scenario:

- Fetch the main token profile, price, supply, liquidity, launchpad, pool,
  developer, social, and wallet-tag statistics.
- Use this as the first call in a token due-diligence workflow.

Parameters:

- `chain`: `sol`, `bsc`, `base`, `eth`, or `monad`
- `address`: token contract address

Example:

```python
from gmgn_sdk import GMGNClient

token_address = "So11111111111111111111111111111111111111112"

with GMGNClient.from_env() as client:
    info = client.getTokenInfo("sol", token_address)
    print(info.get("symbol"), info.get("price"), info.get("liquidity"))
```

#### `getTokenSecurity(chain, address)`

Scenario:

- Check risk and safety fields before trading or ranking a token.
- On Solana, inspect mint/freeze renounce flags, holder concentration, burn
  status, tax fields, and alert flags.
- On EVM chains, inspect honeypot, open-source, ownership-renounced, blacklist,
  and tax fields when the upstream API returns them.

Parameters:

- `chain`: chain identifier
- `address`: token contract address

Example:

```python
with GMGNClient.from_env() as client:
    security = client.getTokenSecurity("sol", token_address)
    if security.get("renounced_mint") and security.get("renounced_freeze_account"):
        print("Solana mint/freeze authority renounced")
```

#### `getTokenPoolInfo(chain, address)`

Scenario:

- Inspect the token's primary liquidity pool.
- Useful before a swap, before estimating liquidity depth, or when you need the
  pool address and quote token.

Parameters:

- `chain`: chain identifier
- `address`: token contract address

Example:

```python
with GMGNClient.from_env() as client:
    pool = client.getTokenPoolInfo("sol", token_address)
    print(pool.get("pool_address"), pool.get("quote_symbol"), pool.get("liquidity"))
```

#### `getTokenTopHolders(chain, address, extra=None)`

Scenario:

- Review concentration and top-wallet distribution.
- Use after `getTokenSecurity` if holder concentration looks high.

Parameters:

- `chain`: chain identifier
- `address`: token contract address
- `extra`: optional GMGN query fields, such as pagination or ordering fields
  supported by the upstream API

Example:

```python
with GMGNClient.from_env() as client:
    holders = client.getTokenTopHolders(
        "sol",
        token_address,
        extra={"limit": 20},
    )
    print(holders)
```

#### `getTokenTopTraders(chain, address, extra=None)`

Scenario:

- Inspect profitable traders, active traders, or suspicious trader clusters for
  one token.
- Useful when validating whether volume is organic.

Parameters:

- `chain`: chain identifier
- `address`: token contract address
- `extra`: optional GMGN query fields

Example:

```python
with GMGNClient.from_env() as client:
    traders = client.getTokenTopTraders(
        "sol",
        token_address,
        extra={"limit": 20},
    )
    print(traders)
```

#### `getTokenKline(chain, address, resolution, from_=None, to=None)`

Scenario:

- Fetch OHLCV candles for charting, momentum checks, and volume analysis.
- Use this when you need historical price and volume, not just the current rank
  item.

Parameters:

- `chain`: chain identifier
- `address`: token contract address
- `resolution`: `1m`, `5m`, `15m`, `1h`, `4h`, or `1d`
- `from_`: optional Unix timestamp in milliseconds
- `to`: optional Unix timestamp in milliseconds

Important:

- The Python SDK passes `from_` and `to` through directly.
- Use milliseconds. The official CLI accepts seconds and converts them, but this
  SDK intentionally stays close to the OpenAPI request shape.

Example:

```python
import time

with GMGNClient.from_env() as client:
    now_ms = int(time.time() * 1000)
    day_ago_ms = now_ms - 24 * 60 * 60 * 1000
    candles = client.getTokenKline(
        "sol",
        token_address,
        "1h",
        from_=day_ago_ms,
        to=now_ms,
    )

    rows = candles.get("list", candles if isinstance(candles, list) else [])
    volume_24h = sum(float(row.get("volume") or 0) for row in rows)
    print(volume_24h)
```

### Market Discovery Methods

Use these methods to discover tokens before you have a final address list.

#### `getTrenches(chain, types=None, platforms=None, limit=None, filters=None)`

Scenario:

- Scan launchpad tokens in lifecycle buckets:
  - `new_creation`: newly created launchpad tokens
  - `near_completion`: bonding curve nearly complete; returned under the
    response key `pump`
  - `completed`: recently graduated or migrated tokens
- Best for early discovery, launchpad monitoring, and "what just launched"
  workflows.

Parameters:

- `chain`: `sol`, `bsc`, or `base` for trenches-style discovery
- `types`: optional list of lifecycle buckets
- `platforms`: optional launchpad platform names
- `limit`: max results per category, up to the upstream route limit
- `filters`: server-side filter object merged into each requested category

Common Solana launchpad platforms:

- `Pump.fun`
- `pump_mayhem`
- `pump_mayhem_agent`
- `pump_agent`
- `letsbonk`
- `bonkers`
- `bags`
- `moonshot_app`
- `Moonshot`
- `boop`
- `meteora_virtual_curve`

Common server-side filters:

| Filter | Meaning |
| --- | --- |
| `min_marketcap`, `max_marketcap` | Market-cap range in USD |
| `min_liquidity`, `max_liquidity` | Liquidity range in USD |
| `min_volume_24h`, `max_volume_24h` | 24h volume range in USD |
| `min_net_buy_24h`, `max_net_buy_24h` | 24h net-buy range in USD |
| `min_swaps_24h`, `max_swaps_24h` | 24h swap-count range |
| `min_buys_24h`, `max_buys_24h` | 24h buy-count range |
| `min_sells_24h`, `max_sells_24h` | 24h sell-count range |
| `min_holder_count`, `max_holder_count` | Holder-count range |
| `min_top_holder_rate`, `max_top_holder_rate` | Top-10 holder concentration range |
| `min_rug_ratio`, `max_rug_ratio` | Rug-risk score range |
| `min_bundler_rate`, `max_bundler_rate` | Bundle-bot trading ratio range |
| `min_insider_ratio`, `max_insider_ratio` | Insider or sneak-trading ratio range |
| `min_smart_degen_count`, `max_smart_degen_count` | Smart-money holder count |
| `min_renowned_count`, `max_renowned_count` | KOL or renowned wallet count |
| `min_x_follower`, `max_x_follower` | Twitter/X follower range |
| `min_tg_call_count`, `max_tg_call_count` | Telegram-call count range |
| `min_created`, `max_created` | Token-age range such as `30m`, `1h`, `24h` |

Example: new Pump.fun-style meme candidates under a safety screen:

```python
MEME_LAUNCHPADS = [
    "Pump.fun",
    "pump_mayhem",
    "pump_mayhem_agent",
    "pump_agent",
    "letsbonk",
    "bonkers",
    "bags",
    "moonshot_app",
    "Moonshot",
    "boop",
]

with GMGNClient.from_env() as client:
    trenches = client.getTrenches(
        "sol",
        types=["new_creation", "near_completion", "completed"],
        platforms=MEME_LAUNCHPADS,
        limit=80,
        filters={
            "min_marketcap": 10_000,
            "max_marketcap": 500_000,
            "min_liquidity": 10_000,
            "min_volume_24h": 1_000,
            "max_rug_ratio": 0.3,
            "max_bundler_rate": 0.3,
            "max_insider_ratio": 0.3,
        },
    )

    completed = trenches.get("completed", [])
    near_completion = trenches.get("pump", [])
    new_creation = trenches.get("new_creation", [])
    print(len(new_creation), len(near_completion), len(completed))
```

Example: market cap greater than 10m, then require social links client-side:

```python
with GMGNClient.from_env() as client:
    trenches = client.getTrenches(
        "sol",
        types=["completed"],
        platforms=["Pump.fun", "letsbonk"],
        limit=80,
        filters={"min_marketcap": 10_000_000},
    )

    candidates = [
        item
        for item in trenches.get("completed", [])
        if item.get("has_at_least_one_social")
    ]
```

If a known older token is missing:

- confirm it with `getTokenInfo`
- use `getTrendingSwaps` for active already-listed tokens
- do not assume `getTrenches` contains all historical Pump.fun tokens

#### `getTrendingSwaps(chain, interval, extra=None)`

Scenario:

- Rank actively trading tokens by interval.
- Use this for already migrated tokens, higher market-cap tokens, and "what is
  active now" screens.
- This is the better route for older Pump.fun tokens that are no longer in the
  current trenches window.

Parameters:

- `chain`: chain identifier
- `interval`: `1m`, `5m`, `1h`, `6h`, or `24h`
- `extra`: optional query fields such as `limit`, `order_by`, `direction`,
  `filters`, and `platforms`

Common `order_by` values:

- `default`
- `volume`
- `swaps`
- `marketcap`
- `history_highest_market_cap`
- `liquidity`
- `holder_count`
- `smart_degen_count`
- `renowned_count`
- `price`
- `change1m`
- `change5m`
- `change1h`
- `creation_timestamp`

Common Solana `filters`:

- `renounced`
- `frozen`
- `burn`
- `token_burnt`
- `has_social`
- `not_social_dup`
- `not_image_dup`
- `dexscr_update_link`
- `not_wash_trading`
- `is_internal_market`
- `is_out_market`

Example: active Pump.fun tokens above 10m market cap:

```python
with GMGNClient.from_env() as client:
    payload = client.getTrendingSwaps(
        "sol",
        "24h",
        extra={
            "limit": 100,
            "order_by": "volume",
            "direction": "desc",
            "platforms": ["Pump.fun"],
            "filters": ["renounced", "frozen", "not_wash_trading"],
        },
    )

    rank = extract_rank(payload)
    large_pump_tokens = [
        item
        for item in rank
        if float(item.get("market_cap") or 0) >= 10_000_000
    ]
```

#### `getTokenSignalV2(chain, groups)`

Scenario:

- Query GMGN token signals by one or more signal groups.
- Use this when screening for event-driven opportunities such as price moves,
  smart-money activity, large buys, Dexscreener events, or market-cap trigger
  ranges.

Parameters:

- `chain`: currently most useful on `sol` and `bsc`
- `groups`: a list of `TokenSignalGroup` objects or dictionaries

Useful group fields:

- `signal_type`: list of GMGN signal ids
- `mc_min`, `mc_max`: current market-cap range
- `trigger_mc_min`, `trigger_mc_max`: trigger-time market-cap range
- `total_fee_min`, `total_fee_max`: fee range
- `min_create_or_open_ts`, `max_create_or_open_ts`: creation/open time range

Example:

```python
from gmgn_sdk import TokenSignalGroup

with GMGNClient.from_env() as client:
    signals = client.getTokenSignalV2(
        "sol",
        [
            TokenSignalGroup(
                signal_type=[12],
                mc_min=100_000,
                mc_max=10_000_000,
            )
        ],
    )
    print(signals)
```

### Wallet and Account Methods

Use these methods when the primary object is a wallet, account, KOL list, or
GMGN user state.

#### `getWalletHoldings(chain, wallet_address, extra=None)`

Scenario:

- List tokens held by one wallet.
- Useful for portfolio snapshots, wallet-copy discovery, and monitoring a
  smart wallet.

Parameters:

- `chain`: chain identifier
- `wallet_address`: wallet address
- `extra`: optional query fields such as `limit`, `order_by`, and `direction`

Example:

```python
wallet = "0x0000000000000000000000000000000000000001"

with GMGNClient.from_env() as client:
    holdings = client.getWalletHoldings(
        "eth",
        wallet,
        extra={"limit": 20, "order_by": "usd_value", "direction": "desc"},
    )
```

#### `getWalletActivity(chain, wallet_address, extra=None)`

Scenario:

- Fetch recent wallet trading activity.
- Useful for tracking what a wallet is buying or selling now.

Parameters:

- `chain`: chain identifier
- `wallet_address`: wallet address
- `extra`: optional query fields such as pagination, filters, or ordering

Example:

```python
with GMGNClient.from_env() as client:
    activity = client.getWalletActivity(
        "sol",
        "11111111111111111111111111111111",
        extra={"limit": 50},
    )
```

#### `getWalletStats(chain, wallet_addresses, period="7d")`

Scenario:

- Compare performance and summary statistics for multiple wallets.
- Useful when ranking wallets before building a follow list.

Parameters:

- `chain`: chain identifier
- `wallet_addresses`: sequence of wallet addresses
- `period`: GMGN period string such as `7d`, depending on upstream support

Example:

```python
wallets = [
    "0x0000000000000000000000000000000000000001",
    "0x0000000000000000000000000000000000000002",
]

with GMGNClient.from_env() as client:
    stats = client.getWalletStats("eth", wallets, period="7d")
```

#### `getWalletTokenBalance(chain, wallet_address, token_address)`

Scenario:

- Fetch one wallet's balance for one token.
- Use before selling, before strategy placement, or when validating a position.

Parameters:

- `chain`: chain identifier
- `wallet_address`: wallet address
- `token_address`: token contract address

Example:

```python
with GMGNClient.from_env() as client:
    balance = client.getWalletTokenBalance("eth", wallet, "0x1111111111111111111111111111111111111111")
```

#### `getUserInfo()`

Scenario:

- Check the authenticated GMGN account associated with `GMGN_API_KEY`.
- Useful as a lightweight auth smoke test.

Parameters:

- none

Example:

```python
with GMGNClient.from_env() as client:
    user = client.getUserInfo()
    print(user)
```

#### `getFollowWallet(chain, extra=None)`

Scenario:

- Read followed-wallet configuration or followed-wallet data from GMGN.
- This is a critical-auth `GET`, so it requires `GMGN_PRIVATE_KEY`.

Parameters:

- `chain`: chain identifier
- `extra`: optional upstream query fields

Example:

```python
with GMGNClient.from_env() as client:
    followed = client.getFollowWallet("sol", extra={"limit": 50})
```

#### `getKol(chain=None, limit=None)`

Scenario:

- Fetch GMGN KOL wallet data.
- Useful as a discovery source before tracking wallets or comparing wallet
  holdings.

Parameters:

- `chain`: optional chain filter
- `limit`: optional result limit

Example:

```python
with GMGNClient.from_env() as client:
    kols = client.getKol("sol", limit=20)
```

#### `getSmartMoney(chain=None, limit=None)`

Scenario:

- Fetch GMGN smart-money wallet data.
- Useful for discovering wallets to monitor or for cross-checking whether a
  token has smart-money involvement.

Parameters:

- `chain`: optional chain filter
- `limit`: optional result limit

Example:

```python
with GMGNClient.from_env() as client:
    smart_money = client.getSmartMoney("sol", limit=20)
```

#### `getCreatedTokens(chain, wallet_address, extra=None)`

Scenario:

- List tokens created by a wallet.
- Useful for developer due diligence, creator-history checks, and filtering out
  mass token creators.

Parameters:

- `chain`: chain identifier
- `wallet_address`: creator wallet address
- `extra`: optional upstream query fields

Example:

```python
with GMGNClient.from_env() as client:
    created = client.getCreatedTokens(
        "sol",
        "11111111111111111111111111111111",
        extra={"limit": 20},
    )
```

### Trading and Order Methods

Trading routes use critical auth and require `GMGN_PRIVATE_KEY`.

Safety notes:

- `quoteOrder` is a `GET` and can be retried once on eligible rate limits.
- `swap`, `multiSwap`, `createStrategyOrder`, `cancelStrategyOrder`, and
  `createToken` are critical-auth `POST` methods and are never automatically
  retried by the SDK.
- Amount fields are raw integer strings in the unit expected by GMGN for that
  chain and token. The SDK does not convert from SOL, ETH, BNB, gwei, or token
  decimals.

#### `quoteOrder(chain, from_address, input_token, output_token, input_amount, slippage)`

Scenario:

- Fetch a quote before submitting a swap.
- Use this as the first step in any trading workflow.

Parameters:

- `chain`: chain identifier
- `from_address`: wallet submitting the trade
- `input_token`: token being sold
- `output_token`: token being bought
- `input_amount`: raw integer amount string
- `slippage`: decimal percent, for example `0.01`

Example:

```python
with GMGNClient.from_env() as client:
    quote = client.quoteOrder(
        chain="eth",
        from_address="0x0000000000000000000000000000000000000001",
        input_token="0x0000000000000000000000000000000000000000",
        output_token="0x1111111111111111111111111111111111111111",
        input_amount="10000000000000000",
        slippage=0.01,
    )
```

#### `swap(params)`

Scenario:

- Submit one market swap from one wallet.
- Use `SwapParams` for clearer code, or pass a dictionary when you need fields
  not modeled yet.

Parameters:

- `params`: `SwapParams` or mapping

Example:

```python
from gmgn_sdk import SwapParams

with GMGNClient.from_env() as client:
    result = client.swap(
        SwapParams(
            chain="eth",
            from_address="0x0000000000000000000000000000000000000001",
            input_token="0x0000000000000000000000000000000000000000",
            output_token="0x1111111111111111111111111111111111111111",
            input_amount="10000000000000000",
            slippage=0.01,
            is_anti_mev=True,
        )
    )
```

#### `multiSwap(params)`

Scenario:

- Submit a batch swap across multiple accounts.
- Use when you intentionally want multiple wallets to execute the same token
  route with account-specific amounts.

Parameters:

- `params`: `MultiSwapParams` or mapping

Example:

```python
from gmgn_sdk import MultiSwapParams

with GMGNClient.from_env() as client:
    result = client.multiSwap(
        MultiSwapParams(
            chain="bsc",
            accounts=[
                "0x0000000000000000000000000000000000000001",
                "0x0000000000000000000000000000000000000002",
            ],
            input_token="0x0000000000000000000000000000000000000000",
            output_token="0x1111111111111111111111111111111111111111",
            input_amount={
                "0x0000000000000000000000000000000000000001": "10000000000000000",
                "0x0000000000000000000000000000000000000002": "20000000000000000",
            },
            slippage=0.01,
        )
    )
```

#### `queryOrder(order_id, chain)`

Scenario:

- Poll or inspect an order after a swap or strategy operation.
- Use this after a trade submission returns an order id.

Parameters:

- `order_id`: GMGN order id
- `chain`: chain identifier

Example:

```python
with GMGNClient.from_env() as client:
    order = client.queryOrder("your-order-id", "sol")
    print(order)
```

#### `createStrategyOrder(params)`

Scenario:

- Create a limit, take-profit, stop-loss, or advanced strategy order.
- Use `StrategyCreateParams` for modeled fields, or pass a mapping for advanced
  upstream fields.

Parameters:

- `params`: `StrategyCreateParams` or mapping

Example:

```python
from gmgn_sdk import StrategyCreateParams

with GMGNClient.from_env() as client:
    order = client.createStrategyOrder(
        StrategyCreateParams(
            chain="eth",
            from_address="0x0000000000000000000000000000000000000001",
            base_token="0x1111111111111111111111111111111111111111",
            quote_token="0x0000000000000000000000000000000000000000",
            order_type="limit",
            sub_order_type="buy",
            check_price="0.000001",
            amount_in="10000000000000000",
            slippage=0.01,
        )
    )
```

#### `getStrategyOrders(chain, from_address, extra=None)`

Scenario:

- List open or historical strategy orders for a wallet.
- Use before displaying active orders or deciding what to cancel.

Parameters:

- `chain`: chain identifier
- `from_address`: wallet address
- `extra`: optional query fields such as status, pagination, or filters

Example:

```python
with GMGNClient.from_env() as client:
    orders = client.getStrategyOrders(
        "eth",
        "0x0000000000000000000000000000000000000001",
        extra={"limit": 20},
    )
```

#### `cancelStrategyOrder(params)`

Scenario:

- Cancel an existing strategy order.
- Use `getStrategyOrders` first if you need to discover the order id.

Parameters:

- `params`: `StrategyCancelParams` or mapping

Example:

```python
from gmgn_sdk import StrategyCancelParams

with GMGNClient.from_env() as client:
    result = client.cancelStrategyOrder(
        StrategyCancelParams(
            chain="eth",
            from_address="0x0000000000000000000000000000000000000001",
            order_id="your-order-id",
            order_type="limit",
        )
    )
```

### Cooking and Token-Creation Methods

These methods cover GMGN cooking statistics and token creation.

#### `getCookingStatistics()`

Scenario:

- Fetch GMGN cooking statistics.
- Useful for dashboards or operational checks around token creation activity.

Parameters:

- none

Example:

```python
with GMGNClient.from_env() as client:
    stats = client.getCookingStatistics()
```

#### `createToken(params)`

Scenario:

- Create a token through GMGN's cooking route.
- This is a critical-auth `POST`. It can have real on-chain effects and is not
  live-tested by this repository's default verification flow.

Parameters:

- `params`: `CreateTokenParams` or mapping

Supported chains:

- General SDK routes support `sol`, `bsc`, `base`, `eth`, and `monad`.
- `createToken` additionally allows `ton`.

Example:

```python
from gmgn_sdk import CreateTokenParams

with GMGNClient.from_env() as client:
    result = client.createToken(
        CreateTokenParams(
            chain="ton",
            dex="stonfi",
            from_address="wallet-address",
            name="Example",
            symbol="EXM",
            buy_amt="1000",
            image_url="https://example.com/token.png",
            website="https://example.com",
            twitter="https://x.com/example",
            telegram="https://t.me/example",
            slippage=0.01,
            is_anti_mev=True,
        )
    )
```

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
