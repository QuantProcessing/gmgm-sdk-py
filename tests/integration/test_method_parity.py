from __future__ import annotations

from gmgn_sdk import GMGNClient

EXPECTED_PARITY = [
    ("getTokenInfo", "GET", "/v1/token/info", "normal"),
    ("getTokenSecurity", "GET", "/v1/token/security", "normal"),
    ("getTokenPoolInfo", "GET", "/v1/token/pool_info", "normal"),
    ("getTokenTopHolders", "GET", "/v1/market/token_top_holders", "normal"),
    ("getTokenTopTraders", "GET", "/v1/market/token_top_traders", "normal"),
    ("getTokenKline", "GET", "/v1/market/token_kline", "normal"),
    ("getWalletHoldings", "GET", "/v1/user/wallet_holdings", "normal"),
    ("getWalletActivity", "GET", "/v1/user/wallet_activity", "normal"),
    ("getWalletStats", "GET", "/v1/user/wallet_stats", "normal"),
    ("getWalletTokenBalance", "GET", "/v1/user/wallet_token_balance", "normal"),
    ("getTrenches", "POST", "/v1/trenches", "normal"),
    ("getTrendingSwaps", "GET", "/v1/market/rank", "normal"),
    ("getTokenSignalV2", "POST", "/v1/market/token_signal", "normal"),
    ("getUserInfo", "GET", "/v1/user/info", "normal"),
    ("getFollowWallet", "GET", "/v1/trade/follow_wallet", "critical"),
    ("getKol", "GET", "/v1/user/kol", "normal"),
    ("getSmartMoney", "GET", "/v1/user/smartmoney", "normal"),
    ("getCreatedTokens", "GET", "/v1/user/created_tokens", "normal"),
    ("quoteOrder", "GET", "/v1/trade/quote", "critical"),
    ("swap", "POST", "/v1/trade/swap", "critical"),
    ("multiSwap", "POST", "/v1/trade/multi_swap", "critical"),
    ("queryOrder", "GET", "/v1/trade/query_order", "critical"),
    ("createStrategyOrder", "POST", "/v1/trade/strategy/create", "critical"),
    ("getStrategyOrders", "GET", "/v1/trade/strategy/orders", "critical"),
    ("cancelStrategyOrder", "POST", "/v1/trade/strategy/cancel", "critical"),
    ("getCookingStatistics", "GET", "/v1/cooking/statistics", "normal"),
    ("createToken", "POST", "/v1/cooking/create_token", "critical"),
]


def test_method_parity_metadata_matches_expected_ts_surface() -> None:
    parity = GMGNClient.method_parity()
    assert len(parity) == 27
    assert [
        (item.name, item.http_method, item.path, item.auth_mode)
        for item in parity
    ] == EXPECTED_PARITY


def test_every_parity_method_exists_on_client() -> None:
    for method_name, _, _, _ in EXPECTED_PARITY:
        assert hasattr(GMGNClient, method_name), method_name


def test_common_snake_case_aliases_exist_on_client() -> None:
    for method_name in (
        "get_token_info",
        "get_wallet_holdings",
        "quote_order",
        "multi_swap",
        "create_strategy_order",
        "create_token",
    ):
        assert hasattr(GMGNClient, method_name), method_name
