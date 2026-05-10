use super::Candle;
use super::ema::ema;

fn calc_ema_from_slice(series: &[f64], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; series.len()];
    let mut valid_idx = Vec::new();

    for i in 0..series.len() {
        if !series[i].is_nan() {
            valid_idx.push(i);
        }
    }

    if valid_idx.len() < period || period == 0 {
        return result;
    }

    let start_idx = valid_idx[period - 1];
    let mut sum = 0.0;
    for i in 0..period {
        sum += series[valid_idx[i]];
    }

    let mut prev_ema = sum / period as f64;
    result[start_idx] = prev_ema;

    let multiplier = 2.0 / (period as f64 + 1.0);
    for i in start_idx + 1..series.len() {
        if !series[i].is_nan() {
            prev_ema = (series[i] - prev_ema) * multiplier + prev_ema;
            result[i] = prev_ema;
        } else {
            result[i] = prev_ema;
        }
    }

    result
}

pub fn macd(candles: &[Candle], fast: usize, slow: usize, signal: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let fast_ema = ema(candles, fast);
    let slow_ema = ema(candles, slow);

    let mut macd_line = vec![f64::NAN; candles.len()];
    for i in 0..candles.len() {
        if !fast_ema[i].is_nan() && !slow_ema[i].is_nan() {
            macd_line[i] = fast_ema[i] - slow_ema[i];
        }
    }

    let signal_line = calc_ema_from_slice(&macd_line, signal);

    let mut histogram = vec![f64::NAN; candles.len()];
    for i in 0..candles.len() {
        if !macd_line[i].is_nan() && !signal_line[i].is_nan() {
            histogram[i] = macd_line[i] - signal_line[i];
        }
    }

    (macd_line, signal_line, histogram)
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
    fn test_macd() {
        let candles = get_test_candles();
        let (macd_line, signal_line, histogram) = macd(&candles, 5, 10, 3);

        let expected_macd = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN,
            0.6447736625514402, 0.672273350791869, 0.6162263109962325, 0.6240657249867194, 0.6359741492853672,
            0.66453182621885, 0.6095310544723347, 0.61834693324864, 0.6311345681418583, 0.6604651224386515, 0.6061323870588033
        ];

        let expected_signal = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN,
            0.6444244414465139, 0.6342450832166167, 0.6351096162509919, 0.649820721234921, 0.6296758878536278,
            0.6240114105511338, 0.6275729893464961, 0.6440190558925738, 0.6250757214756886
        ];

        let expected_hist = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN,
            -0.02819813045028141, -0.01017935822989724, 0.0008645330343752811, 0.014711104983929024, -0.020144833381293137,
            -0.005664477302493864, 0.00356157879536223, 0.01644606654607772, -0.018943334416885227
        ];

        assert_eq!(macd_line.len(), expected_macd.len());
        assert_eq!(signal_line.len(), expected_signal.len());
        assert_eq!(histogram.len(), expected_hist.len());

        for i in 0..macd_line.len() {
            if expected_macd[i].is_nan() {
                assert!(macd_line[i].is_nan());
            } else {
                assert!((macd_line[i] - expected_macd[i]).abs() < 1e-10);
            }

            if expected_signal[i].is_nan() {
                assert!(signal_line[i].is_nan());
            } else {
                assert!((signal_line[i] - expected_signal[i]).abs() < 1e-10);
            }

            if expected_hist[i].is_nan() {
                assert!(histogram[i].is_nan());
            } else {
                assert!((histogram[i] - expected_hist[i]).abs() < 1e-10);
            }
        }
    }
}
