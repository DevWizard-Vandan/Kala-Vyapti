import os
import logging
from typing import Callable, List
from threading import Thread
from kiteconnect import KiteTicker

NIFTY_TOKEN = 256265       # NSE Nifty 50 index instrument token
BANKNIFTY_TOKEN = 260105   # NSE BankNifty index instrument token

logger = logging.getLogger(__name__)

class KiteFeed:
    def __init__(self, on_candle_callback: Callable, timeframe_minutes: int = 15):
        self.api_key = os.getenv("KITE_API_KEY", "")
        self.access_token = os.getenv("KITE_ACCESS_TOKEN", "")
        self.on_candle = on_candle_callback

        # Import CandleBuilder here to avoid circular imports or missing dependencies if engine isn't fully loaded
        from engine.data.candle_builder import CandleBuilder
        self._candle_builder = CandleBuilder(timeframe_minutes=timeframe_minutes)

        self.ticker = None
        self.tokens = []
        self._thread = None

    def start(self, tokens: List[int] = [NIFTY_TOKEN]):
        self.tokens = tokens
        self.ticker = KiteTicker(self.api_key, self.access_token)

        self.ticker.on_ticks = self._on_ticks
        self.ticker.on_connect = self._on_connect
        self.ticker.on_close = self._on_close
        self.ticker.on_error = self._on_error

        # Start in background thread
        self._thread = Thread(target=self.ticker.connect, kwargs={"threaded": False})
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        if self.ticker:
            self.ticker.close()
            self.ticker = None
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def _on_ticks(self, ws, ticks):
        for tick in ticks:
            candle = self._candle_builder.on_tick(tick)
            if candle is not None:
                self.on_candle(candle)

    def _on_connect(self, ws, response):
        logger.info("Kite WebSocket connected")
        ws.subscribe(self.tokens)
        ws.set_mode(ws.MODE_FULL, self.tokens)

    def _on_close(self, ws, code, reason):
        logger.warning(f"Kite WebSocket closed: {code} {reason}")

    def _on_error(self, ws, code, reason):
        logger.error(f"Kite WebSocket error: {code} {reason}")
