use super::Candle;

pub fn atr(candles: &[Candle], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; candles.len()];

    if candles.len() < period || period == 0 || candles.is_empty() {
        return result;
    }

    let mut trs = vec![0.0; candles.len()];

    // First True Range is just high - low
    trs[0] = candles[0].high - candles[0].low;

    for i in 1..candles.len() {
        let hl = candles[i].high - candles[i].low;
        let hc = (candles[i].high - candles[i - 1].close).abs();
        let lc = (candles[i].low - candles[i - 1].close).abs();

        trs[i] = hl.max(hc).max(lc);
    }

    let mut sum = 0.0;
    for i in 0..period {
        sum += trs[i];
    }

    let mut prev_atr = sum / period as f64;
    result[period - 1] = prev_atr;

    for i in period..candles.len() {
        prev_atr = ((period as f64 - 1.0) * prev_atr + trs[i]) / period as f64;
        result[i] = prev_atr;
    }

    result
}

#[cfg(test)]
mod tests {
    use super::*;

    fn get_test_candles() -> Vec<Candle> {
        let opens = vec![
            10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0, 11.8, 12.2, 12.5, 13.0, 12.8, 13.2, 13.5,
            14.0, 13.8, 14.2, 14.5, 15.0, 14.8,
        ];
        let highs = vec![
            10.5, 11.0, 11.5, 11.2, 11.8, 12.4, 12.5, 12.2, 12.8, 13.0, 13.5, 13.2, 13.8, 14.0,
            14.5, 14.2, 14.8, 15.0, 15.5, 15.2,
        ];
        let lows = vec![
            9.5, 10.0, 10.5, 10.2, 10.8, 11.0, 11.5, 11.2, 11.8, 12.0, 12.5, 12.2, 12.8, 13.0,
            13.5, 13.2, 13.8, 14.0, 14.5, 14.2,
        ];
        let closes = vec![
            10.2, 10.8, 11.2, 11.0, 11.5, 11.8, 12.2, 12.0, 12.5, 12.8, 13.2, 13.0, 13.5, 13.8,
            14.2, 14.0, 14.5, 14.8, 15.2, 15.0,
        ];
        let volumes = vec![
            100.0, 110.0, 120.0, 115.0, 125.0, 130.0, 135.0, 130.0, 140.0, 145.0, 150.0, 145.0,
            155.0, 160.0, 165.0, 160.0, 170.0, 175.0, 180.0, 175.0,
        ];

        let mut candles = Vec::new();
        for i in 0..20 {
            candles.push(Candle {
                open: opens[i],
                high: highs[i],
                low: lows[i],
                close: closes[i],
                volume: volumes[i],
            });
        }
        candles
    }

    #[test]
    fn test_atr() {
        let candles = get_test_candles();
        let atr_vals = atr(&candles, 5);

        let expected = vec![
            f64::NAN,
            f64::NAN,
            f64::NAN,
            f64::NAN,
            1.0,
            1.08,
            1.064,
            1.0512,
            1.04096,
            1.032768,
            1.0262144,
            1.02097152,
            1.016777216,
            1.0134217728,
            1.01073741824,
            1.008589934592,
            1.0068719476736,
            1.0054975581388801,
            1.004398046511104,
            1.0035184372088832,
        ];

        assert_eq!(atr_vals.len(), expected.len());
        for i in 0..atr_vals.len() {
            if atr_vals[i].is_nan() {
                assert!(expected[i].is_nan());
            } else {
                assert!((atr_vals[i] - expected[i]).abs() < 1e-10);
            }
        }
    }
}
