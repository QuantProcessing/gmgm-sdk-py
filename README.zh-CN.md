# GMGN SDK

[English](README.md) | [简体中文](README.zh-CN.md)

这是一个面向 GMGN OpenAPI 的 Python SDK，按照官方 TypeScript
`gmgn-cli` / `OpenApiClient` 的接口面移植。

这是非官方社区项目，不是 GMGN 官方发布的 SDK，也不应被描述为官方
GMGN SDK。

这个仓库只提供 SDK：

- 不提供 Python CLI 封装
- 主包内不提供 mock transport
- 成功时方法返回 GMGN 响应中的 `data` 字段，而不是完整的
  `{code, message, data}` envelope
- GMGN 返回非零 `code` 时会抛出结构化 Python 异常

当前 SDK 覆盖官方 TypeScript `OpenApiClient` 的全部 27 个方法，包括普通鉴权、
关键鉴权、请求签名、限流重试规则和 live swap 验证路径。

## 功能范围

- 官方 GMGN 方法完整对齐：`27` 个方法
- 两种鉴权模式：
  - 普通鉴权：`X-APIKEY`
  - 关键鉴权：`X-APIKEY` + `X-Signature`
- 关键鉴权支持 Ed25519 和 RSA 私钥
- 同步 `httpx` 客户端
- 使用预构造 URL、body bytes、headers 发送请求
- swap 类接口支持自定义 fee 和 anti-MEV 字段
- 同时支持官方 `camelCase` 方法名和 Python 风格 `snake_case` 别名

## 安装

本地开发安装：

```bash
python3 -m pip install -e '.[dev]'
```

构建发布包：

```bash
python3 -m build
```

构建产物：

- `dist/gmgn_sdk-0.1.0.tar.gz`
- `dist/gmgn_sdk-0.1.0-py3-none-any.whl`

## Python 版本和依赖

- Python `>=3.11`
- 运行时依赖：
  - `httpx`
  - `cryptography`
- 开发依赖：
  - `pytest`
  - `pytest-mock`
  - `ruff`
  - `mypy`
  - `build`

## 快速开始

```python
from gmgn_sdk import GMGNClient

client = GMGNClient.from_env()
token = client.getTokenInfo("sol", "So11111111111111111111111111111111111111112")
print(token)
client.close()
```

推荐使用 context manager：

```python
from gmgn_sdk import GMGNClient

with GMGNClient.from_env() as client:
    data = client.getUserInfo()
    print(data)
```

显式传入配置：

```python
from gmgn_sdk import GMGNClient

client = GMGNClient(
    api_key="your-api-key",
    private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)
```

使用配置对象：

```python
from gmgn_sdk import GMGNClient, GMGNConfig

config = GMGNConfig(
    api_key="your-api-key",
    private_key_pem="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)

client = GMGNClient(config)
```

## 配置

配置加载顺序如下，后加载的来源会覆盖前面的来源：

1. `~/.config/gmgn/.env`
2. 项目目录 `.env`
3. 当前进程环境变量

支持的环境变量：

- `GMGN_API_KEY`
- `GMGN_PRIVATE_KEY`
- `GMGN_HOST`
- `GMGN_DEBUG`
- `GMGN_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS`

### 必填变量

所有请求都需要：

- `GMGN_API_KEY`

关键鉴权方法还需要：

- `GMGN_PRIVATE_KEY`

可选变量：

- `GMGN_HOST`
  - 默认：`https://openapi.gmgn.ai`
- `GMGN_DEBUG`
  - 支持 `1`、`true`、`yes`、`on`
  - 开启后会打印已脱敏的请求和响应调试信息
- `GMGN_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS`
  - 控制限流响应自动重试的最大等待时间

### 私钥格式

`GMGN_PRIVATE_KEY` 支持以下形式。

单行转义换行：

```dotenv
GMGN_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
```

带引号的多行形式：

```dotenv
GMGN_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----
...
-----END PRIVATE KEY-----"
```

内存字符串：

```python
client = GMGNClient(
    api_key="...",
    private_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----",
)
```

## 鉴权模式

### 普通鉴权

普通鉴权请求包含：

- query 参数：`timestamp`、`client_id`
- header：`X-APIKEY`

