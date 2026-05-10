use super::Candle;

fn rma(series: &[f64], period: usize) -> Vec<f64> {
    let mut result = vec![f64::NAN; series.len()];

    if series.len() < period || period == 0 {
        return result;
    }

    let mut sum = 0.0;
    for i in 0..period {
        sum += series[i];
    }

    let mut prev_rma = sum / period as f64;
    result[period - 1] = prev_rma;

    for i in period..series.len() {
        prev_rma = ((period as f64 - 1.0) * prev_rma + series[i]) / period as f64;
        result[i] = prev_rma;
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

    let mut tr = vec![0.0; len];
    let mut pdm = vec![0.0; len];
    let mut ndm = vec![0.0; len];

    tr[0] = candles[0].high - candles[0].low;

    for i in 1..len {
        let hl = candles[i].high - candles[i].low;
        let hc = (candles[i].high - candles[i - 1].close).abs();
        let lc = (candles[i].low - candles[i - 1].close).abs();
        tr[i] = hl.max(hc).max(lc);

        let up_move = candles[i].high - candles[i - 1].high;
        let down_move = candles[i - 1].low - candles[i].low;

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
            dx[i] = if (pdi[i] + ndi[i]) > 0.0 {
                100.0 * (pdi[i] - ndi[i]).abs() / (pdi[i] + ndi[i])
            } else {
                0.0
            };
        } else {
            dx[i] = 0.0;
        }
    }

    let adx = rma(&dx, period);

    (adx, pdi, ndi)
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
            10.5, 11.0, 11.5, 11.2, 11.8, 12.0, 12.5, 12.2, 12.8, 13.0, 13.5, 13.2, 13.8, 14.0,
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
    fn test_adx() {
        let candles = get_test_candles();
        let (adx_vals, pdi_vals, ndi_vals) = adx(&candles, 5);

        let expected_adx = vec![
            f64::NAN,
            f64::NAN,
            f64::NAN,
            f64::NAN,
            13.68421052631578,
            25.365973072215404,
            36.19896182664225,
            38.883647471087215,
            43.99385540826383,
            48.85834001061203,
            54.36150281297805,
            53.11345325729842,
            55.08199125436853,
            57.445577482668725,
            60.98907260308545,
            58.29909763628383,
            59.114019719360215,
            60.559144663205686,
            63.38326800274028,
            60.16780735200956,
        ];

        let expected_pdi = vec![
            f64::NAN,
            f64::NAN,
            f64::NAN,
            f64::NAN,
            32.00000000000003,
            29.60000000000001,
            33.68000000000001,
            26.944000000000006,
            33.555200000000035,
            30.844160000000016,
            34.67532800000001,
            27.74026240000001,
            34.19220992000004,
            31.353767936000015,
            35.08301434880001,
            28.06641147904001,
            34.453129183232036,
            31.562503346585615,
            35.25000267726849,
            28.20000214181479,
        ];

        let expected_ndi = vec![
            f64::NAN,
            f64::NAN,
            f64::NAN,
            f64::NAN,
            6.000000000000014,
            4.800000000000011,
            3.8400000000000087,
            9.072000000000022,
            7.257600000000017,
            5.806080000000014,
            4.644864000000011,
            9.715891200000023,
            7.772712960000019,
            6.218170368000016,
            4.974536294400013,
            9.979629035520023,
            7.98370322841602,
            6.386962582732816,
            5.109570066186253,
            10.087656052949017,
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
