# Live Verification

Live verification calls the real GMGN API and may submit swaps. It must only run
with explicit user-provided credentials and capped amounts.

Required environment:

- `RUN_LIVE_GMGN=1`
- `GMGN_API_KEY`
- `GMGN_PRIVATE_KEY`
- `GMGN_SOL_FROM_ADDRESS`, `GMGN_BSC_FROM_ADDRESS`, `GMGN_ETH_FROM_ADDRESS`

For each enabled acceptance chain (`SOL`, `BSC`, `ETH`), provide:

- `GMGN_<CHAIN>_INPUT_TOKEN`
- `GMGN_<CHAIN>_OUTPUT_TOKEN`
- `GMGN_<CHAIN>_INPUT_AMOUNT`, in the raw smallest-unit amount expected by GMGN
- `GMGN_<CHAIN>_INPUT_AMOUNT_NATIVE`, the human-readable native spend amount checked against the cap

Optional per-chain swap fields:

- `GMGN_<CHAIN>_SLIPPAGE`, default `0.01`
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

Caps:

- Solana: `0.1 SOL`
- Ethereum: `0.01 ETH`
- BSC: `0.01 BNB`

Report artifact:

- `.omx/reports/gmgn-sdk-live-verification.md`

Normal local verification must not require real credentials. The live suite is
fully gated by `RUN_LIVE_GMGN=1` and should otherwise skip during standard
`pytest` runs.

Expected verification commands:

- `pytest tests/unit`
- `pytest tests/integration`
- `RUN_LIVE_GMGN=1 pytest tests/live/test_live_swaps.py -m live`

`createToken` is implemented but not live-tested in the first acceptance pass.
Request formation is covered by integration tests instead.