### 关键鉴权

关键鉴权请求包含：

- query 参数：`timestamp`、`client_id`
- headers：
  - `X-APIKEY`
  - `X-Signature`

签名消息格式与官方 TypeScript 客户端一致：

```text
{sub_path}:{sorted_query_string}:{request_body}:{timestamp}
```

重要细节：

- 签名时 query key 按字母序排序
- 数组 query 值会以重复 `k=v` 的形式序列化，并按 value 排序
- 实际请求 URL 保持构造时的 query 插入顺序，以对齐 TypeScript 行为
- Ed25519 对原始 message bytes 签名
- RSA 使用 `RSA-PSS + SHA256`，salt length 为 `32`

## 请求和响应行为

成功时，SDK 方法返回：

- GMGN 响应中的 `data` 字段

失败时，SDK 会抛出：

- `GMGNConfigurationError`
- `GMGNValidationError`
- `GMGNTransportError`
- `GMGNAPIError`

### 重试策略

SDK 只对部分限流响应自动重试一次：

- 所有普通鉴权请求
- 关键鉴权 `GET` 请求

不会自动重试：

- 关键鉴权 `POST` 请求

因此 `swap`、`multiSwap`、`createStrategyOrder`、`cancelStrategyOrder` 和
`createToken` 不会被 SDK 自动二次提交。

### 传输层保证

SDK 发送的是：

- 已构造好的完整 URL
- 已构造好的 body bytes
- 显式 headers

SDK 不依赖 `httpx` 的便利序列化参数：

- `params=`
- `json=`

这对签名请求很重要，因为签名必须覆盖最终发送的精确 bytes。

## 支持链

通用路由校验支持：

- `sol`
- `bsc`
- `base`
- `eth`
- `monad`

`createToken` 额外支持：

- `ton`

当前仓库 live acceptance 覆盖：

- `sol`
- `eth`
- `bsc`

## 公开 API

包导出：

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

## 方法对照表

| 方法 | HTTP | 路径 | 鉴权 |
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

程序化读取方法表：

```python
from gmgn_sdk import GMGNClient

for item in GMGNClient.method_parity():
    print(item.name, item.http_method, item.path, item.auth_mode)
```

## Snake Case 别名

SDK 同时暴露 Python 风格别名。

| 官方方法 | Python 别名 |
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

别名调用的是同一套底层实现。

## 详细方法使用指南

这一节覆盖全部 27 个 SDK 方法，说明适用场景、关键参数和示例。

### 如何选择市场发现方法

GMGN 的市场类接口看起来相似，但适用场景不同。

| 目标 | 使用方法 | 原因 |
| --- | --- | --- |
| 已知代币地址，查询详情 | `getTokenInfo`、`getTokenSecurity`、`getTokenPoolInfo` | 直接按地址查单个 token |
| 找新创建、快毕业、刚毕业的 launchpad token | `getTrenches` | launchpad 当前窗口，适合新币扫描 |
| 找已经上市且当前交易活跃的 token | `getTrendingSwaps` | rank feed，适合老一些但仍活跃的 token |
| 按信号、触发市值、smart money 等事件筛选 | `getTokenSignalV2` | signal feed，适合事件驱动筛选 |

非常重要：

- `getTrenches` 不是全量历史 token 数据库。
- `getTrenches(..., limit=80)` 返回每个 category 当前窗口中的结果。
- 已经迁移多日的 Pump.fun token，即使市值和成交量很高，也可能不在
  `getTrenches` 当前窗口里。
- 这类已经上市且仍活跃的 token 应该用 `getTrendingSwaps`，然后在客户端按
  `market_cap >= 10_000_000`、`launchpad_platform == "Pump.fun"` 等条件过滤。

### Rank 响应辅助函数

多数方法直接返回 GMGN 的 `data` 字段。但部分 market 响应中仍可能包含一层
上游原始 `data`。rank 类结果建议用防御式提取：

```python
def extract_rank(payload: dict) -> list[dict]:
    if isinstance(payload.get("rank"), list):
        return payload["rank"]
    nested = payload.get("data")
    if isinstance(nested, dict) and isinstance(nested.get("rank"), list):
        return nested["rank"]
    return []
```

