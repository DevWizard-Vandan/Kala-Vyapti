from datetime import datetime
from engine.execution.paper_trader import PaperTrader
from engine.signals.models import Signal

def create_mock_signal(action: str, symbol: str = "NIFTY") -> Signal:
    return Signal(
        timestamp=datetime(2026, 1, 1, 9, 30),
        symbol=symbol,
        action=action,
        timeframe="15m",
        adx=30.0,
        dmi_plus=25.0,
        dmi_minus=10.0,
        ema_aligned=True,
        macd_hist=6.0,
        supertrend_bullish=True,
        supertrend_ai_bullish=True,
        confidence=1.0
    )

def test_paper_trader_enters_position_on_buy():
    trader = PaperTrader(initial_capital=500000)
    signal = create_mock_signal("BUY")

    result = trader.on_signal(signal, current_price=100.0)

    assert result == "ENTERED"
    assert trader.position is not None
    assert trader.position.entry_price == 100.0
    assert trader.position.stop_loss_price == 60.0
    assert trader.position.lots == 1
    assert trader.position.symbol == "NIFTY"

def test_paper_trader_blocks_when_position_open():
    trader = PaperTrader(initial_capital=500000)

    # Enter first position
    signal1 = create_mock_signal("BUY")
    trader.on_signal(signal1, current_price=100.0)
    assert trader.position is not None

    # Try to enter second position
    signal2 = create_mock_signal("BUY", symbol="BANKNIFTY")
    result = trader.on_signal(signal2, current_price=200.0)

    assert result == "BLOCKED"
    assert trader.position.symbol == "NIFTY"  # Still the first position
    assert len(trader.trades) == 0

def test_paper_trader_check_stop_loss_exits_at_minus_40_percent():
    trader = PaperTrader(initial_capital=500000)

    # Enter position
    signal = create_mock_signal("BUY")
    trader.on_signal(signal, current_price=100.0)

    # Stop loss is at 60.0
    assert trader.position.stop_loss_price == 60.0

    # Current price above stop loss -> no exit
    trader.check_stop_loss(current_price=61.0, current_time=datetime(2026, 1, 1, 9, 35))
    assert trader.position is not None

    # Current price at stop loss -> exit
    trader.check_stop_loss(current_price=60.0, current_time=datetime(2026, 1, 1, 9, 40))
    assert trader.position is None

    assert len(trader.trades) == 1
    assert trader.trades[0].exit_reason == "stop_loss"
    assert trader.trades[0].realized_pnl == -40.0 * 1  # 100 -> 60 with 1 lot

def test_paper_trader_blocks_on_daily_loss_limit():
    trader = PaperTrader(initial_capital=10000)

    # Set daily_pnl to trigger the limit (-3% of 10000 is -300)
    trader.daily_pnl = -301.0

    signal = create_mock_signal("BUY")
    result = trader.on_signal(signal, current_price=100.0)

    assert result == "BLOCKED"
    assert trader.position is None
