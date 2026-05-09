use super::Candle;

/// Calculate SuperTrend direction and bands using Wilder-smoothed ATR.
///
/// Returns `(trend, upper_band, lower_band)` where trend is `1` for bullish,
/// `-1` for bearish, and `0` during the ATR warmup period.
pub fn supertrend(
    candles: &[Candle],
    atr_period: usize,
    multiplier: f64,
) -> (Vec<i8>, Vec<f64>, Vec<f64>) {
    let len = candles.len();
    let mut trend = vec![0; len];
    let mut upper_band = vec![f64::NAN; len];
    let mut lower_band = vec![f64::NAN; len];

    if len == 0 || atr_period == 0 || len < atr_period {
        return (trend, upper_band, lower_band);
    }

    let atr = wilder_atr(candles, atr_period);
    let first_valid = atr_period - 1;

    for i in first_valid..len {
        let hl2 = (candles[i].high + candles[i].low) / 2.0;
        let basic_upper = hl2 + multiplier * atr[i];
        let basic_lower = hl2 - multiplier * atr[i];

        if i == first_valid {
            upper_band[i] = basic_upper;
            lower_band[i] = basic_lower;
            trend[i] = 1;
            continue;
        }

        upper_band[i] = if candles[i - 1].close <= upper_band[i - 1] {
            basic_upper.min(upper_band[i - 1])
        } else {
            basic_upper
        };

        lower_band[i] = if candles[i - 1].close >= lower_band[i - 1] {
            basic_lower.max(lower_band[i - 1])
        } else {
            basic_lower
        };

        trend[i] = if candles[i].close > upper_band[i - 1] {
            1
        } else if candles[i].close < lower_band[i - 1] {
            -1
        } else {
            trend[i - 1]
        };
    }

    (trend, upper_band, lower_band)
}

fn wilder_atr(candles: &[Candle], period: usize) -> Vec<f64> {
    let len = candles.len();
    let mut true_ranges = vec![0.0; len];
    let mut atr = vec![f64::NAN; len];

    for i in 0..len {
        true_ranges[i] = if i == 0 {
            candles[i].high - candles[i].low
        } else {
            let high_low = candles[i].high - candles[i].low;
            let high_prev_close = (candles[i].high - candles[i - 1].close).abs();
            let low_prev_close = (candles[i].low - candles[i - 1].close).abs();
            high_low.max(high_prev_close).max(low_prev_close)
        };
    }

    let initial_sum: f64 = true_ranges.iter().take(period).sum();
    atr[period - 1] = initial_sum / period as f64;

    for i in period..len {
        atr[i] = ((period as f64 - 1.0) * atr[i - 1] + true_ranges[i]) / period as f64;
    }

    atr
}

#[cfg(test)]
mod tests {
    use super::*;