### Token 研究方法

#### `getTokenInfo(chain, address)`

场景：

- 查询一个 token 的基础档案、价格、供应量、流动性、launchpad、pool、
  developer、社交链接和钱包标签统计。
- 适合作为任何 token 尽调流程的第一步。

参数：

- `chain`：`sol`、`bsc`、`base`、`eth` 或 `monad`
- `address`：token 合约地址

示例：

```python
from gmgn_sdk import GMGNClient

token_address = "So11111111111111111111111111111111111111112"

with GMGNClient.from_env() as client:
    info = client.getTokenInfo("sol", token_address)
    print(info.get("symbol"), info.get("price"), info.get("liquidity"))
```

#### `getTokenSecurity(chain, address)`

场景：

- 交易或排序前检查风险字段。
- Solana 上重点看 mint/freeze 是否放弃、top holder 集中度、burn 状态、
  tax 字段和 alert。
- EVM 链上重点看 honeypot、open source、renounced、blacklist、tax。

参数：

- `chain`：链名
- `address`：token 合约地址

示例：

```python
with GMGNClient.from_env() as client:
    security = client.getTokenSecurity("sol", token_address)
    if security.get("renounced_mint") and security.get("renounced_freeze_account"):
        print("Solana mint/freeze authority renounced")
```

#### `getTokenPoolInfo(chain, address)`

场景：

- 查询主池信息。
- 适合在 swap 前检查流动性深度、quote token、pool address。

参数：

- `chain`：链名
- `address`：token 合约地址

示例：

```python
with GMGNClient.from_env() as client:
    pool = client.getTokenPoolInfo("sol", token_address)
    print(pool.get("pool_address"), pool.get("quote_symbol"), pool.get("liquidity"))
```

#### `getTokenTopHolders(chain, address, extra=None)`

场景：

- 查询 top holders 和持仓集中度。
- 如果 `getTokenSecurity` 显示 holder 集中度偏高，可以继续查这个接口。

参数：

- `chain`：链名
- `address`：token 合约地址
- `extra`：透传上游支持的分页、limit、排序等 query 字段

示例：

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

场景：

- 查看一个 token 的活跃交易者、盈利交易者或可疑交易者。
- 适合判断成交量是否自然，或找 smart wallets。

参数：

- `chain`：链名
- `address`：token 合约地址
- `extra`：透传 query 字段

示例：

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

场景：

- 拉取 OHLCV / K 线数据。
- 适合画图、计算成交量、判断趋势和波动。

参数：

- `chain`：链名
- `address`：token 合约地址
- `resolution`：`1m`、`5m`、`15m`、`1h`、`4h`、`1d`
- `from_`：可选，Unix timestamp，单位毫秒
- `to`：可选，Unix timestamp，单位毫秒

注意：

- 这个 SDK 直接透传 `from_` 和 `to`。
- 请传毫秒。官方 CLI 可以接收秒并转换，但 SDK 不做这层转换。

示例：

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

### 市场发现方法

#### `getTrenches(chain, types=None, platforms=None, limit=None, filters=None)`

场景：

- 扫描 launchpad token 的生命周期窗口：
  - `new_creation`：刚创建
  - `near_completion`：bonding curve 接近完成，响应里会放在 `pump` key 下
  - `completed`：刚毕业 / 刚迁移
- 适合新币扫描、launchpad 监控、"刚发射的 token" 场景。

参数：

- `chain`：通常用于 `sol`、`bsc`、`base`
- `types`：生命周期列表
- `platforms`：launchpad 平台列表
- `limit`：每个 category 的最大数量
- `filters`：服务端过滤字段，会合并到每个 category 请求体中

常见 Solana launchpad：

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

常用服务端过滤字段：

