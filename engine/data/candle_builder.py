from datetime import datetime, timedelta
from typing import Dict, Optional

class CandleBuilder:
    def __init__(self, timeframe_minutes: int = 15):
        self.timeframe_minutes = timeframe_minutes
        self.current_candle: Optional[Dict] = None
        self.current_boundary: Optional[datetime] = None

    def on_tick(self, tick: dict) -> Optional[Dict]:
        """
        tick has: instrument_token, last_price, timestamp, volume etc.
        Aggregate into current timeframe candle.
        Return completed candle dict when timeframe boundary crossed.
        Candle dict: {timestamp, open, high, low, close, volume}
        """
        # Note: Kite API returns timestamp as datetime object in 'exchange_timestamp' or 'timestamp'
        tick_time = tick.get("exchange_timestamp") or tick.get("timestamp")

        if not tick_time:
            return None

        last_price = tick.get("last_price", 0.0)
        volume = tick.get("volume_traded", 0) # Use volume_traded for the current tick or cumulative? Assuming cumulative for now, will handle difference if needed. But usually ticks give last traded quantity or we can accumulate volume. Wait, let's assume we accumulate `last_traded_quantity` or just use cumulative volume if it's snapshot. Usually, we need to accumulate last traded quantity. Let's assume tick has `last_traded_quantity` or we can approximate.
        # Often Kite ticker sends `last_traded_quantity`.
        ltq = tick.get("last_traded_quantity", 0)

        boundary = self._candle_boundary(tick_time)

        completed_candle = None

        if self.current_boundary is None:
            # First tick
            self.current_boundary = boundary
            self.current_candle = {
                "timestamp": self.current_boundary,
                "open": last_price,
                "high": last_price,
                "low": last_price,
                "close": last_price,
                "volume": ltq,
                "instrument_token": tick.get("instrument_token")
            }
        elif boundary > self.current_boundary:
            # Boundary crossed, complete the current candle
            completed_candle = self.current_candle.copy()

            # Start new candle
            self.current_boundary = boundary
            self.current_candle = {
                "timestamp": self.current_boundary,
                "open": last_price,
                "high": last_price,
                "low": last_price,
                "close": last_price,
                "volume": ltq,
                "instrument_token": tick.get("instrument_token")
            }
        else:
            # Update current candle
            if self.current_candle is not None:
                self.current_candle["high"] = max(self.current_candle["high"], last_price)
                self.current_candle["low"] = min(self.current_candle["low"], last_price)
                self.current_candle["close"] = last_price
                self.current_candle["volume"] += ltq

        return completed_candle

    def _candle_boundary(self, timestamp: datetime) -> datetime:
        """
        Round down to nearest timeframe boundary.
        e.g. 09:27 -> 09:15, 09:31 -> 09:30 for 15m.
        Note: Market opens at 09:15. For 15m, 09:15-09:30 is one candle.
        We can round down the minute.
        """
        # In IST, market opens at 9:15.
        # If timeframe is 15m, we want boundaries at 9:15, 9:30, 9:45, etc.
        # Number of minutes since market open (9:15) could be used, or we just round minutes.
        # Normal rounding to nearest 15 mins works: 0, 15, 30, 45
        minute = timestamp.minute
        rounded_minute = (minute // self.timeframe_minutes) * self.timeframe_minutes

        return timestamp.replace(minute=rounded_minute, second=0, microsecond=0)
