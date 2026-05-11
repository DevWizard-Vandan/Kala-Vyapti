import pytest
import pandas as pd
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo
from backtest.data_loader import DataLoader
import shutil
import os
from pathlib import Path

@pytest.fixture
def temp_cache_dir(tmp_path):
    cache_dir = tmp_path / "historical"
    yield str(cache_dir)
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

def test_get_candles_columns_and_timezone(temp_cache_dir, mocker):
    dl = DataLoader(cache_dir=temp_cache_dir)

    # Mock yfinance to return a simple dataframe
    mock_df = pd.DataFrame({
        'timestamp': [
            datetime(2023, 1, 2, 9, 15, tzinfo=ZoneInfo('Asia/Kolkata')),
            datetime(2023, 1, 2, 9, 30, tzinfo=ZoneInfo('Asia/Kolkata'))
        ],
        'open': [18000.0, 18010.0],
        'high': [18020.0, 18025.0],
        'low': [17990.0, 18005.0],
        'close': [18010.0, 18020.0],
        'volume': [1000.0, 2000.0]
    })

    mocker.patch.object(dl, '_fetch_from_yfinance', return_value=mock_df)

    df = dl.get_candles('NIFTY 50', date(2023, 1, 1), date(2023, 1, 5))

    # Test columns
    expected_cols = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    assert list(df.columns) == expected_cols

    # Test types
    for col in ['open', 'high', 'low', 'close', 'volume']:
        assert df[col].dtype == 'float64'

    # Test timezone aware
    assert df['timestamp'].dt.tz is not None
    assert str(df['timestamp'].dt.tz) == 'Asia/Kolkata'

def test_caching_behavior(temp_cache_dir, mocker):
    dl = DataLoader(cache_dir=temp_cache_dir)

    mock_df = pd.DataFrame({
        'timestamp': [
            datetime(2023, 1, 2, 9, 15, tzinfo=ZoneInfo('Asia/Kolkata')),
            datetime(2023, 1, 2, 9, 30, tzinfo=ZoneInfo('Asia/Kolkata'))
        ],
        'open': [18000.0, 18010.0],
        'high': [18020.0, 18025.0],
        'low': [17990.0, 18005.0],
        'close': [18010.0, 18020.0],
        'volume': [1000.0, 2000.0]
    })

    mock_fetch = mocker.patch.object(dl, '_fetch_from_yfinance', return_value=mock_df)

    # First call - should fetch from yfinance and save to cache
    df1 = dl.get_candles('NIFTY 50', date(2023, 1, 2), date(2023, 1, 2))
    assert mock_fetch.call_count == 1
    assert len(df1) == 2

    # Second call - should load from cache, yfinance should NOT be called again for the same date range
    df2 = dl.get_candles('NIFTY 50', date(2023, 1, 2), date(2023, 1, 2))
    # Note: because of how we calculate missing ranges (from min/max date),
    # it might still attempt a fetch if we don't mock it to recognize it has the full range.
    # But since min_cached and max_cached exactly match the requested date in this mocked scenario,
    # it shouldn't call fetch again.

    # Wait, our logic:
    # min_cached = 2023-01-02, from_date = 2023-01-02 -> no gap at start
    # max_cached = 2023-01-02, to_date = 2023-01-02 -> no gap at end
    assert mock_fetch.call_count == 1
    assert len(df2) == 2

    pd.testing.assert_frame_equal(df1, df2)
