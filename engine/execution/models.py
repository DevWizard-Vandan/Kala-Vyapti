from dataclasses import dataclass
from datetime import datetime, date
from typing import Literal, Optional

@dataclass
class Trade:
    id: str
    entry_time: datetime
    exit_time: Optional[datetime]
    symbol: str
    strike: int
    option_type: Literal["CE", "PE"]
    expiry: date
    lots: int
    entry_price: float
    exit_price: Optional[float]
    stop_loss_price: float        # entry_price * 0.60
    realized_pnl: Optional[float]
    exit_reason: Optional[str]       # "stop_loss" | "signal_exit" | "daily_limit"
    mode: Literal["paper", "live"]
