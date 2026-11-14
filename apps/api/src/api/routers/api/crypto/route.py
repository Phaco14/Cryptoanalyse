"""The crypto dashboard API: full analysis for the tracked pairs, plus stored history.

Every response says what served it: ``live`` when the public data APIs answered,
``snapshot`` when the embedded analysis of 2026-11-14 stepped in. Technical analysis is
always computed the same way, from daily closes.
"""

import json
from typing import Annotated, Any, Literal

import structlog
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.services import crypto_data
from api.services.crypto_analysis import PairAnalysis, analyze_pair, utc_today
from api.services.crypto_pairs import PAIRS, PAIRS_BY_SYMBOL, SNAPSHOT_AS_OF
from db.accessors import crypto_snapshot as snapshots

logger = structlog.get_logger("api.crypto")

router = APIRouter()


class Close(BaseModel):
    date: str
    price: float


class FibLevels(BaseModel):
    retracements: dict[str, float]
    extensions: dict[str, float]


class TradePlan(BaseModel):
    zone_low: float
    zone_high: float
    stop: float
    target1: float
    target2: float | None = None
    rr: float
    valid: bool
    note: str


class PairAnalysisOut(BaseModel):
    symbol: str
    name: str
    quote: str
    price: float
    change_24h: float | None = None
    ma50: float | None = None
    ma200: float | None = None
    trend: str
    trend_label: str
    swing_high: float
    swing_high_date: str
    swing_low: float
    swing_low_date: str
    leg: Literal["up", "down"]
    fib: FibLevels
    plan: TradePlan | None = None
    series: list[Close] = Field(default_factory=list)
    insufficient_history: bool


class TvlInfo(BaseModel):
    value: float | None = None
    label: str
    source: str


class AnalysisResponse(BaseModel):
    as_of: str
    source: Literal["live", "snapshot", "mixed"]
    restored_from_history: bool | None = None
    pairs: list[PairAnalysisOut]
    tvl: dict[str, TvlInfo]


class SnapshotMeta(BaseModel):
    date_key: str
    created_at: str


class HistoryResponse(BaseModel):
    snapshots: list[SnapshotMeta]


class PairDetailResponse(BaseModel):
    as_of: str
    source: Literal["live", "snapshot", "mixed"]
    tvl: TvlInfo | None = None
    analysis: PairAnalysisOut


def _snapshot_analysis(pair: dict[str, Any]) -> PairAnalysis:
    """The embedded fallback analysis, without a close series."""
    snap: dict[str, Any] = pair["snapshot"]
    ma50 = snap.get("ma50")
    ma200 = snap.get("ma200")
    price = float(snap["price"])
    if ma50 is not None and ma200 is not None:
        if price > ma50 > ma200:
            trend, label = "bullish", "Haussière (prix > MA50 > MA200)"
        else:
            trend, label = "bearish", "Baissière (prix sous les MA)"
    else:
        trend, label = "unknown", "Historique insuffisant"
    span = float(snap["swing_high"]) - float(snap["swing_low"])
    leg = "down" if snap["swing_high_date"] < snap["swing_low_date"] else "up"
    if leg == "down":
        retr = {f"{r:.3f}": float(snap["swing_low"]) + span * r for r in (0.236, 0.382, 0.5, 0.618, 0.786)}
        ext = {f"{e:.3f}": float(snap["swing_low"]) - span * (e - 1.0) for e in (1.272, 1.618)}
    else:
        retr = {f"{r:.3f}": float(snap["swing_high"]) - span * r for r in (0.236, 0.382, 0.5, 0.618, 0.786)}
        ext = {f"{e:.3f}": float(snap["swing_low"]) + span * e for e in (1.272, 1.618)}
    return {
        "symbol": pair["symbol"],
        "name": pair["name"],
        "quote": pair["quote"],
        "price": price,
        "change_24h": snap.get("change_24h"),
        "ma50": ma50,
        "ma200": ma200,
        "trend": trend,
        "trend_label": label,
        "swing_high": float(snap["swing_high"]),
        "swing_high_date": str(snap["swing_high_date"]),
        "swing_low": float(snap["swing_low"]),
        "swing_low_date": str(snap["swing_low_date"]),
        "leg": leg,
        "fib": {
            "retracements": {k: round(v, 6) for k, v in retr.items()},
            "extensions": {k: round(v, 6) for k, v in ext.items()},
        },
        "plan": None,
        "series": [],
        "insufficient_history": True,
    }


