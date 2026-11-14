"""Deterministic technical analysis: moving averages, swings, Fibonacci, trade plan.

Pure functions over daily close series, mirroring the analysis rules: MA50/MA200 on the
last 50/200 daily closes, 365-day swing extremes with dates, the main leg oriented by the
chronological order of the extremes, retracements 0.236/0.382/0.5/0.618/0.786 on that leg,
extensions 1.272/1.618 beyond the leg's end extreme, and a buy plan whose reward/risk must
reach 2 to be valid.
"""

from datetime import date, datetime, timezone
from typing import NotRequired, TypedDict

RETRACEMENTS = (0.236, 0.382, 0.5, 0.618, 0.786)
EXTENSIONS = (1.272, 1.618)
MIN_RR = 2.0
CONFLUENCE_PCT = 0.02


class Close(TypedDict):
    date: str
    price: float


class FibLevels(TypedDict):
    retracements: dict[str, float]
    extensions: dict[str, float]


class Plan(TypedDict):
    zone_low: float
    zone_high: float
    stop: float
    target1: float
    target2: float | None
    rr: float
    valid: bool
    note: str


class PairAnalysis(TypedDict, total=False):
    symbol: str
    name: str
    quote: str
    price: float
    change_24h: float | None
    ma50: float | None
    ma200: float | None
    trend: str
    trend_label: str
    swing_high: float
    swing_high_date: str
    swing_low: float
    swing_low_date: str
    leg: str
    fib: FibLevels
    plan: Plan | None
    series: list[Close]
    insufficient_history: bool


def _ma(closes: list[Close], window: int) -> float | None:
    if len(closes) < window:
        return None
    return sum(c["price"] for c in closes[-window:]) / window


def _trend(price: float, ma50: float | None, ma200: float | None) -> tuple[str, str]:
    if ma50 is None or ma200 is None:
        return "unknown", "Historique insuffisant"
    if price > ma50 > ma200:
        return "bullish", "Haussière (prix > MA50 > MA200)"
    if price < ma200 < ma50:
        return "bearish", "Baissière (prix < MA200 < MA50)"
    if price < ma50 < ma200:
        return "bearish", "Baissière (death cross : prix < MA50 < MA200)"
    if ma50 > ma200 and price < ma200:
        return "bearish", "Baissière (prix sous les deux MA)"
    if ma50 < ma200 and price > ma200:
        return "recovering", "Retournement (prix repasse la MA200)"
    if ma50 > ma200 and ma200 < price < ma50:
        return "neutral", "Neutre (prix entre MA200 et MA50)"
    return "neutral", "Mixte (MA50 sous MA200)"


def _fib(swing_low: float, swing_high: float, leg: str) -> FibLevels:
    span = swing_high - swing_low
    retr: dict[str, float]
    ext: dict[str, float]
    if leg == "down":
        # Bear leg high -> low: retracements retrace up from the low.
        retr = {f"{r:.3f}": swing_low + span * r for r in RETRACEMENTS}
        ext = {f"{e:.3f}": swing_low - span * (e - 1.0) for e in EXTENSIONS}
    else:
        # Bull leg low -> high: retracements fall from the high.
        retr = {f"{r:.3f}": swing_high - span * r for r in RETRACEMENTS}
        ext = {f"{e:.3f}": swing_low + span * e for e in EXTENSIONS}
    return {"retracements": retr, "extensions": ext}


def _near(a: float, b: float, pct: float = CONFLUENCE_PCT) -> bool:
    if a == 0 or b == 0:
        return False
    return abs(a - b) / min(abs(a), abs(b)) <= pct


def _local_low(closes: list[Close], lookback: int = 30) -> float:
    window = closes[-lookback:]
    return min(c["price"] for c in window)


