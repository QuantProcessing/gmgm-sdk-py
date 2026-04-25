from __future__ import annotations

from gmgn_sdk.models import MethodParitySpec

DEFAULT_HOST = "https://openapi.gmgn.ai"
NORMAL_AUTH = "normal"
CRITICAL_AUTH = "critical"
RATE_LIMIT_RETRY_BUFFER_MS = 1000
DEFAULT_RATE_LIMIT_AUTO_RETRY_MAX_WAIT_MS = 5000
DEFAULT_TIMEOUT_SECONDS = 10.0

VALID_CHAINS = frozenset({"sol", "bsc", "base", "eth", "monad"})
CREATE_TOKEN_VALID_CHAINS = frozenset({*VALID_CHAINS, "ton"})
EVM_CHAINS = frozenset({"bsc", "base", "eth", "monad"})
LIVE_NATIVE_SPEND_CAPS = {
    "sol": "0.1",
    "eth": "0.01",
    "bsc": "0.01",
}

REDACTED_HEADER_NAMES = frozenset({"x-apikey", "x-signature", "authorization"})
REDACTION_PLACEHOLDER = "***"

TRENCHES_PLATFORMS: dict[str, tuple[str, ...]] = {
    "sol": (
        "Pump.fun",
        "pump_mayhem",
        "pump_mayhem_agent",
        "pump_agent",
        "letsbonk",
        "bonkers",
        "bags",
        "memoo",
        "liquid",
        "bankr",
        "zora",
        "surge",
        "anoncoin",
        "moonshot_app",
        "wendotdev",
        "heaven",
        "sugar",
        "token_mill",
        "believe",
        "trendsfun",
        "trends_fun",
        "jup_studio",
        "Moonshot",
        "boop",
        "ray_launchpad",
        "meteora_virtual_curve",
        "xstocks",
    ),
    "bsc": (
        "fourmeme",
        "fourmeme_agent",
        "bn_fourmeme",
        "four_xmode_agent",
        "flap",
        "clanker",
        "lunafun",
    ),
    "base": (
        "clanker",
        "bankr",
        "flaunch",
        "zora",
        "zora_creator",
        "baseapp",
        "basememe",
        "virtuals_v2",
        "klik",
    ),
}

TRENCHES_QUOTE_ADDRESS_TYPES: dict[str, tuple[int, ...]] = {
    "sol": (4, 5, 3, 1, 13, 0),
    "bsc": (6, 7, 1, 16, 8, 3, 9, 10, 2, 17, 18, 0),
    "base": (11, 3, 12, 13, 0),
}

METHOD_PARITY_SPECS: tuple[MethodParitySpec, ...] = (
    MethodParitySpec("getTokenInfo", "GET", "/v1/token/info", NORMAL_AUTH),
    MethodParitySpec("getTokenSecurity", "GET", "/v1/token/security", NORMAL_AUTH),
    MethodParitySpec("getTokenPoolInfo", "GET", "/v1/token/pool_info", NORMAL_AUTH),
    MethodParitySpec("getTokenTopHolders", "GET", "/v1/market/token_top_holders", NORMAL_AUTH),
    MethodParitySpec("getTokenTopTraders", "GET", "/v1/market/token_top_traders", NORMAL_AUTH),
    MethodParitySpec("getTokenKline", "GET", "/v1/market/token_kline", NORMAL_AUTH),
    MethodParitySpec("getWalletHoldings", "GET", "/v1/user/wallet_holdings", NORMAL_AUTH),
    MethodParitySpec("getWalletActivity", "GET", "/v1/user/wallet_activity", NORMAL_AUTH),
    MethodParitySpec("getWalletStats", "GET", "/v1/user/wallet_stats", NORMAL_AUTH),
    MethodParitySpec("getWalletTokenBalance", "GET", "/v1/user/wallet_token_balance", NORMAL_AUTH),
    MethodParitySpec("getTrenches", "POST", "/v1/trenches", NORMAL_AUTH),
    MethodParitySpec("getTrendingSwaps", "GET", "/v1/market/rank", NORMAL_AUTH),
    MethodParitySpec("getTokenSignalV2", "POST", "/v1/market/token_signal", NORMAL_AUTH),
    MethodParitySpec("getUserInfo", "GET", "/v1/user/info", NORMAL_AUTH),
    MethodParitySpec("getFollowWallet", "GET", "/v1/trade/follow_wallet", CRITICAL_AUTH),
    MethodParitySpec("getKol", "GET", "/v1/user/kol", NORMAL_AUTH),
    MethodParitySpec("getSmartMoney", "GET", "/v1/user/smartmoney", NORMAL_AUTH),
    MethodParitySpec("getCreatedTokens", "GET", "/v1/user/created_tokens", NORMAL_AUTH),
    MethodParitySpec("quoteOrder", "GET", "/v1/trade/quote", CRITICAL_AUTH),
    MethodParitySpec("swap", "POST", "/v1/trade/swap", CRITICAL_AUTH),
    MethodParitySpec("multiSwap", "POST", "/v1/trade/multi_swap", CRITICAL_AUTH),
    MethodParitySpec("queryOrder", "GET", "/v1/trade/query_order", CRITICAL_AUTH),
    MethodParitySpec("createStrategyOrder", "POST", "/v1/trade/strategy/create", CRITICAL_AUTH),
    MethodParitySpec("getStrategyOrders", "GET", "/v1/trade/strategy/orders", CRITICAL_AUTH),
    MethodParitySpec("cancelStrategyOrder", "POST", "/v1/trade/strategy/cancel", CRITICAL_AUTH),
    MethodParitySpec("getCookingStatistics", "GET", "/v1/cooking/statistics", NORMAL_AUTH),
    MethodParitySpec("createToken", "POST", "/v1/cooking/create_token", CRITICAL_AUTH),
)
