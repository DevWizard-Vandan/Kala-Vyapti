from __future__ import annotations

import math
from datetime import datetime
from typing import Any

from kala_vyapti_core import (
    PyCandle,
    py_adx,
    py_ema,
    py_macd,
    py_supertrend,
    py_supertrend_ai,
)

from .models import Signal


THRESHOLDS = {
    "15m": {
        "adx_min": 25,
        "dmi_plus_min": 21,
        "dmi_minus_max": 15,
        "macd_hist_min": 5,
    },
    "1h": {
        "adx_min": 25,
        "dmi_plus_min": 21,
        "dmi_minus_max": 20,
        "macd_hist_min": 0,
    },
    "1d": {
        "adx_min": 25,
        "dmi_plus_min": 21,
        "dmi_minus_max": 25,
        "macd_hist_min": 0,
    },
}


class SignalEngine:
    def __init__(self, symbol: str, timeframe: str = "15m") -> None:
        """Initialize the signal engine for one symbol/timeframe stream."""
        self.symbol = symbol
        self.timeframe = timeframe
        self.thresholds = THRESHOLDS.get(timeframe, THRESHOLDS["15m"])
        self.position_open = False

    def evaluate(self, candles: list[dict]) -> Signal:
        """
        candles: list of dicts with keys: timestamp, open, high, low, close, volume
        Returns a Signal based on all strategy conditions.

        BUY conditions (ALL must be true):
          - ADX > 25
          - DMI+ > DMI-
          - DMI- < 15
          - DMI+ > 21
          - EMA(9) > EMA(30) > EMA(100) > EMA(300)
          - MACD histogram > 5
          - SuperTrend AI bullish (trend == 1 on latest candle)

        EXIT: any single condition above fails while position is open.
        NONE: default when no BUY conditions met.

        confidence: fraction of conditions met (0.0-1.0), 7 conditions total.
        """
        timestamp = self._latest_timestamp(candles)

        if len(candles) < 300:
            return self._empty_signal(timestamp)

        py_candles = self._to_py_candles(candles)
        closes = [float(candle["close"]) for candle in candles]

        adx_vals, plus_di_vals, minus_di_vals = py_adx(py_candles, 14)
        _, _, macd_hist_vals = py_macd(py_candles, 12, 26, 9)
        standard_supertrend, _, _ = py_supertrend(py_candles, 10, 3.0)
        supertrend_ai_result = py_supertrend_ai(py_candles, 10, 1.0, 5.0, 0.5, 10.0, 2)

        latest_adx = self._latest_number(adx_vals)
        latest_plus_di = self._latest_number(plus_di_vals)
        latest_minus_di = self._latest_number(minus_di_vals)
        latest_macd_hist = self._latest_number(macd_hist_vals)
        latest_supertrend = int(standard_supertrend[-1]) if standard_supertrend else 0
        latest_supertrend_ai = (
            int(supertrend_ai_result["trend"][-1]) if supertrend_ai_result["trend"] else 0
        )

        ema_aligned = self._check_ema_alignment(closes)
        supertrend_bullish = latest_supertrend == 1
        supertrend_ai_bullish = latest_supertrend_ai == 1

        conditions = [
            latest_adx > self.thresholds["adx_min"],
            latest_plus_di > latest_minus_di,
            latest_minus_di < self.thresholds["dmi_minus_max"],
            latest_plus_di > self.thresholds["dmi_plus_min"],
            ema_aligned,
            latest_macd_hist > self.thresholds["macd_hist_min"],
            supertrend_ai_bullish,
        ]
        confidence = sum(conditions) / 7.0

        if all(conditions):
            action = "BUY"
            self.position_open = True
        elif self.position_open:
            action = "EXIT"
            self.position_open = False
        else:
            action = "NONE"

        return Signal(
            timestamp=timestamp,
            symbol=self.symbol,
            action=action,
            timeframe=self.timeframe,
            adx=latest_adx,
            dmi_plus=latest_plus_di,
            dmi_minus=latest_minus_di,
            ema_aligned=ema_aligned,
            macd_hist=latest_macd_hist,
            supertrend_bullish=supertrend_bullish,
            supertrend_ai_bullish=supertrend_ai_bullish,
            confidence=confidence,
        )

    def _to_py_candles(self, candles: list[dict]) -> list[PyCandle]:
        """Convert OHLCV dictionaries into Rust extension candle objects."""
        return [
            PyCandle(
                float(candle["open"]),
                float(candle["high"]),
                float(candle["low"]),
                float(candle["close"]),
                float(candle["volume"]),
            )
            for candle in candles
        ]

    def _check_ema_alignment(self, closes: list[float]) -> bool:
        """Return whether EMA(9) > EMA(30) > EMA(100) > EMA(300)."""
        if len(closes) < 300:
            return False

        py_candles = [
            PyCandle(close, close, close, close, 0.0)
            for close in closes
        ]
        ema_values = []
        for period in (9, 30, 100, 300):
            ema_value = self._latest_number(py_ema(py_candles, period))
            ema_values.append(ema_value)

        return ema_values[0] > ema_values[1] > ema_values[2] > ema_values[3]

    def _empty_signal(self, timestamp: datetime) -> Signal:
        """Return a neutral signal when data is unavailable or insufficient."""
        return Signal(
            timestamp=timestamp,
            symbol=self.symbol,
            action="NONE",
            timeframe=self.timeframe,
            adx=0.0,
            dmi_plus=0.0,
            dmi_minus=0.0,
            ema_aligned=False,
            macd_hist=0.0,
            supertrend_bullish=False,
            supertrend_ai_bullish=False,
            confidence=0.0,
        )

    @staticmethod
    def _latest_number(values: list[float]) -> float:
        """Return the latest finite numeric value, or 0.0 for missing data."""
        if not values:
            return 0.0

        value = float(values[-1])
        if math.isnan(value) or math.isinf(value):
            return 0.0
        return value

    @staticmethod
    def _latest_timestamp(candles: list[dict]) -> datetime:
        """Return the latest candle timestamp as a datetime."""
        if not candles:
            return datetime.now()

        timestamp: Any = candles[-1].get("timestamp")
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            return datetime.fromisoformat(timestamp)
        return datetime.now()
