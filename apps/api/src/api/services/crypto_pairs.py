"""The tracked crypto pairs and the offline snapshot that keeps the app useful without network.

Each pair carries the public data-source identifiers: the CoinGecko coin id for prices
and the DefiLlama mapping for the on-chain value metric (chain TVL or protocol TVL/AUM).
Zama is too recently listed for indicators; it is shown with live price only.
"""

from typing import NotRequired, TypedDict


class PairConfig(TypedDict):
    symbol: str
    name: str
    coingecko_id: str
    quote: str
    # DefiLlama: chain name in /v2/chains, or protocol slug for /tvl/<slug>.
    defillama_kind: str  # "chain" | "protocol" | "none"
    defillama_slug: str
    defillama_metric: str  # human label of the on-chain metric
    snapshot: dict[str, object]


# Values computed from CoinMarketCap daily closes and DefiLlama on 2026-11-14 (UTC).
# They are the fallback shown when the public APIs are unreachable, and always carry
# their date in the response.
PAIRS: list[PairConfig] = [
    {
        "symbol": "BTC",
        "name": "Bitcoin",
        "coingecko_id": "bitcoin",
        "quote": "USDC",
        "defillama_kind": "chain",
        "defillama_slug": "Bitcoin",
        "defillama_metric": "TVL DeFi (BTCFi)",
        "snapshot": {
            "price": 68233.0,
            "change_24h": -3.7,
            "ma50": 78820.0,
            "ma200": 69650.0,
            "swing_high": 99697.0,
            "swing_high_date": "2025-11-13",
            "swing_low": 58559.0,
            "swing_low_date": "2026-06-30",
            "tvl": 3_604_000_000.0,
        },
    },
    {
        "symbol": "ETH",
        "name": "Ethereum",
        "coingecko_id": "ethereum",
        "quote": "USDC",
        "defillama_kind": "chain",
        "defillama_slug": "Ethereum",
        "defillama_metric": "TVL chaîne",
        "snapshot": {
            "price": 1927.7,
            "change_24h": -4.0,
            "ma50": 2412.0,
            "ma200": 2147.0,
            "swing_high": 3354.7,
            "swing_high_date": "2026-01-14",
            "swing_low": 1564.8,
            "swing_low_date": "2026-06-25",
            "tvl": 39_150_000_000.0,
        },
    },
    {
        "symbol": "SOL",
        "name": "Solana",
        "coingecko_id": "solana",
        "quote": "USDC",
        "defillama_kind": "chain",
        "defillama_slug": "Solana",
        "defillama_metric": "TVL chaîne",
        "snapshot": {
            "price": 77.12,
            "change_24h": -4.5,
            "ma50": 103.9,
            "ma200": 88.9,
            "swing_high": 146.75,
            "swing_high_date": "2026-01-14",
            "swing_low": 62.19,
            "swing_low_date": "2026-06-06",
            "tvl": 4_899_000_000.0,
        },
    },
    {
        "symbol": "LINK",
        "name": "Chainlink",
        "coingecko_id": "chainlink",
        "quote": "USDC",
        "defillama_kind": "protocol",
        "defillama_slug": "chainlink",
        "defillama_metric": "TVL protocole (staking)",
        "snapshot": {
            "price": 9.78,
            "change_24h": -3.5,
            "ma50": 12.23,
            "ma200": 10.09,
            "swing_high": 15.44,
            "swing_high_date": "2026-09-28",
            "swing_low": 7.19,
            "swing_low_date": "2026-06-30",
            "tvl": 1_804_000_000.0,
        },
    },
    {
        "symbol": "AVAX",
        "name": "Avalanche",
        "coingecko_id": "avalanche-2",
        "quote": "USDC",
        "defillama_kind": "chain",
        "defillama_slug": "Avalanche",
        "defillama_metric": "TVL chaîne",
        "snapshot": {
            "price": 8.18,
            "change_24h": -1.5,
            "ma50": 9.63,
            "ma200": 8.09,
            "swing_high": 16.16,
            "swing_high_date": "2025-11-13",
            "swing_low": 5.91,
            "swing_low_date": "2026-06-19",
            "tvl": 590_400_000.0,
        },
    },
    {
        "symbol": "INJ",
        "name": "Injective",
        "coingecko_id": "injective-protocol",
        "quote": "USDC",
        "defillama_kind": "chain",
        "defillama_slug": "Injective",
        "defillama_metric": "TVL chaîne",
        "snapshot": {
            "price": 8.07,
            "change_24h": 0.8,
            "ma50": 7.81,
            "ma200": 5.79,
            "swing_high": 8.93,
            "swing_high_date": "2026-10-20",
            "swing_low": 2.74,
            "swing_low_date": "2026-04-02",
            "tvl": 18_540_000.0,
        },
    },
    {
        "symbol": "ONDO",
        "name": "Ondo",
        "coingecko_id": "ondo-finance",
        "quote": "USDC",
        "defillama_kind": "protocol",
        "defillama_slug": "ondo-finance",
        "defillama_metric": "AUM RWA",
        "snapshot": {
            "price": 0.337,
            "change_24h": -4.3,
            "ma50": 0.442,
            "ma200": 0.381,
            "swing_high": 0.616,
            "swing_high_date": "2025-11-13",
            "swing_low": 0.225,
            "swing_low_date": "2026-02-05",
            "tvl": 2_776_000_000.0,
        },
    },
    {
        "symbol": "TAO",
        "name": "Bittensor",
        "coingecko_id": "bittensor",
        "quote": "USDC",
        "defillama_kind": "protocol",
        "defillama_slug": "bittensor",
        "defillama_metric": "TVL dTAO",
        "snapshot": {
            "price": 215.35,
            "change_24h": 1.2,
            "ma50": 263.9,
            "ma200": 241.0,
            "swing_high": 346.28,
            "swing_high_date": "2026-03-25",
            "swing_low": 145.63,
            "swing_low_date": "2026-02-11",
            "tvl": 376_000_000.0,
        },
    },
    {
        "symbol": "FET",
        "name": "Artificial Superintelligence Alliance",
        "coingecko_id": "fetch-ai",
        "quote": "USDC",
        "defillama_kind": "none",
        "defillama_slug": "",
        "defillama_metric": "TVL",
        "snapshot": {
            "price": 0.1469,
            "change_24h": -0.1,
            "ma50": 0.192,
            "ma200": 0.183,
            "swing_high": 0.329,
            "swing_high_date": "2025-11-19",
            "swing_low": 0.1215,
            "swing_low_date": "2026-08-16",
            "tvl": None,
        },
    },
    {
        "symbol": "ZAMA",
        "name": "Zama",
        "coingecko_id": "zama",
        "quote": "USDC",
        "defillama_kind": "none",
        "defillama_slug": "",
        "defillama_metric": "TVL",
        "snapshot": {
            "price": 0.0583,
            "change_24h": -1.8,
            "ma50": None,
            "ma200": None,
            "swing_high": 0.0611,
            "swing_high_date": "2026-11-13",
            "swing_low": 0.0565,
            "swing_low_date": "2026-11-13",
            "tvl": None,
        },
    },
]

PAIRS_BY_SYMBOL: dict[str, PairConfig] = {pair["symbol"]: pair for pair in PAIRS}

SNAPSHOT_AS_OF = "2026-11-14"


class SnapshotExtra(TypedDict, total=False):
    fib: NotRequired[dict[str, float]]
