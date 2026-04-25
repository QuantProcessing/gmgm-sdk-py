from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class MethodContract:
    name: str
    path: str
    http_method: str
    auth_mode: str


METHOD_CONTRACTS: tuple[MethodContract, ...] = (
    MethodContract("getTokenInfo", "/v1/token/info", "GET", "normal"),
    MethodContract("getTokenSecurity", "/v1/token/security", "GET", "normal"),
    MethodContract("getTokenPoolInfo", "/v1/token/pool_info", "GET", "normal"),
    MethodContract("getTokenTopHolders", "/v1/market/token_top_holders", "GET", "normal"),
    MethodContract("getTokenTopTraders", "/v1/market/token_top_traders", "GET", "normal"),
    MethodContract("getTokenKline", "/v1/market/token_kline", "GET", "normal"),
    MethodContract("getWalletHoldings", "/v1/user/wallet_holdings", "GET", "normal"),
    MethodContract("getWalletActivity", "/v1/user/wallet_activity", "GET", "normal"),
    MethodContract("getWalletStats", "/v1/user/wallet_stats", "GET", "normal"),
    MethodContract("getWalletTokenBalance", "/v1/user/wallet_token_balance", "GET", "normal"),
    MethodContract("getTrenches", "/v1/trenches", "POST", "normal"),
    MethodContract("getTrendingSwaps", "/v1/market/rank", "GET", "normal"),
    MethodContract("getTokenSignalV2", "/v1/market/token_signal", "POST", "normal"),
    MethodContract("getUserInfo", "/v1/user/info", "GET", "normal"),
    MethodContract("getFollowWallet", "/v1/trade/follow_wallet", "GET", "critical"),
    MethodContract("getKol", "/v1/user/kol", "GET", "normal"),
    MethodContract("getSmartMoney", "/v1/user/smartmoney", "GET", "normal"),
    MethodContract("getCreatedTokens", "/v1/user/created_tokens", "GET", "normal"),
    MethodContract("quoteOrder", "/v1/trade/quote", "GET", "critical"),
    MethodContract("swap", "/v1/trade/swap", "POST", "critical"),
    MethodContract("multiSwap", "/v1/trade/multi_swap", "POST", "critical"),
    MethodContract("queryOrder", "/v1/trade/query_order", "GET", "critical"),
    MethodContract("createStrategyOrder", "/v1/trade/strategy/create", "POST", "critical"),
    MethodContract("getStrategyOrders", "/v1/trade/strategy/orders", "GET", "critical"),
    MethodContract("cancelStrategyOrder", "/v1/trade/strategy/cancel", "POST", "critical"),
    MethodContract("getCookingStatistics", "/v1/cooking/statistics", "GET", "normal"),
    MethodContract("createToken", "/v1/cooking/create_token", "POST", "critical"),
)

LIVE_SPEND_CAPS = {
    "sol": "0.1 SOL",
    "eth": "0.01 ETH",
    "bsc": "0.01 BNB",
}

LIVE_REPORT_PATH = Path(".omx/reports/gmgn-sdk-live-verification.md")

