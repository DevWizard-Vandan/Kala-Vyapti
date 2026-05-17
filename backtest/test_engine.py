import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from backtest.engine import BacktestEngine, BacktestResult
from engine.signals.models import Signal

class MockDataLoader:
    def __init__(self, df):
        self.df = df

    def get_candles(self, symbol, from_date, to_date, timeframe="15m"):
        return self.df

class MockSignalEngine:
    def __init__(self, action_map):
        self.action_map = action_map

    def evaluate(self, candles):
        last_idx = len(candles) - 1
        action = self.action_map.get(last_idx, "NONE")
        return Signal(
            timestamp=candles[-1]['timestamp'],
            symbol="NIFTY 50",
            action=action,
            timeframe="15m",
            adx=0.0,
            dmi_plus=0.0,
            dmi_minus=0.0,
            ema_aligned=True,
            macd_hist=0.0,
            supertrend_bullish=True,
            supertrend_ai_bullish=True,
            confidence=1.0
        )

def generate_synthetic_data(num_candles=500):
    start_time = datetime(2023, 1, 1, 9, 15, tzinfo=ZoneInfo('Asia/Kolkata'))

    timestamps = []
    opens = []
    highs = []
    lows = []
    closes = []

    current_price = 1000.0

    for i in range(num_candles):
        timestamps.append(start_time + timedelta(minutes=15 * i))

        # Simple trend + reversal
        if i < 380:
            # Uptrend
            open_price = current_price
            close_price = current_price + 2.0
            high_price = close_price + 1.0
            low_price = open_price - 1.0
        else:
            # Downtrend
            open_price = current_price
            close_price = current_price - 2.0
            high_price = open_price + 1.0
            low_price = close_price - 1.0

        opens.append(open_price)
        highs.append(high_price)
        lows.append(low_price)
        closes.append(close_price)

        current_price = close_price

    return pd.DataFrame({
        'timestamp': timestamps,
        'open': opens,
        'high': highs,
        'low': lows,
        'close': closes,
        'volume': [1000] * num_candles
    })

def test_backtest_engine_basic_run():
    df = generate_synthetic_data(500)
    data_loader = MockDataLoader(df)

    # Signals are emitted after the 300-candle warmup.
    # Buy at index 310, exit at index 360 (uptrend -> win)
    # Buy at index 410, exit at index 460 (downtrend -> loss/stop loss)
    action_map = {
        310: "BUY",
        360: "EXIT",
        410: "BUY",
        460: "EXIT"
    }
    signal_engine = MockSignalEngine(action_map)

    engine = BacktestEngine(data_loader, signal_engine, initial_capital=500000.0)

    result = engine.run("NIFTY 50", date(2023, 1, 1), date(2023, 1, 10))

    assert isinstance(result, BacktestResult)
    assert result.total_trades == 2
    assert result.win_rate >= 0.0 and result.win_rate <= 1.0
    assert len(result.capital_curve) == 199 # length of df - 301 warmup

    # Verify trade details
    trade1 = result.trades[0]
    assert trade1['exit_reason'] == 'SIGNAL'
    assert trade1['pnl'] > 0 # Should be a win since it was in an uptrend

    trade2 = result.trades[1]
    # Trade 2 might hit stop loss before index 350 because it's a downtrend
    assert trade2['exit_reason'] in ['SIGNAL', 'STOP_LOSS']

    # Assert fields are present
    assert hasattr(result, 'total_pnl')
    assert hasattr(result, 'avg_win')
    assert hasattr(result, 'avg_loss')
    assert hasattr(result, 'max_drawdown')
    assert hasattr(result, 'sharpe_ratio')
