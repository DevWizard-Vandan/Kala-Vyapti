import logging
import os
import re
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)
IST = ZoneInfo('Asia/Kolkata')
NIFTY_50_INDEX_TOKEN = 256265

EMPTY_CANDLES_DF = pd.DataFrame({
    'timestamp': pd.Series(dtype='datetime64[ns, Asia/Kolkata]'),
    'open': pd.Series(dtype='float64'),
    'high': pd.Series(dtype='float64'),
    'low': pd.Series(dtype='float64'),
    'close': pd.Series(dtype='float64'),
    'volume': pd.Series(dtype='float64'),
})

KITE_INTERVALS = {
    "1m": "minute",
    "3m": "3minute",
    "5m": "5minute",
    "10m": "10minute",
    "15m": "15minute",
    "30m": "30minute",
    "1h": "60minute",
    "1d": "day",
}

YFINANCE_SYMBOLS = {
    "NIFTY 50": "^NSEI",
    "NIFTY": "^NSEI",
}

class DataLoader:
    def __init__(self, cache_dir: str = "data/historical", data_source: str | None = None):
        """Initialize historical data loading with Kite intraday or yfinance daily fallback."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.kite_api_key = os.getenv("KITE_API_KEY")
        self.kite_access_token = os.getenv("KITE_ACCESS_TOKEN")
        self.data_source = data_source or self._detect_data_source()

    def _detect_data_source(self) -> str:
        """Return the best available market data source for this environment."""
        if self.kite_api_key and self.kite_access_token:
            return "kite"

        if self.kite_api_key and not self.kite_access_token:
            logger.warning("KITE_API_KEY is set but KITE_ACCESS_TOKEN is missing; using yfinance daily fallback")

        return "yfinance_daily"

    def get_candles(
        self,
        symbol: str,
        from_date: date,
        to_date: date,
        timeframe: str = "15m"
    ) -> pd.DataFrame:
        """
        Returns DataFrame with columns:
        timestamp (datetime, IST), open, high, low, close, volume (all float64)
        """
        logger.info("Loading candles using data source: %s", self.data_source)
        if self.data_source == "yfinance_daily" and timeframe != "1d":
            logger.warning(
                "WARNING: Using daily candles as proxy for 15m - set KITE_API_KEY for true intraday data"
            )

        cached_df = self._load_from_cache(symbol, from_date, to_date)

        # Determine missing date ranges
        missing_ranges = []
        if cached_df is None or cached_df.empty:
            missing_ranges.append((from_date, to_date))
        else:
            cached_df = self._ensure_timestamp_dtype(cached_df)
            # Simple missing range check:
            # We assume cache is complete for a month if there's any data in that month.
            # However, standard backtest requires fetching missing dates exactly.
            # To be precise, let's find the missing days between from_date and to_date

            # This is a bit tricky with just df. Let's do a naive approach:
            # We find the min and max date in cache within the range.
            cached_dates = cached_df['timestamp'].dt.date
            min_cached = cached_dates.min()
            max_cached = cached_dates.max()

            # Check gaps at the start
            if min_cached > from_date:
                missing_ranges.append((from_date, min_cached - timedelta(days=1)))

            # Check gaps at the end
            if max_cached < to_date:
                missing_ranges.append((max_cached + timedelta(days=1), to_date))

        dfs_to_concat = [cached_df] if cached_df is not None and not cached_df.empty else []

        new_data_fetched = False
        for start, end in missing_ranges:
            if start > end:
                continue
            fetched_df = self._fetch_market_data(symbol, start, end, timeframe)
            if not fetched_df.empty:
                dfs_to_concat.append(fetched_df)
                new_data_fetched = True

        if not dfs_to_concat:
            return EMPTY_CANDLES_DF.copy()

        final_df = pd.concat(dfs_to_concat, ignore_index=True)
        final_df = self._ensure_timestamp_dtype(final_df)
        final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

        # Drop helper columns if they exist
        if 'year' in final_df.columns:
            final_df = final_df.drop(columns=['year'])
        if 'month' in final_df.columns:
            final_df = final_df.drop(columns=['month'])

        # Filter to exact requested range
        from_datetime = pd.Timestamp(datetime.combine(from_date, time.min, tzinfo=IST))
        to_datetime = pd.Timestamp(
            datetime.combine(to_date + timedelta(days=1), time.min, tzinfo=IST)
            - timedelta(seconds=1)
        )

        final_df = final_df[(final_df['timestamp'] >= from_datetime) & (final_df['timestamp'] <= to_datetime)]

        if new_data_fetched:
            self._save_to_cache(final_df, symbol)

        # Drop helper columns if they exist
        if 'year' in final_df.columns:
            final_df = final_df.drop(columns=['year'])
        if 'month' in final_df.columns:
            final_df = final_df.drop(columns=['month'])

        final_df = self._ensure_timestamp_dtype(final_df)
        return final_df

    def _fetch_market_data(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        """Fetch missing candles from the configured market data source."""
        if self.data_source == "kite":
            return self._fetch_from_nse(symbol, from_date, to_date, timeframe)

        return self._fetch_from_yfinance(symbol, from_date, to_date, timeframe)

    def _fetch_from_nse(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        """Fetch true NSE intraday index candles through Zerodha Kite historical data."""
        return self._fetch_from_kite(symbol, from_date, to_date, timeframe)

    def _fetch_from_kite(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        """Fetch Kite historical candles in 60-day chunks to respect API limits."""
        if symbol not in ("NIFTY 50", "NIFTY"):
            raise ValueError(f"Kite historical index token is not configured for symbol: {symbol}")

        if timeframe not in KITE_INTERVALS:
            raise ValueError(f"Unsupported Kite timeframe: {timeframe}")

        from kiteconnect import KiteConnect

        logger.info("Fetching true intraday candles from Kite: %s %s %s to %s", symbol, timeframe, from_date, to_date)
        kite = KiteConnect(api_key=self.kite_api_key)
        kite.set_access_token(self.kite_access_token)

        all_dfs = []
        chunk_start = from_date
        while chunk_start <= to_date:
            chunk_end = min(chunk_start + timedelta(days=59), to_date)
            data = kite.historical_data(
                NIFTY_50_INDEX_TOKEN,
                datetime.combine(chunk_start, time.min, tzinfo=IST),
                datetime.combine(chunk_end, time.max, tzinfo=IST),
                KITE_INTERVALS[timeframe],
            )
            if data:
                all_dfs.append(self._normalize_kite_data(data))
            chunk_start = chunk_end + timedelta(days=1)

        if not all_dfs:
            return EMPTY_CANDLES_DF.copy()

        combined_df = pd.concat(all_dfs, ignore_index=True)
        combined_df = self._ensure_timestamp_dtype(combined_df)
        return combined_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

    def _normalize_kite_data(self, data: list[dict]) -> pd.DataFrame:
        """Normalize Kite historical API rows into the backtester candle schema."""
        df = pd.DataFrame(data)
        if df.empty:
            return EMPTY_CANDLES_DF.copy()

        df = df.rename(columns={'date': 'timestamp'})
        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if 'volume' not in df.columns:
            df['volume'] = 0.0
        df = df[cols]
        df = self._ensure_timestamp_dtype(df)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype('float64')
        return df

    def _fetch_from_yfinance(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        effective_timeframe = "1d"
        logger.info("Fetching daily candles from yfinance: %s from %s to %s", symbol, from_date, to_date)

        yf_symbol = YFINANCE_SYMBOLS.get(symbol, symbol)
        end_date = to_date + timedelta(days=1)

        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(
            start=from_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=effective_timeframe
        )

        if df.empty:
            return EMPTY_CANDLES_DF.copy()

        return self._normalize_yfinance_df(df)

    def _ensure_timestamp_dtype(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return a copy with timestamp coerced to timezone-aware IST datetimes."""
        df = df.copy()
        if df.empty:
            return EMPTY_CANDLES_DF.copy()

        df['timestamp'] = (
            pd.to_datetime(df['timestamp'], utc=True)
            .astype('datetime64[ns, UTC]')
            .dt.tz_convert('Asia/Kolkata')
        )
        return df

    def _normalize_yfinance_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize a yfinance OHLCV response into the backtester candle schema."""
        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert(IST)
        else:
            df.index = df.index.tz_convert(IST)

        df = df.reset_index()
        df = df.rename(columns={
            'Datetime': 'timestamp',
            'Date': 'timestamp',
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Volume': 'volume'
        })

        cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
        if 'volume' not in df.columns:
            df['volume'] = 0.0

        df = df[cols]
        df = self._ensure_timestamp_dtype(df)
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype('float64')

        return df

    def _cache_path(self, symbol: str, year: int, month: int) -> Path:
        safe_symbol = re.sub(r'[^\w\-]', '_', symbol)
        symbol_dir = self.cache_dir / safe_symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)
        return symbol_dir / f"{year}-{month:02d}.parquet"

    def _load_from_cache(self, symbol: str, from_date: date, to_date: date) -> pd.DataFrame | None:
        # Load all months that overlap with [from_date, to_date]
        dfs = []

        start_year = from_date.year
        start_month = from_date.month
        end_year = to_date.year
        end_month = to_date.month

        current_year = start_year
        current_month = start_month

        while (current_year, current_month) <= (end_year, end_month):
            path = self._cache_path(symbol, current_year, current_month)
            if path.exists():
                logger.info(f"Loading cache: {path}")
                df = pd.read_parquet(path)
                dfs.append(df)

            current_month += 1
            if current_month > 12:
                current_month = 1
                current_year += 1

        if not dfs:
            return None

        combined_df = pd.concat(dfs, ignore_index=True)
        combined_df = self._ensure_timestamp_dtype(combined_df)
        return combined_df

    def _save_to_cache(self, df: pd.DataFrame, symbol: str) -> None:
        if df.empty:
            return

        df = self._ensure_timestamp_dtype(df)

        # Group by year and month
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month

        for (year, month), group in df.groupby(['year', 'month']):
            path = self._cache_path(symbol, year, month)

            # If path already exists, load and combine to avoid overwriting existing days
            if path.exists():
                existing_df = pd.read_parquet(path)
                existing_df = self._ensure_timestamp_dtype(existing_df)
                combined = pd.concat([existing_df, group], ignore_index=True)
                combined = self._ensure_timestamp_dtype(combined)
                combined = combined.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            else:
                combined = group

            # Drop the helper columns before saving
            combined_to_save = combined.drop(columns=['year', 'month'], errors='ignore')
            combined_to_save.to_parquet(path, index=False)
            logger.info(f"Saved to cache: {path}")