    fn sample_candles() -> Vec<Candle> {
        vec![
            Candle {
                open: 100.0,
                high: 101.0,
                low: 99.0,
                close: 100.0,
                volume: 1000.0,
            },
            Candle {
                open: 100.0,
                high: 102.0,
                low: 100.0,
                close: 101.0,
                volume: 1100.0,
            },
            Candle {
                open: 101.0,
                high: 103.0,
                low: 101.0,
                close: 102.0,
                volume: 1200.0,
            },
            Candle {
                open: 102.0,
                high: 104.0,
                low: 102.0,
                close: 103.0,
                volume: 1300.0,
            },
            Candle {
                open: 103.0,
                high: 105.0,
                low: 103.0,
                close: 104.0,
                volume: 1400.0,
            },
            Candle {
                open: 104.0,
                high: 106.0,
                low: 104.0,
                close: 105.0,
                volume: 1500.0,
            },
            Candle {
                open: 105.0,
                high: 107.0,
                low: 105.0,
                close: 106.0,
                volume: 1600.0,
            },
            Candle {
                open: 106.0,
                high: 108.0,
                low: 106.0,
                close: 107.0,
                volume: 1700.0,
            },
            Candle {
                open: 107.0,
                high: 109.0,
                low: 107.0,
                close: 108.0,
                volume: 1800.0,
            },
            Candle {
                open: 108.0,
                high: 110.0,
                low: 108.0,
                close: 109.0,
                volume: 1900.0,
            },
            Candle {
                open: 109.0,
                high: 111.0,
                low: 109.0,
                close: 110.0,
                volume: 2000.0,
            },
            Candle {
                open: 110.0,
                high: 112.0,
                low: 110.0,
                close: 111.0,
                volume: 2100.0,
            },
            Candle {
                open: 111.0,
                high: 113.0,
                low: 111.0,
                close: 112.0,
                volume: 2200.0,
            },
            Candle {
                open: 112.0,
                high: 114.0,
                low: 112.0,
                close: 113.0,
                volume: 2300.0,
            },
            Candle {
                open: 113.0,
                high: 115.0,
                low: 113.0,
                close: 114.0,
                volume: 2400.0,
            },
            Candle {
                open: 114.0,
                high: 116.0,
                low: 114.0,
                close: 115.0,
                volume: 2500.0,
            },
            Candle {
                open: 115.0,
                high: 117.0,
                low: 115.0,
                close: 116.0,
                volume: 2600.0,
            },
            Candle {
                open: 116.0,
                high: 118.0,
                low: 116.0,
                close: 117.0,
                volume: 2700.0,
            },
            Candle {
                open: 117.0,
                high: 119.0,
                low: 117.0,
                close: 118.0,
                volume: 2800.0,
            },
            Candle {
                open: 118.0,
                high: 120.0,
                low: 118.0,
                close: 119.0,
                volume: 2900.0,
            },
            Candle {
                open: 119.0,
                high: 121.0,
                low: 119.0,
                close: 120.0,
                volume: 3000.0,
            },
            Candle {
                open: 120.0,
                high: 122.0,
                low: 120.0,
                close: 121.0,
                volume: 3100.0,
            },
            Candle {
                open: 121.0,
                high: 123.0,
                low: 121.0,
                close: 122.0,
                volume: 3200.0,
            },
            Candle {
                open: 122.0,
                high: 124.0,
                low: 122.0,
                close: 123.0,
                volume: 3300.0,
            },
            Candle {
                open: 123.0,
                high: 125.0,
                low: 123.0,
                close: 124.0,
                volume: 3400.0,
            },
            Candle {
                open: 124.0,
                high: 126.0,
                low: 124.0,
                close: 125.0,
                volume: 3500.0,
            },
            Candle {
                open: 125.0,
                high: 126.0,
                low: 110.0,
                close: 111.0,
                volume: 3600.0,
            },
            Candle {
                open: 111.0,
                high: 112.0,
                low: 100.0,
                close: 101.0,
                volume: 3700.0,
            },
            Candle {
                open: 101.0,
                high: 110.0,
                low: 100.0,
                close: 109.0,
                volume: 3800.0,
            },
            Candle {
                open: 109.0,
                high: 126.0,
                low: 108.0,
                close: 125.0,
                volume: 3900.0,
            },
        ]
    }

    fn assert_close(actual: f64, expected: f64) {
        assert!(
            (actual - expected).abs() < 1e-6,
            "expected {expected}, got {actual}"
        );
    }

    #[test]
    fn calculates_supertrend_with_wilder_atr() {
        let candles = sample_candles();
        let (trend, upper, lower) = supertrend(&candles, 3, 2.0);

        assert_eq!(trend.len(), 30);
        assert_eq!(upper.len(), 30);
        assert_eq!(lower.len(), 30);

        assert_eq!(trend[0], 0);
        assert_eq!(trend[1], 0);
        assert!(upper[0].is_nan());
        assert!(upper[1].is_nan());
        assert!(lower[0].is_nan());
        assert!(lower[1].is_nan());

        assert_close(upper[2], 106.0);
        assert_close(lower[2], 98.0);
        assert_close(upper[6], 106.0);
        assert_close(lower[6], 102.0);
        assert_close(upper[26], 131.33333333333334);
        assert_close(lower[26], 121.0);
        assert_close(upper[29], 122.88888888888889);
        assert_close(lower[29], 93.04938271604938);

        assert_eq!(trend[2], 1);
        assert_eq!(trend[7], 1);
        assert_eq!(trend[27], -1);
        assert_eq!(trend[29], 1);
    }

    #[test]
    fn returns_empty_vectors_for_empty_input() {
        let (trend, upper, lower) = supertrend(&[], 10, 3.0);

        assert!(trend.is_empty());
        assert!(upper.is_empty());
        assert!(lower.is_empty());
    }

    #[test]
    fn returns_warmup_only_when_period_exceeds_input() {
        let candles = sample_candles();
        let (trend, upper, lower) = supertrend(&candles[..2], 3, 2.0);

        assert_eq!(trend, vec![0, 0]);
        assert!(upper.iter().all(|value| value.is_nan()));
        assert!(lower.iter().all(|value| value.is_nan()));
    }
}
