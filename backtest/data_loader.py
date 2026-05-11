import logging
from datetime import date, timedelta
from pathlib import Path
import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self, cache_dir: str = "data/historical"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

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
        cached_df = self._load_from_cache(symbol, from_date, to_date)

        # Determine missing date ranges
        missing_ranges = []
        if cached_df is None or cached_df.empty:
            missing_ranges.append((from_date, to_date))
        else:
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
            fetched_df = self._fetch_from_yfinance(symbol, start, end, timeframe)
            if not fetched_df.empty:
                dfs_to_concat.append(fetched_df)
                new_data_fetched = True

        if not dfs_to_concat:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        final_df = pd.concat(dfs_to_concat, ignore_index=True)
        final_df = final_df.drop_duplicates(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)

        # Drop helper columns if they exist
        if 'year' in final_df.columns:
            final_df = final_df.drop(columns=['year'])
        if 'month' in final_df.columns:
            final_df = final_df.drop(columns=['month'])

        # Filter to exact requested range
        from_datetime = pd.to_datetime(from_date).tz_localize('Asia/Kolkata')
        to_datetime = (pd.to_datetime(to_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)).tz_localize('Asia/Kolkata')

        final_df = final_df[(final_df['timestamp'] >= from_datetime) & (final_df['timestamp'] <= to_datetime)]

        if new_data_fetched:
            self._save_to_cache(final_df, symbol)

        # Drop helper columns if they exist
        if 'year' in final_df.columns:
            final_df = final_df.drop(columns=['year'])
        if 'month' in final_df.columns:
            final_df = final_df.drop(columns=['month'])

        return final_df

    def _fetch_from_yfinance(self, symbol: str, from_date: date, to_date: date, timeframe: str) -> pd.DataFrame:
        logger.info(f"Fetching from yfinance: {symbol} from {from_date} to {to_date}")

        end_date = to_date + timedelta(days=1)
        yf_symbol = "^NSEI" if symbol == "NIFTY 50" else symbol

        ticker = yf.Ticker(yf_symbol)
        df = ticker.history(
            start=from_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval=timeframe
        )

        if df.empty:
            return pd.DataFrame(columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

        if df.index.tz is None:
            df.index = df.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
        else:
            df.index = df.index.tz_convert('Asia/Kolkata')

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
        for col in ['open', 'high', 'low', 'close', 'volume']:
            df[col] = df[col].astype('float64')

        return df

    def _cache_path(self, symbol: str, year: int, month: int) -> Path:
        symbol_dir = self.cache_dir / symbol.replace(" ", "_")
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
        return combined_df

    def _save_to_cache(self, df: pd.DataFrame, symbol: str) -> None:
        if df.empty:
            return

        # Group by year and month
        df['year'] = df['timestamp'].dt.year
        df['month'] = df['timestamp'].dt.month

        for (year, month), group in df.groupby(['year', 'month']):
            path = self._cache_path(symbol, year, month)

            # If path already exists, load and combine to avoid overwriting existing days
            if path.exists():
                existing_df = pd.read_parquet(path)
                combined = pd.concat([existing_df, group], ignore_index=True)
                combined = combined.drop_duplicates(subset=['timestamp']).sort_values('timestamp')
            else:
                combined = group

            # Drop the helper columns before saving
            combined_to_save = combined.drop(columns=['year', 'month'], errors='ignore')
            combined_to_save.to_parquet(path, index=False)
            logger.info(f"Saved to cache: {path}")