def _plan(
    closes: list[Close],
    price: float,
    ma50: float | None,
    ma200: float | None,
    trend: str,
    leg: str,
    fib: FibLevels,
) -> Plan | None:
    if len(closes) < 30:
        return None
    retr = fib["retracements"]
    ext = fib["extensions"]
    local_low = _local_low(closes)
    stop_buffer = max(local_low * 0.02, price * 0.005)

    if trend in ("bearish",):
        # Bounce plan: buy the retracement just below the price, target the levels above it.
        # The levels are ordered from the highest, so this holds whichever way the leg ran.
        levels = sorted(retr.values(), reverse=True)
        zone = next((level for level in levels if level <= price * 1.05), levels[-1])
        zone_low, zone_high = zone * 0.97, zone * 1.03
        stop = local_low - stop_buffer
        if stop * 1.005 >= zone_high:
            # The price has already fallen through the zone: the support to buy is the price
            # area itself, with the stop under the recent low.
            zone_low, zone_high = price * 0.97, price * 1.03
        # The zone must sit above the stop, or the plan buys through its own invalidation.
        zone_low = max(zone_low, stop * 1.005)
        entry = (zone_low + zone_high) / 2
        above = sorted(level for level in levels if level > zone_high)
        target1 = above[0] if above else zone * 1.05
        target2 = above[1] if len(above) > 1 else None
        if ma200 is not None and _near(target1, ma200):
            note = "Cible 1 en confluence avec la MA200"
        elif ma50 is not None and target2 is not None and _near(target2, ma50):
            note = "Cible 2 en confluence avec la MA50"
        else:
            note = "Scénario rebond sur retracement"
    elif trend in ("bullish", "recovering"):
        # Pullback plan: buy the first retracement (plus MA confluence), target extension 1.272.
        zone = retr["0.236"]
        stop = local_low - stop_buffer
        zone_low, zone_high = zone * 0.97, zone * 1.05
        if stop * 1.005 >= zone_high:
            zone_low, zone_high = price * 0.97, price * 1.03
        zone_low = max(zone_low, stop * 1.005)
        entry = (zone_low + zone_high) / 2
        target1 = ext["1.272"]
        target2 = ext["1.618"]
        note = "Scénario continuation vers extension 1.272"
    else:
        return None

    risk = entry - stop
    reward = target1 - entry
    if risk <= 0:
        rr = 0.0
    else:
        rr = reward / risk
    return {
        "zone_low": round(zone_low, 6),
        "zone_high": round(zone_high, 6),
        "stop": round(stop, 6),
        "target1": round(target1, 6),
        "target2": None if target2 is None else round(target2, 6),
        "rr": round(rr, 2),
        "valid": rr >= MIN_RR,
        "note": note,
    }


def analyze_pair(
    *,
    symbol: str,
    name: str,
    quote: str,
    closes: list[Close],
    price: float | None = None,
    change_24h: float | None = None,
) -> PairAnalysis:
    """Compute the full analysis of one pair from its daily closes (oldest first)."""
    if not closes:
        raise ValueError("no closes")
    last = closes[-1]["price"]
    if price is None:
        price = last
    if change_24h is None and len(closes) >= 2:
        prev = closes[-2]["price"]
        change_24h = (price - prev) / prev * 100 if prev else None

    ma50 = _ma(closes, 50)
    ma200 = _ma(closes, 200)
    trend, label = _trend(price, ma50, ma200)

    year = closes[-365:] if len(closes) >= 365 else closes
    high = max(year, key=lambda c: c["price"])
    low = min(year, key=lambda c: c["price"])
    leg = "down" if high["date"] < low["date"] else "up"

    fib = _fib(low["price"], high["price"], leg)
    plan = _plan(closes, price, ma50, ma200, trend, leg, fib)

    analysis: PairAnalysis = {
        "symbol": symbol,
        "name": name,
        "quote": quote,
        "price": price,
        "change_24h": round(change_24h, 2) if change_24h is not None else None,
        "ma50": round(ma50, 6) if ma50 is not None else None,
        "ma200": round(ma200, 6) if ma200 is not None else None,
        "trend": trend,
        "trend_label": label,
        "swing_high": high["price"],
        "swing_high_date": high["date"],
        "swing_low": low["price"],
        "swing_low_date": low["date"],
        "leg": leg,
        "fib": {
            "retracements": {k: round(v, 6) for k, v in fib["retracements"].items()},
            "extensions": {k: round(v, 6) for k, v in fib["extensions"].items()},
        },
        "plan": plan,
        "series": closes[-365:],
        "insufficient_history": len(closes) < 50,
    }
    return analysis


def utc_today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()
