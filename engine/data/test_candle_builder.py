from datetime import datetime
from engine.data.candle_builder import CandleBuilder

def test_candle_builder_aggregates_ticks():
    builder = CandleBuilder(timeframe_minutes=15)

    # Simulate ticks starting from 9:16
    tick1 = {
        "timestamp": datetime(2026, 1, 1, 9, 16, 0),
        "last_price": 100.0,
        "last_traded_quantity": 10,
        "instrument_token": 12345
    }

    tick2 = {
        "timestamp": datetime(2026, 1, 1, 9, 18, 0),
        "last_price": 105.0,
        "last_traded_quantity": 20,
        "instrument_token": 12345
    }

    tick3 = {
        "timestamp": datetime(2026, 1, 1, 9, 25, 0),
        "last_price": 95.0,
        "last_traded_quantity": 15,
        "instrument_token": 12345
    }

    assert builder.on_tick(tick1) is None
    assert builder.on_tick(tick2) is None
    assert builder.on_tick(tick3) is None

    assert builder.current_candle is not None
    assert builder.current_candle["open"] == 100.0
    assert builder.current_candle["high"] == 105.0
    assert builder.current_candle["low"] == 95.0
    assert builder.current_candle["close"] == 95.0
    assert builder.current_candle["volume"] == 45

    # Cross boundary
    tick4 = {
        "timestamp": datetime(2026, 1, 1, 9, 31, 0),
        "last_price": 98.0,
        "last_traded_quantity": 5,
        "instrument_token": 12345
    }

    completed = builder.on_tick(tick4)
    assert completed is not None
    assert completed["open"] == 100.0
    assert completed["high"] == 105.0
    assert completed["low"] == 95.0
    assert completed["close"] == 95.0
    assert completed["volume"] == 45
    assert completed["timestamp"] == datetime(2026, 1, 1, 9, 15, 0)

    # Verify new candle started
    assert builder.current_candle["open"] == 98.0
    assert builder.current_candle["timestamp"] == datetime(2026, 1, 1, 9, 30, 0)

def test_candle_builder_detects_boundary_crossing():
    builder = CandleBuilder(timeframe_minutes=15)

    # Exact boundary 09:15
    tick1 = {
        "timestamp": datetime(2026, 1, 1, 9, 15, 0),
        "last_price": 100.0,
        "last_traded_quantity": 10,
        "instrument_token": 12345
    }

    assert builder.on_tick(tick1) is None

    # Exact boundary 09:30
    tick2 = {
        "timestamp": datetime(2026, 1, 1, 9, 30, 0),
        "last_price": 102.0,
        "last_traded_quantity": 15,
        "instrument_token": 12345
    }

    completed = builder.on_tick(tick2)
    assert completed is not None
    assert completed["timestamp"] == datetime(2026, 1, 1, 9, 15, 0)
    assert completed["close"] == 100.0

    # New boundary
    assert builder.current_candle["timestamp"] == datetime(2026, 1, 1, 9, 30, 0)