| 字段 | 含义 |
| --- | --- |
| `min_marketcap`, `max_marketcap` | 市值范围，USD |
| `min_liquidity`, `max_liquidity` | 流动性范围，USD |
| `min_volume_24h`, `max_volume_24h` | 24h 成交额范围，USD |
| `min_net_buy_24h`, `max_net_buy_24h` | 24h 净买入范围 |
| `min_swaps_24h`, `max_swaps_24h` | 24h swap 次数 |
| `min_buys_24h`, `max_buys_24h` | 24h 买入次数 |
| `min_sells_24h`, `max_sells_24h` | 24h 卖出次数 |
| `min_holder_count`, `max_holder_count` | holder 数量 |
| `min_top_holder_rate`, `max_top_holder_rate` | top10 holder 集中度 |
| `min_rug_ratio`, `max_rug_ratio` | rug 风险分数 |
| `min_bundler_rate`, `max_bundler_rate` | bundler 交易比例 |
| `min_insider_ratio`, `max_insider_ratio` | insider / rat trader 比例 |
| `min_smart_degen_count`, `max_smart_degen_count` | smart money holder 数 |
| `min_renowned_count`, `max_renowned_count` | KOL / renowned 钱包数 |
| `min_x_follower`, `max_x_follower` | X/Twitter 粉丝数 |
| `min_tg_call_count`, `max_tg_call_count` | Telegram call 次数 |
| `min_created`, `max_created` | token 年龄，例如 `30m`、`1h`、`24h` |

示例：筛选 Solana 上更像 meme launchpad 的候选池：

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

示例：市值大于 1000 万，并在客户端要求有社交链接：

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

如果一个已知 token 没出现在 `getTrenches`：

- 先用 `getTokenInfo` 确认 token 是否存在
- 如果它已经迁移较久，用 `getTrendingSwaps`
- 不要把 `getTrenches` 当作 Pump.fun 历史全量库

#### `getTrendingSwaps(chain, interval, extra=None)`

场景：

- 查询当前活跃交易 token 的 rank。
- 适合已经迁移、已经上市、或者市值更高但仍有成交量的 token。
- 对老一些的 Pump.fun token，比 `getTrenches` 更合适。

参数：

- `chain`：链名
- `interval`：`1m`、`5m`、`1h`、`6h`、`24h`
- `extra`：透传 query 参数，例如 `limit`、`order_by`、`direction`、
  `filters`、`platforms`

常见 `order_by`：

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

常见 Solana `filters`：

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

示例：筛选 24h 活跃、Pump.fun、MC 大于 1000 万的 token：

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

场景：

- 按 GMGN signal 查询 token。
- 适合价格异动、smart money、large buy、Dexscreener 事件、市值触发等场景。

参数：

- `chain`：通常用于 `sol` 和 `bsc`
- `groups`：`TokenSignalGroup` 或 dict 列表

常用字段：

- `signal_type`：GMGN signal id 列表
- `mc_min`、`mc_max`：当前市值范围
- `trigger_mc_min`、`trigger_mc_max`：触发时市值范围
- `total_fee_min`、`total_fee_max`：fee 范围
- `min_create_or_open_ts`、`max_create_or_open_ts`：创建或上市时间范围

示例：

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

### 钱包和账户方法

#### `getWalletHoldings(chain, wallet_address, extra=None)`

场景：

- 查询某个钱包当前持仓。
- 适合做组合快照、钱包跟单发现、smart wallet 监控。

参数：

- `chain`：链名
- `wallet_address`：钱包地址
- `extra`：分页、排序、limit 等 query 字段

示例：

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

场景：

- 查询钱包最近交易动态。
- 适合跟踪某个钱包正在买什么、卖什么。

参数：

- `chain`：链名
- `wallet_address`：钱包地址
- `extra`：分页、过滤或排序字段

示例：

```python
with GMGNClient.from_env() as client:
    activity = client.getWalletActivity(
        "sol",
        "11111111111111111111111111111111",
        extra={"limit": 50},
    )
```

#### `getWalletStats(chain, wallet_addresses, period="7d")`

场景：

- 批量查询钱包统计，用来比较多个钱包表现。
- 适合筛选值得跟踪的钱包。

参数：

- `chain`：链名
- `wallet_addresses`：钱包地址列表
- `period`：周期，例如 `7d`

示例：

```python
wallets = [
    "0x0000000000000000000000000000000000000001",
    "0x0000000000000000000000000000000000000002",
]

with GMGNClient.from_env() as client:
    stats = client.getWalletStats("eth", wallets, period="7d")
```

#### `getWalletTokenBalance(chain, wallet_address, token_address)`

场景：

