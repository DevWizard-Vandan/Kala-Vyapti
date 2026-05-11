from dataclasses import dataclass
from datetime import date
import math
import pandas as pd
import numpy as np
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from backtest.data_loader import DataLoader
    from engine.signals.signal_engine import SignalEngine

@dataclass
class BacktestResult:
    trades: list[dict]
    total_pnl: float
    win_rate: float
    avg_win: float
    avg_loss: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    capital_curve: list[float]

class BacktestEngine:
    def __init__(self, data_loader: 'DataLoader', signal_engine: 'SignalEngine',
                 initial_capital: float = 500000.0):
        self.data_loader = data_loader
        self.signal_engine = signal_engine
        self.initial_capital = initial_capital

    def _position_size(self, capital: float, entry_price: float) -> int:
        return math.floor((capital * 0.02) / entry_price)

    def run(self, symbol: str, from_date: date, to_date: date,
            timeframe: str = "15m") -> BacktestResult:

        # Load all candles in chronological order
        df = self.data_loader.get_candles(symbol, from_date, to_date, timeframe)
        if df.empty:
            return BacktestResult(
                trades=[], total_pnl=0.0, win_rate=0.0, avg_win=0.0, avg_loss=0.0,
                max_drawdown=0.0, sharpe_ratio=0.0, total_trades=0, capital_curve=[]
            )

        capital = self.initial_capital
        capital_curve = []
        trades = []

        position = None

        # Simulated chronological walk
        for i in range(1, len(df)):
            # Up to current candle index 'i', inclusive or exclusive based on requirement.
            # SignalEngine should evaluate on completed candles. We pass history up to i.
            history_df = df.iloc[:i]

            current_candle = history_df.iloc[-1]
            next_candle = df.iloc[i]

            signal = self.signal_engine.evaluate(history_df, symbol, timeframe)

            # Position Management
            if position:
                # 1. Check Stop Loss
                if next_candle['low'] <= position['stop_loss_price']:
                    exit_price = position['stop_loss_price']
                    # If open gaps down below SL, we exit at open price
                    if next_candle['open'] < exit_price:
                        exit_price = next_candle['open']

                    pnl = (exit_price - position['entry_price']) * position['units']
                    pnl -= 40 # Brokerage 20 in + 20 out
                    capital += (position['entry_price'] * position['units']) + pnl
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': next_candle['timestamp'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'exit_reason': 'STOP_LOSS'
                    })
                    position = None

                # 2. Check Exit Signal
                elif signal.action == "EXIT":
                    # Exit at close of the candle where signal triggered (next_candle close)
                    exit_price = next_candle['close']
                    pnl = (exit_price - position['entry_price']) * position['units']
                    pnl -= 40 # Brokerage
                    capital += (position['entry_price'] * position['units']) + pnl
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': next_candle['timestamp'],
                        'entry_price': position['entry_price'],
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'exit_reason': 'SIGNAL'
                    })
                    position = None

            # If no position, check for ENTRY
            if not position and signal.action == "BUY":
                entry_price = next_candle['open']
                units = self._position_size(capital, entry_price)
                if units > 0:
                    capital -= (entry_price * units) # Cost of acquiring units
                    position = {
                        'entry_time': next_candle['timestamp'],
                        'entry_price': entry_price,
                        'units': units,
                        'stop_loss_price': entry_price * 0.60
                    }

            # End of step, record capital (including unrealized if any, but we'll just track realized to keep simple)
            # Actually, standard is realized capital curve + value of position
            current_value = capital
            if position:
                current_value += position['units'] * next_candle['close']
            capital_curve.append(current_value)

        # Force exit at the end if position is still open
        if position:
            last_candle = df.iloc[-1]
            exit_price = last_candle['close']
            pnl = (exit_price - position['entry_price']) * position['units']
            pnl -= 40
            capital += (position['entry_price'] * position['units']) + pnl
            trades.append({
                'entry_time': position['entry_time'],
                'exit_time': last_candle['timestamp'],
                'entry_price': position['entry_price'],
                'exit_price': exit_price,
                'pnl': pnl,
                'exit_reason': 'END_OF_BACKTEST'
            })
            capital_curve[-1] = capital

        # Calculate Stats
        total_pnl = sum(t['pnl'] for t in trades)
        total_trades = len(trades)
        wins = [t['pnl'] for t in trades if t['pnl'] > 0]
        losses = [t['pnl'] for t in trades if t['pnl'] <= 0]

        win_rate = len(wins) / total_trades if total_trades > 0 else 0.0
        avg_win = sum(wins) / len(wins) if wins else 0.0
        avg_loss = sum(losses) / len(losses) if losses else 0.0

        # Max Drawdown
        max_dd = 0.0
        peak = self.initial_capital
        for c in capital_curve:
            if c > peak:
                peak = c
            dd = (peak - c) / peak
            if dd > max_dd:
                max_dd = dd

        # Sharpe Ratio (Approximate Daily, annualized)
        # We need daily returns, but capital_curve is per candle.
        # So we'll approximate per-candle return to calculate standard dev.
        returns = pd.Series(capital_curve).pct_change().dropna()
        if not returns.empty and returns.std() != 0:
            # Assume 252 trading days, roughly 25 candles per day for 15m.
            # 252 * 25 = 6300 candles per year
            sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(6300)
        else:
            sharpe_ratio = 0.0

        return BacktestResult(
            trades=trades,
            total_pnl=total_pnl,
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            max_drawdown=max_dd,
            sharpe_ratio=float(sharpe_ratio),
            total_trades=total_trades,
            capital_curve=capital_curve
        )
