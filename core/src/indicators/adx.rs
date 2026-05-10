use super::Candle;

fn rma(series: &[f64], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; series.len()];
    let mut valid_idx = Vec::new();

    for i in 0..series.len() {
        if !series[i].is_nan() {
            valid_idx.push(i);
        }
    }

    if valid_idx.len() < period {
        return result;
    }

    let start_idx = valid_idx[period - 1];
    let mut sum = 0.0;
    for i in 0..period {
        sum += series[valid_idx[i]];
    }

    let mut prev_rma = sum / period as f64;
    result[start_idx] = prev_rma;

    let alpha = 1.0 / period as f64;
    for i in start_idx + 1..series.len() {
        if !series[i].is_nan() {
            prev_rma = (series[i] - prev_rma) * alpha + prev_rma;
            result[i] = prev_rma;
        } else {
            // Keep the previous value or just propagate? standard RMA over continuous valid data
            result[i] = prev_rma;
        }
    }

    result
}

pub fn adx(candles: &[Candle], period: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let len = candles.len();
    let adx_vals = vec![f64::NAN; len];
    let pdi_vals = vec![f64::NAN; len];
    let ndi_vals = vec![f64::NAN; len];

    if len < period * 2 || period == 0 {
        return (adx_vals, pdi_vals, ndi_vals);
    }

    let mut tr = vec![f64::NAN; len];
    let mut pdm = vec![f64::NAN; len];
    let mut ndm = vec![f64::NAN; len];

    for i in 1..len {
        let hl = candles[i].high - candles[i].low;
        let hc = (candles[i].high - candles[i-1].close).abs();
        let lc = (candles[i].low - candles[i-1].close).abs();
        tr[i] = hl.max(hc).max(lc);

        let up_move = candles[i].high - candles[i-1].high;
        let down_move = candles[i-1].low - candles[i].low;

        if up_move > down_move && up_move > 0.0 {
            pdm[i] = up_move;
        } else {
            pdm[i] = 0.0;
        }

        if down_move > up_move && down_move > 0.0 {
            ndm[i] = down_move;
        } else {
            ndm[i] = 0.0;
        }
    }

    let smoothed_tr = rma(&tr, period);
    let smoothed_pdm = rma(&pdm, period);
    let smoothed_ndm = rma(&ndm, period);

    let mut pdi = vec![f64::NAN; len];
    let mut ndi = vec![f64::NAN; len];
    let mut dx = vec![f64::NAN; len];

    for i in 0..len {
        if !smoothed_tr[i].is_nan() && smoothed_tr[i] != 0.0 {
            pdi[i] = 100.0 * smoothed_pdm[i] / smoothed_tr[i];
            ndi[i] = 100.0 * smoothed_ndm[i] / smoothed_tr[i];
            dx[i] = 100.0 * (pdi[i] - ndi[i]).abs() / (pdi[i] + ndi[i]);
        }
    }

    let adx = rma(&dx, period);

    (adx, pdi, ndi)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn get_test_candles() -> Vec<Candle> {
        let opens = vec![10.0, 10.5, 11.0, 10.8, 11.2, 11.5, 12.0, 11.8, 12.2, 12.5, 13.0, 12.8, 13.2, 13.5, 14.0, 13.8, 14.2, 14.5, 15.0, 14.8];
        let highs = vec![10.5, 11.0, 11.5, 11.2, 11.8, 12.0, 12.5, 12.2, 12.8, 13.0, 13.5, 13.2, 13.8, 14.0, 14.5, 14.2, 14.8, 15.0, 15.5, 15.2];
        let lows = vec![9.5, 10.0, 10.5, 10.2, 10.8, 11.0, 11.5, 11.2, 11.8, 12.0, 12.5, 12.2, 12.8, 13.0, 13.5, 13.2, 13.8, 14.0, 14.5, 14.2];
        let closes = vec![10.2, 10.8, 11.2, 11.0, 11.5, 11.8, 12.2, 12.0, 12.5, 12.8, 13.2, 13.0, 13.5, 13.8, 14.2, 14.0, 14.5, 14.8, 15.2, 15.0];
        let volumes = vec![100.0, 110.0, 120.0, 115.0, 125.0, 130.0, 135.0, 130.0, 140.0, 145.0, 150.0, 145.0, 155.0, 160.0, 165.0, 160.0, 170.0, 175.0, 180.0, 175.0];

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
    fn test_adx() {
        let candles = get_test_candles();
        let (adx_vals, pdi_vals, ndi_vals) = adx(&candles, 5);

        let expected_adx = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN,
            66.87509571080142, 68.68016504389713, 64.77342620658928, 64.44996233635622, 64.94993990588064,
            66.95907855733871, 63.162799743832025, 63.023305605183275, 63.69222454913499, 65.87690627977639, 62.19926588430625
        ];

        let expected_pdi = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, 36.000000000000014, 38.80000000000001, 31.040000000000013,
            36.832000000000036, 33.465600000000016, 36.772480000000016, 29.417984000000008, 35.53438720000003,
            32.427509760000014, 35.94200780800001, 28.75360624640001, 35.002884997120034, 32.002307997696015,
            35.60184639815681, 28.48147711852545
        ];

        let expected_ndi = vec![
            f64::NAN, f64::NAN, f64::NAN, f64::NAN, f64::NAN, 6.000000000000014, 4.800000000000011, 9.840000000000023,
            7.872000000000019, 6.297600000000016, 5.038080000000013, 10.030464000000025, 8.02437120000002,
            6.419496960000017, 5.135597568000013, 10.108478054400024, 8.08678244352002, 6.469425954816016,
            5.175540763852813, 10.140432611082264
        ];

        assert_eq!(adx_vals.len(), expected_adx.len());
        assert_eq!(pdi_vals.len(), expected_pdi.len());
        assert_eq!(ndi_vals.len(), expected_ndi.len());

        for i in 0..adx_vals.len() {
            if expected_adx[i].is_nan() {
                assert!(adx_vals[i].is_nan());
            } else {
                assert!((adx_vals[i] - expected_adx[i]).abs() < 1e-10);
            }

            if expected_pdi[i].is_nan() {
                assert!(pdi_vals[i].is_nan());
            } else {
                assert!((pdi_vals[i] - expected_pdi[i]).abs() < 1e-10);
            }

            if expected_ndi[i].is_nan() {
                assert!(ndi_vals[i].is_nan());
            } else {
                assert!((ndi_vals[i] - expected_ndi[i]).abs() < 1e-10);
            }
        }
    }
}