- 查询某钱包对某 token 的余额。
- 适合卖出前、创建策略前、检查仓位时使用。

参数：

- `chain`：链名
- `wallet_address`：钱包地址
- `token_address`：token 地址

示例：

```python
with GMGNClient.from_env() as client:
    balance = client.getWalletTokenBalance(
        "eth",
        wallet,
        "0x1111111111111111111111111111111111111111",
    )
```

#### `getUserInfo()`

场景：

- 查询当前 `GMGN_API_KEY` 对应的 GMGN 账户信息。
- 适合作为轻量鉴权 smoke test。

参数：

- 无

示例：

```python
with GMGNClient.from_env() as client:
    user = client.getUserInfo()
    print(user)
```

#### `getFollowWallet(chain, extra=None)`

场景：

- 查询 GMGN follow wallet 相关数据。
- 这是关键鉴权 `GET`，需要 `GMGN_PRIVATE_KEY`。

参数：

- `chain`：链名
- `extra`：透传 query 字段

示例：

```python
with GMGNClient.from_env() as client:
    followed = client.getFollowWallet("sol", extra={"limit": 50})
```

#### `getKol(chain=None, limit=None)`

场景：

- 查询 GMGN KOL 钱包数据。
- 可作为钱包发现、持仓对比或跟踪列表来源。

参数：

- `chain`：可选链过滤
- `limit`：可选数量限制

示例：

```python
with GMGNClient.from_env() as client:
    kols = client.getKol("sol", limit=20)
```

#### `getSmartMoney(chain=None, limit=None)`

场景：

- 查询 GMGN smart money 钱包数据。
- 适合发现要监控的钱包，或交叉验证 token 是否有 smart money 参与。

参数：

- `chain`：可选链过滤
- `limit`：可选数量限制

示例：

```python
with GMGNClient.from_env() as client:
    smart_money = client.getSmartMoney("sol", limit=20)
```

#### `getCreatedTokens(chain, wallet_address, extra=None)`

场景：

- 查询某钱包创建过的 token。
- 适合做 dev 尽调、creator 历史检查、排除批量发币地址。

参数：

- `chain`：链名
- `wallet_address`：creator 钱包地址
- `extra`：分页、limit 等 query 字段

示例：

```python
with GMGNClient.from_env() as client:
    created = client.getCreatedTokens(
        "sol",
        "11111111111111111111111111111111",
        extra={"limit": 20},
    )
```

### 交易和订单方法

这些方法使用关键鉴权，需要 `GMGN_PRIVATE_KEY`。

安全说明：

- `quoteOrder` 是 `GET`，遇到符合条件的限流响应时可以自动重试一次。
- `swap`、`multiSwap`、`createStrategyOrder`、`cancelStrategyOrder` 和
  `createToken` 是关键鉴权 `POST`，SDK 不会自动重试。
- 金额字段一般是链或 token 对应的 raw integer string。SDK 不会把 SOL、ETH、
  BNB、gwei 或 token 小数自动换算成 raw unit。

#### `quoteOrder(chain, from_address, input_token, output_token, input_amount, slippage)`

场景：

- 下单前获取 quote。
- 任何交易流程都建议先调用这个方法。

参数：

- `chain`：链名
- `from_address`：交易钱包
- `input_token`：卖出 token
- `output_token`：买入 token
- `input_amount`：raw integer 字符串
- `slippage`：滑点，例如 `0.01`

示例：

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

场景：

- 单钱包提交一次 market swap。
- 推荐使用 `SwapParams`，需要透传未建模字段时也可以传 dict。

参数：

- `params`：`SwapParams` 或 mapping

示例：

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

场景：

- 多钱包批量 swap。
- 每个账户可以有自己的输入金额。

参数：

- `params`：`MultiSwapParams` 或 mapping

示例：

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

场景：

- swap 或 strategy 提交后查询订单状态。

参数：

- `order_id`：GMGN order id
- `chain`：链名

示例：

```python
with GMGNClient.from_env() as client:
    order = client.queryOrder("your-order-id", "sol")
    print(order)
```

#### `createStrategyOrder(params)`

场景：

- 创建 limit、take-profit、stop-loss 或其他策略订单。
- 推荐使用 `StrategyCreateParams`。

