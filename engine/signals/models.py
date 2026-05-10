from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass
class Signal:
    timestamp: datetime
    symbol: str
    action: Literal["BUY", "EXIT", "NONE"]
    timeframe: str
    adx: float
    dmi_plus: float
    dmi_minus: float
    ema_aligned: bool
    macd_hist: float
    supertrend_bullish: bool
    supertrend_ai_bullish: bool
    confidence: float        # 0.0-1.0
