"""Unit tests of the deterministic analysis engine (no network, no database)."""

from datetime import timedelta

import pytest

from api.services.crypto_analysis import _fib, _ma, _plan, _trend, analyze_pair


def closes_from(prices: list[float], start: str = "2025-01-01") -> list[dict]:
    from datetime import datetime

    day = datetime.strptime(start, "%Y-%m-%d")
    return [
        {"date": (day + timedelta(days=i)).strftime("%Y-%m-%d"), "price": p}
        for i, p in enumerate(prices)
    ]


def test_ma_windows():
    closes = closes_from([float(i) for i in range(1, 51)])
    assert _ma(closes, 50) == sum(range(1, 51)) / 50
    assert _ma(closes, 200) is None


def test_trend_classification():
    assert _trend(120.0, 110.0, 100.0)[0] == "bullish"
    assert _trend(90.0, 110.0, 100.0)[0] == "bearish"
    assert _trend(105.0, 110.0, 100.0)[0] == "neutral"
    assert _trend(105.0, None, None)[0] == "unknown"


def test_fib_bear_leg():
    fib = _fib(100.0, 200.0, "down")
    assert fib["retracements"]["0.236"] == pytest.approx(123.6)
    assert fib["retracements"]["0.500"] == pytest.approx(150.0)
    assert fib["extensions"]["1.272"] == pytest.approx(72.8)
    assert fib["extensions"]["1.618"] == pytest.approx(38.2)


def test_fib_bull_leg():
    fib = _fib(100.0, 200.0, "up")
    assert fib["retracements"]["0.236"] == pytest.approx(176.4)
    assert fib["retracements"]["0.500"] == pytest.approx(150.0)
    assert fib["extensions"]["1.272"] == pytest.approx(227.2)
    assert fib["extensions"]["1.618"] == pytest.approx(261.8)


def _series(count: int, start: float, end: float) -> list[float]:
    step = (end - start) / (count - 1)
    return [start + step * i for i in range(count)]


def test_plan_bearish_bounce_requires_rr():
    # A year falling from 200 to 100: price below both MAs, leg down.
    closes = closes_from(_series(365, 200.0, 100.0))
    ma50 = _ma(closes, 50)
    ma200 = _ma(closes, 200)
    trend, _ = _trend(100.0, ma50, ma200)
    assert trend == "bearish"
    fib = _fib(100.0, 200.0, "down")
    plan = _plan(closes, 100.0, ma50, ma200, trend, "down", fib)
    assert plan is not None
    assert plan["target1"] == pytest.approx(138.2)
    assert plan["rr"] >= 0
    # The zone sits on the first retracement.
    assert plan["zone_low"] <= 123.6 <= plan["zone_high"]


def test_plan_bullish_continuation():
    # A year rising from 100 to 200: price above both MAs, leg up.
    closes = closes_from(_series(365, 100.0, 200.0))
    ma50 = _ma(closes, 50)
    ma200 = _ma(closes, 200)
    trend, _ = _trend(200.0, ma50, ma200)
    assert trend == "bullish"
    fib = _fib(100.0, 200.0, "up")
    plan = _plan(closes, 200.0, ma50, ma200, trend, "up", fib)
    assert plan is not None
    assert plan["target1"] == pytest.approx(227.2)
    assert plan["target2"] == pytest.approx(261.8)


def test_analyze_pair_end_to_end():
    closes = closes_from(_series(365, 200.0, 100.0))
    analysis = analyze_pair(symbol="TEST", name="Test", quote="USDC", closes=closes)
    assert analysis["trend"] == "bearish"
    assert analysis["swing_high"] == pytest.approx(200.0)
    assert analysis["swing_low"] == pytest.approx(100.0)
    assert analysis["leg"] == "down"
    assert analysis["fib"]["retracements"]["0.382"] == pytest.approx(138.2)
    assert analysis["plan"] is None or analysis["plan"]["rr"] >= 0
    assert len(analysis["series"]) == 365
    assert analysis["insufficient_history"] is False


def test_insufficient_history_flag():
    closes = closes_from([100.0, 101.0, 102.0])
    analysis = analyze_pair(symbol="NEW", name="New", quote="USDC", closes=closes)
    assert analysis["insufficient_history"] is True
    assert analysis["ma50"] is None
    assert analysis["trend"] == "unknown"