参数：

- `params`：`StrategyCreateParams` 或 mapping

示例：

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

场景：

- 查询钱包的策略订单列表。
- 展示活跃订单或决定取消哪个订单前使用。

参数：

- `chain`：链名
- `from_address`：钱包地址
- `extra`：状态、分页、过滤等 query 字段

示例：

```python
with GMGNClient.from_env() as client:
    orders = client.getStrategyOrders(
        "eth",
        "0x0000000000000000000000000000000000000001",
        extra={"limit": 20},
    )
```

#### `cancelStrategyOrder(params)`

场景：

- 取消已有策略订单。
- 如果不知道 order id，先调用 `getStrategyOrders`。

参数：

- `params`：`StrategyCancelParams` 或 mapping

示例：

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

### Cooking 和发币方法

#### `getCookingStatistics()`

场景：

- 查询 GMGN cooking 统计。
- 适合仪表盘或发币活动监控。

参数：

- 无

示例：

```python
with GMGNClient.from_env() as client:
    stats = client.getCookingStatistics()
```

#### `createToken(params)`

场景：

- 通过 GMGN cooking route 创建 token。
- 这是关键鉴权 `POST`，可能产生真实链上影响。
- 仓库默认 live verification 不会真实执行发币。

参数：

- `params`：`CreateTokenParams` 或 mapping

支持链：

- 通用 SDK 路由支持 `sol`、`bsc`、`base`、`eth`、`monad`
- `createToken` 额外允许 `ton`

示例：

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

## 请求模型

复杂路由支持 dataclass payload。

### `SwapParams`

用于 `client.swap(...)`。

核心字段：

- `chain`
- `from_address`
- `input_token`
- `output_token`
- `input_amount`

可选执行字段：

- `swap_mode`
- `input_amount_bps`
- `output_amount`
- `slippage`
- `auto_slippage`
- `min_output_amount`
- `condition_orders`
- `sell_ratio_type`

fee 和 anti-MEV 字段：

- `is_anti_mev`
- `priority_fee`
- `tip_fee`
- `auto_tip_fee`
- `max_auto_fee`
- `gas_price`
- `max_fee_per_gas`
- `max_priority_fee_per_gas`

### `MultiSwapParams`

用于 `client.multiSwap(...)`。

核心字段：

- `chain`
- `accounts`
- `input_token`
- `output_token`

金额字段：

- `input_amount`
- `input_amount_bps`
- `output_amount`

也支持与 `SwapParams` 类似的 fee 和 anti-MEV 字段。

### `StrategyCreateParams`

用于 `client.createStrategyOrder(...)`。

核心字段：

- `chain`
- `from_address`
- `base_token`
- `quote_token`
- `order_type`
- `sub_order_type`
- `check_price`

可选字段：

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

### `StrategyCancelParams`

用于 `client.cancelStrategyOrder(...)`。

字段：

- `chain`
- `from_address`
- `order_id`
- `order_type`
- `close_sell_model`

### `TokenSignalGroup`

用于 `client.getTokenSignalV2(...)`。

字段：

- `signal_type`
- `mc_min`
- `mc_max`
- `trigger_mc_min`
- `trigger_mc_max`
- `total_fee_min`
- `total_fee_max`
- `min_create_or_open_ts`
- `max_create_or_open_ts`

### `CreateTokenParams`

用于 `client.createToken(...)`。

核心字段：

- `chain`
- `dex`
- `from_address`
- `name`
- `symbol`
- `buy_amt`

可选元数据字段：

- `image`
- `image_url`
- `website`
- `twitter`
- `telegram`

可选执行字段：

- `slippage`
- `auto_slippage`
- `priority_fee`
- `tip_fee`
- `gas_price`
- `max_priority_fee_per_gas`
- `max_fee_per_gas`
- `is_anti_mev`
- `anti_mev_mode`

## 校验规则

SDK 会在发送请求前做有限但明确的客户端校验：

- 链名是否合法
- Solana / EVM 地址格式
- raw token amount 是否为正整数字符串
- `slippage` 等百分比字段是否在合理范围
- live test harness 中的 native spend cap

边界：

