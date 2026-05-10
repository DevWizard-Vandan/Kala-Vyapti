use super::Candle;

pub fn ema(candles: &[Candle], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; candles.len()];

    if candles.len() < period || period == 0 {
        return result;
    }

    let multiplier = 2.0 / (period as f64 + 1.0);
    let mut sum = 0.0;

    // Calculate SMA for the first valid value
    for i in 0..period {
        sum += candles[i].close;
    }

    let mut prev_ema = sum / period as f64;
    result[period - 1] = prev_ema;

    // Calculate EMA for the remaining values
    for i in period..candles.len() {
        prev_ema = (candles[i].close - prev_ema) * multiplier + prev_ema;
        result[i] = prev_ema;
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn get_test_candles() -> Vec<Candle> {
        let closes = vec![
            10.2, 10.8, 11.2, 11.0, 11.5, 11.8, 12.2, 12.0, 12.5, 12.8,
            13.2, 13.0, 13.5, 13.8, 14.2, 14.0, 14.5, 14.8, 15.2, 15.0
        ];

        closes.into_iter().map(|close| Candle {
            open: 0.0,
            high: 0.0,
            low: 0.0,
            close,
            volume: 0.0,
        }).collect()
    }

    #[test]
    fn test_ema() {
        let candles = get_test_candles();
        let ema_vals = ema(&candles, 5);

        let expected = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, 10.94,
            11.226666666666668, 11.551111111111112, 11.700740740740741, 11.967160493827162, 12.244773662551442,
            12.563182441700963, 12.708788294467311, 12.972525529644875, 13.248350353096583, 13.56556690206439,
            13.710377934709594, 13.973585289806397, 14.249056859870933, 14.566037906580624, 14.710691937720417
        ];

        assert_eq!(ema_vals.len(), expected.len());
        for i in 0..ema_vals.len() {
            if ema_vals[i].is_nan() {
                assert!(expected[i].is_nan());
            } else {
                assert!((ema_vals[i] - expected[i]).abs() < 1e-10);
            }
        }
    }
}
