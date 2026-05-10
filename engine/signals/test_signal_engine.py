from datetime import datetime, timedelta

from engine.signals.models import Signal
from engine.signals.signal_engine import SignalEngine


def synthetic_trending_candles(count: int) -> list[dict]:
    start = datetime(2026, 1, 1, 9, 15)
    candles = []

    for index in range(count):
        close = 100.0 + index * 1.25
        candles.append(
            {
                "timestamp": start + timedelta(minutes=15 * index),
                "open": close - 0.5,
                "high": close + 1.0,
                "low": close - 1.0,
                "close": close,
                "volume": 1000.0 + index,
            }
        )

    return candles


def test_signal_engine_returns_signal_for_trending_candles() -> None:
    engine = SignalEngine("NIFTY")

    signal = engine.evaluate(synthetic_trending_candles(350))

    assert isinstance(signal, Signal)
    assert 0.0 <= signal.confidence <= 1.0
    assert signal.action in {"BUY", "EXIT", "NONE"}


def test_signal_engine_returns_none_for_insufficient_data() -> None:
    engine = SignalEngine("NIFTY")

    signal = engine.evaluate(synthetic_trending_candles(299))

    assert isinstance(signal, Signal)
    assert signal.action == "NONE"
    assert signal.adx == 0.0
    assert signal.dmi_plus == 0.0
    assert signal.dmi_minus == 0.0
    assert signal.ema_aligned is False
    assert signal.macd_hist == 0.0
    assert signal.supertrend_bullish is False
    assert signal.supertrend_ai_bullish is False
    assert signal.confidence == 0.0