async def _build_analysis() -> dict[str, Any]:
    market = await crypto_data.collect_all()
    pairs_out: list[PairAnalysis] = []
    tvl_by_symbol: dict[str, Any] = {}
    sources: set[str] = set()
    as_of = SNAPSHOT_AS_OF
    for pair in PAIRS:
        symbol = pair["symbol"]
        data = market[symbol]
        sources.add(data["source"])
        if data["source"] == "live" or data["source"] == "coingecko":
            as_of = max(as_of, data["as_of"])
            analysis = analyze_pair(
                symbol=symbol,
                name=pair["name"],
                quote=pair["quote"],
                closes=data["closes"],
                price=data["price"],
                change_24h=data["change_24h"],
            )
        else:
            as_of = max(as_of, data["as_of"])
            analysis = _snapshot_analysis(pair)
        pairs_out.append(analysis)
        tvl_by_symbol[symbol] = {
            "value": data["tvl"],
            "label": data["tvl_label"],
            "source": data["tvl_source"],
        }

    payload = {
        "as_of": as_of,
        "source": "live" if sources == {"coingecko"} else ("snapshot" if sources == {"snapshot"} else "mixed"),
        "pairs": pairs_out,
        "tvl": tvl_by_symbol,
    }
    return payload


async def _store_snapshot(payload: dict[str, Any]) -> None:
    try:
        await snapshots.upsert_by_date(utc_today(), json.dumps(payload))
    except Exception:  # noqa: BLE001 - the dashboard must answer even when the database is down
        logger.warning("crypto_snapshot_store_failed")


@router.get("", operation_id="crypto_analysis", summary="The full dashboard analysis")
async def crypto_analysis(
    refresh: Annotated[bool, Query(description="Recompute even if a stored snapshot exists")] = False,
) -> AnalysisResponse:
    """Analysis of every tracked pair: indicators, Fibonacci levels, trade plan, on-chain
    value. Today's analysis is stored once per day; the stored copy is served until
    ``refresh`` forces a recompute."""
    if not refresh:
        try:
            stored = await snapshots.latest()
        except Exception:  # noqa: BLE001 - database down must not break the dashboard
            stored = None
            logger.warning("crypto_snapshot_read_failed")
        if stored is not None and stored.date_key == utc_today():
            payload: dict[str, Any] = json.loads(stored.payload)
            payload["restored_from_history"] = True
            return AnalysisResponse.model_validate(payload)
    payload = await _build_analysis()
    await _store_snapshot(payload)
    return AnalysisResponse.model_validate(payload)


@router.get("/history", operation_id="crypto_history", summary="Past stored daily analyses")
async def crypto_history(
    limit: Annotated[int, Query(ge=1, le=365)] = 30,
) -> HistoryResponse:
    """Metadata of the most recent stored daily analyses (date and creation time)."""
    try:
        rows = await snapshots.recent(limit)
    except Exception:  # noqa: BLE001
        logger.warning("crypto_history_read_failed")
        rows = []
    return HistoryResponse(
        snapshots=[
            SnapshotMeta(date_key=row.date_key, created_at=row.created_at.isoformat())
            for row in rows
        ]
    )


@router.post("/refresh", operation_id="crypto_refresh", summary="Recompute and store now")
async def crypto_refresh() -> AnalysisResponse:
    """Force a fresh computation from the public data sources and store it as today's
    snapshot."""
    payload = await _build_analysis()
    await _store_snapshot(payload)
    return AnalysisResponse.model_validate(payload)


@router.get("/pairs/{symbol}", operation_id="crypto_pair", summary="One pair's analysis")
async def crypto_pair(symbol: str) -> PairDetailResponse:
    """The analysis of a single tracked pair, by symbol (case-insensitive)."""
    key = symbol.upper()
    pair = PAIRS_BY_SYMBOL.get(key)
    if pair is None:
        raise HTTPException(status_code=404, detail=f"Unknown pair: {symbol}")
    payload = await _build_analysis()
    for analysis in payload["pairs"]:
        if analysis["symbol"] == key:
            return PairDetailResponse(
                as_of=payload["as_of"],
                source=payload["source"],
                tvl=payload["tvl"].get(key),
                analysis=analysis,
            )
    raise HTTPException(status_code=404, detail=f"Pair missing from analysis: {symbol}")
