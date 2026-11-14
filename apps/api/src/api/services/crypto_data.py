"""Public data providers: CoinGecko for prices, DefiLlama for on-chain value.

Both are unauthenticated public APIs. Every fetch has a timeout and every failure falls
back to the embedded snapshot, so the app always answers; the response says which source
served each part. Results are cached in memory for ten minutes.
"""

import asyncio
import time
from typing import Any

import httpx

from api.services.crypto_analysis import Close
from api.services.crypto_pairs import PAIRS, SNAPSHOT_AS_OF

CACHE_TTL_S = 600
COINGECKO_BASE = "https://api.coingecko.com/api/v3"
DEFILLAMA_BASE = "https://api.llama.fi"
HTTP_TIMEOUT_S = 15.0


class MarketData:
    """One pair's fetched market data, or None fields when unavailable."""

    def __init__(
        self,
        *,
        closes: list[Close] | None = None,
        price: float | None = None,
        change_24h: float | None = None,
        source: str = "snapshot",
    ) -> None:
        self.closes = closes
        self.price = price
        self.change_24h = change_24h
        self.source = source


_cache: dict[str, tuple[float, Any]] = {}
_cache_lock = asyncio.Lock()


async def _cached(key: str, factory: Any) -> Any:
    async with _cache_lock:
        hit = _cache.get(key)
        now = time.monotonic()
        if hit is not None and now - hit[0] < CACHE_TTL_S:
            return hit[1]
    value = await factory()
    async with _cache_lock:
        _cache[key] = (time.monotonic(), value)
    return value


RATE_LIMIT_PAUSE_S = 6.0
RATE_LIMIT_RETRY_WAIT_S = 30.0


async def fetch_pair_market(client: httpx.AsyncClient, pair: dict[str, Any]) -> MarketData:
    """Daily closes (oldest first), live price and 24h change for one pair.

    The public endpoint rate-limits bursts, so a 429 waits once and retries; every
    other failure falls back to the embedded snapshot.
    """

    async def load() -> MarketData:
        url = f"{COINGECKO_BASE}/coins/{pair['coingecko_id']}/market_chart"
        params = {"vs_currency": "usd", "days": "365", "interval": "daily"}
        payload: dict[str, Any] = {}
        for attempt in (1, 2):
            try:
                resp = await client.get(url, params=params)
                if resp.status_code == 429 and attempt == 1:
                    await asyncio.sleep(RATE_LIMIT_RETRY_WAIT_S)
                    continue
                resp.raise_for_status()
                payload = resp.json()
                break
            except (httpx.HTTPError, KeyError, ValueError):
                return MarketData()
        closes: list[Close] = [
            {"date": _ms_to_date(ts), "price": round(p, 8)}
            for ts, p in payload.get("prices", [])
        ]
        # CoinGecko appends an in-progress point for today; keep it, it is the live price.
        price = closes[-1]["price"] if closes else None
        change = None
        if len(closes) >= 2:
            prev = closes[-2]["price"]
            if prev:
                change = (closes[-1]["price"] - prev) / prev * 100
        return MarketData(closes=closes, price=price, change_24h=change, source="coingecko")

    return await _cached(f"market:{pair['coingecko_id']}", load)


async def fetch_tvl_map(client: httpx.AsyncClient) -> dict[str, float]:
    """Chain name -> TVL in USD, from DefiLlama's /v2/chains."""

    async def load() -> dict[str, float]:
        try:
            resp = await client.get(f"{DEFILLAMA_BASE}/v2/chains")
            resp.raise_for_status()
            return {str(c.get("name")): float(c.get("tvl") or 0) for c in resp.json()}
        except (httpx.HTTPError, ValueError):
            return {}

    return await _cached("tvl:chains", load)


async def fetch_protocol_tvl(client: httpx.AsyncClient, slug: str) -> float | None:
    """A protocol's current TVL in USD from DefiLlama's /tvl/<slug>."""

    async def load() -> float | None:
        try:
            resp = await client.get(f"{DEFILLAMA_BASE}/tvl/{slug}")
            resp.raise_for_status()
            text = resp.text.strip()
            value = float(text)
            return value if value > 0 else None
        except (httpx.HTTPError, ValueError):
            return None

    return await _cached(f"tvl:protocol:{slug}", load)


def _ms_to_date(ms: int | float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d")


async def collect_all() -> dict[str, Any]:
    """Fetch every tracked pair's market data and on-chain value, snapshot as fallback."""

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S, follow_redirects=True) as client:
        tvl_chains = await fetch_tvl_map(client)
        markets: dict[str, MarketData] = {}
        for index, pair in enumerate(PAIRS):
            if index:
                await asyncio.sleep(RATE_LIMIT_PAUSE_S)
            markets[pair["symbol"]] = await fetch_pair_market(client, pair)

    results: dict[str, Any] = {}
    for pair in PAIRS:
        symbol = pair["symbol"]
        market = markets[symbol]
        snapshot: dict[str, Any] = pair["snapshot"]
        tvl: float | None = None
        tvl_source = "snapshot"
        if pair["defillama_kind"] == "chain":
            live_tvl = tvl_chains.get(pair["defillama_slug"])
            if live_tvl:
                tvl, tvl_source = live_tvl, "defillama"
        elif pair["defillama_kind"] == "protocol":
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_S, follow_redirects=True) as client:
                live_tvl = await fetch_protocol_tvl(client, pair["defillama_slug"])
            if live_tvl:
                tvl, tvl_source = live_tvl, "defillama"
        if tvl is None and snapshot.get("tvl") is not None:
            tvl = float(snapshot["tvl"])

        if market.closes:
            results[symbol] = {
                "closes": market.closes,
                "price": market.price,
                "change_24h": market.change_24h,
                "tvl": tvl,
                "tvl_label": pair["defillama_metric"],
                "tvl_source": tvl_source,
                "source": market.source,
                "as_of": market.closes[-1]["date"],
            }
        else:
            results[symbol] = {
                "closes": [],
                "price": float(snapshot["price"]),
                "change_24h": snapshot.get("change_24h"),
                "tvl": tvl,
                "tvl_label": pair["defillama_metric"],
                "tvl_source": tvl_source,
                "source": "snapshot",
                "as_of": SNAPSHOT_AS_OF,
            }
    return results
