import os
import uuid
import logging
from datetime import datetime, date
from typing import Optional, List, Dict

from engine.signals.models import Signal
from engine.execution.models import Trade
from engine.risk.risk_gate import RiskGate

logger = logging.getLogger(__name__)

class PaperTrader:
    def __init__(self, initial_capital: float = float(os.getenv("PAPER_CAPITAL", 500000))):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.position: Optional[Trade] = None      # current open Trade or None
        self.trades: List[Trade] = []              # completed trades
        self.daily_pnl = 0.0
        self.risk_gate = RiskGate()

    def on_signal(self, signal: Signal, current_price: float) -> str:
        if signal.action == "BUY":
            # Check if position already open
            if self.position is not None:
                return "BLOCKED"

            # Check daily loss limit (-3% of initial capital)
            max_loss = -0.03 * self.initial_capital
            if self.daily_pnl <= max_loss:
                logger.warning("Daily loss limit reached, blocking new trade")
                return "BLOCKED"

            # Check RiskGate
            # Portfolio state mock for now
            portfolio_state = {"capital": self.capital, "open_positions": 0}
            is_valid, reason = self.risk_gate.validate(signal, portfolio_state)
            if not is_valid:
                logger.warning(f"RiskGate blocked trade: {reason}")
                return "BLOCKED"

            # Calculate stop_loss
            stop_loss = current_price * 0.60

            # Open paper position
            self.position = Trade(
                id=str(uuid.uuid4()),
                entry_time=signal.timestamp,
                exit_time=None,
                symbol=signal.symbol,
                strike=0, # Mocked for now, need option chain integration later
                option_type="CE", # Mocked
                expiry=date.today(), # Mocked
                lots=1, # Mocked
                entry_price=current_price,
                exit_price=None,
                stop_loss_price=stop_loss,
                realized_pnl=None,
                exit_reason=None,
                mode="paper"
            )

            logger.info(f"Entered paper trade: {self.position.id} at {current_price} SL: {stop_loss}")
            # Stub: Send Telegram alert

            return "ENTERED"

        elif signal.action == "EXIT":
            if self.position is not None:
                self._close_position(current_price, signal.timestamp, "signal_exit")
                return "EXITED"
            return "NONE"

        return "NONE"

    def _close_position(self, exit_price: float, exit_time: datetime, reason: str):
        if self.position is None:
            return

        # Calculate PnL (Mocked 1 lot size = 1 for simple tracking, usually 50 for Nifty)
        # We need actual lot size to calculate properly. For now we assume lots=1 represents 1 quantity.
        quantity = self.position.lots
        pnl = (exit_price - self.position.entry_price) * quantity

        self.position.exit_price = exit_price
        self.position.exit_time = exit_time
        self.position.realized_pnl = pnl
        self.position.exit_reason = reason

        self.capital += pnl
        self.daily_pnl += pnl

        self.trades.append(self.position)

        logger.info(f"Exited paper trade: {self.position.id} at {exit_price} PnL: {pnl} Reason: {reason}")
        # Stub: Send Telegram alert

        self.position = None

    def check_stop_loss(self, current_price: float, current_time: datetime = None):
        if self.position is not None:
            if current_price <= self.position.stop_loss_price:
                exit_time = current_time if current_time else datetime.now()
                self._close_position(current_price, exit_time, "stop_loss")

    def get_summary(self) -> Dict:
        win_rate = 0.0
        total_pnl = sum(t.realized_pnl or 0.0 for t in self.trades)

        if self.trades:
            wins = sum(1 for t in self.trades if t.realized_pnl and t.realized_pnl > 0)
            win_rate = wins / len(self.trades)

        return {
            "capital": self.capital,
            "open_position": self.position is not None,
            "total_trades": len(self.trades),
            "win_rate": win_rate,
            "total_pnl": total_pnl
        }