- SDK 只校验明显错误输入
- 不尝试复刻 CLI 的全部单位转换和业务规则
- `gas_price`、`priority_fee` 等 route-specific 数值字段会按 raw string 透传

## Fee 调优和 Anti-MEV

swap、multi-swap、strategy、create-token 路由支持：

- `is_anti_mev=True`
- `priority_fee="..."`
- `tip_fee="..."`
- `auto_tip_fee=True`
- `max_auto_fee="..."`
- `gas_price="..."`
- `max_fee_per_gas="..."`
- `max_priority_fee_per_gas="..."`

示例：

```python
from gmgn_sdk import GMGNClient, SwapParams

with GMGNClient.from_env() as client:
    result = client.swap(
        SwapParams(
            chain="bsc",
            from_address="0x0000000000000000000000000000000000000001",
            input_token="0x0000000000000000000000000000000000000000",
            output_token="0x1111111111111111111111111111111111111111",
            input_amount="10000000000000000",
            slippage=0.01,
            is_anti_mev=True,
            gas_price="50000000",
            tip_fee="1000000000000",
        )
    )
```

注意：

- 这个 SDK 比 TypeScript CLI wrapper 更底层。
- SDK 不会把 `gwei` 等用户友好单位转换为 raw string。
- 从 CLI 示例迁移时，请确认 CLI 是否曾做额外单位转换。

## 错误处理

### `GMGNAPIError`

GMGN 返回非零 envelope code 时抛出。

常用字段：

- `method`
- `path`
- `status_code`
- `api_code`
- `api_error`
- `api_message`
- `rate_limit_reset`
- `reset_at_unix`

示例：

```python
from gmgn_sdk import GMGNAPIError, GMGNClient

try:
    with GMGNClient.from_env() as client:
        client.getUserInfo()
except GMGNAPIError as exc:
    print(exc.status_code, exc.api_error, exc.api_message)
```

### 其他异常

- `GMGNConfigurationError`
  - 缺少 API key、构造参数混用、关键鉴权缺少私钥
- `GMGNValidationError`
  - 链名、地址、百分比、raw integer 格式错误
- `GMGNTransportError`
  - 请求失败或响应无法解析

## Live 验证

Live swap 验证见 [`docs/live-verification.md`](docs/live-verification.md)。

概览：

- live tests 需要显式设置 `RUN_LIVE_GMGN=1`
- 当前 live swap acceptance 覆盖 `sol`、`eth`、`bsc`
- test harness 会限制 native spend cap
- `createToken` 已实现，但默认 live verification 不执行真实发币

验证命令：

```bash
python3 -m pytest tests/unit
python3 -m pytest tests/integration
RUN_LIVE_GMGN=1 python3 -m pytest tests/live/test_live_swaps.py -m live
```

## 开发验证

Lint：

```bash
python3 -m ruff check .
```

类型检查：

```bash
python3 -m mypy src
```

单元测试：

```bash
python3 -m pytest tests/unit
```

集成测试：

```bash
python3 -m pytest tests/integration
```

构建：

```bash
python3 -m build
```

## 实用注意事项

- 不要把 `getTrenches` 当作历史全量 token screener。
- 想筛当前活跃 token，用 `getTrendingSwaps`。
- 想筛新创建 / 快毕业 / 刚迁移 token，用 `getTrenches`。
- 想查一个已知 token，先用 `getTokenInfo`，再补 `getTokenSecurity` 和
  `getTokenPoolInfo`。
- 想按市值筛 token：
  - trenches 用 `filters={"min_marketcap": ...}`
  - trending 用 `getTrendingSwaps` 拉 rank 后客户端过滤 `market_cap`
- 想更接近 meme 候选池，不要只靠市值；组合使用 launchpad、社交链接、
  流动性、volume、holder count、rug ratio、bundler ratio、insider ratio、
  smart money 等字段。
- 所有 live trading 示例都是真实交易能力。运行前确认地址、金额、滑点和费用。

## 当前边界

- SDK 返回 raw GMGN data，不做 typed response model。
- SDK 不提供 async client。
- SDK 不提供 CLI。
- SDK 不自动换算用户友好单位。
- `createToken` 请求构造有集成测试覆盖，但默认不做真实 live 创建。
