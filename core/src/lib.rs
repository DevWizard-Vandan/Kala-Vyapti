use pyo3::prelude::*;
use pyo3::types::PyDict;

pub mod clustering;
pub mod indicators;

use clustering::supertrend_ai;
use indicators::{adx, atr, ema, macd, supertrend, Candle};

/// Python-facing OHLCV candle used by PyO3 indicator bindings.
#[pyclass]
#[derive(Clone)]
pub struct PyCandle {
    #[pyo3(get, set)]
    pub open: f64,
    #[pyo3(get, set)]
    pub high: f64,
    #[pyo3(get, set)]
    pub low: f64,
    #[pyo3(get, set)]
    pub close: f64,
    #[pyo3(get, set)]
    pub volume: f64,
}

#[pymethods]
impl PyCandle {
    /// Create a Python candle with open, high, low, close, and volume values.
    #[new]
    fn new(open: f64, high: f64, low: f64, close: f64, volume: f64) -> Self {
        Self {
            open,
            high,
            low,
            close,
            volume,
        }
    }
}

fn py_candles_to_candles(py_candles: Vec<PyCandle>) -> Vec<Candle> {
    py_candles
        .into_iter()
        .map(|candle| Candle {
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
            volume: candle.volume,
        })
        .collect()
}

/// Return a static greeting to verify the Python bindings are loaded.
#[pyfunction]
fn hello_world() -> &'static str {
    "Hello from Kala-Vyapti Rust core"
}

/// Calculate EMA values for Python-provided candles.
#[pyfunction]
fn py_ema(candles: Vec<PyCandle>, period: usize) -> Vec<f64> {
    let candles = py_candles_to_candles(candles);
    ema(&candles, period)
}

/// Calculate ATR values for Python-provided candles.
#[pyfunction]
fn py_atr(candles: Vec<PyCandle>, period: usize) -> Vec<f64> {
    let candles = py_candles_to_candles(candles);
    atr(&candles, period)
}

/// Calculate ADX, plus DI, and minus DI values for Python-provided candles.
#[pyfunction]
fn py_adx(candles: Vec<PyCandle>, period: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let candles = py_candles_to_candles(candles);
    adx(&candles, period)
}

/// Calculate MACD, signal, and histogram values for Python-provided candles.
#[pyfunction]
fn py_macd(
    candles: Vec<PyCandle>,
    fast: usize,
    slow: usize,
    signal_period: usize,
) -> (Vec<f64>, Vec<f64>, Vec<f64>) {
    let candles = py_candles_to_candles(candles);
    macd(&candles, fast, slow, signal_period)
}

/// Calculate SuperTrend direction and bands for Python-provided candles.
#[pyfunction]
fn py_supertrend(
    candles: Vec<PyCandle>,
    atr_period: usize,
    multiplier: f64,
) -> (Vec<i8>, Vec<f64>, Vec<f64>) {
    let candles = py_candles_to_candles(candles);
    supertrend(&candles, atr_period, multiplier)
}

/// Calculate SuperTrend AI factor selection and final bands for Python candles.
#[pyfunction]
fn py_supertrend_ai(
    py: Python<'_>,
    candles: Vec<PyCandle>,
    atr_period: usize,
    min_mult: f64,
    max_mult: f64,
    step: f64,
    perf_alpha: f64,
    from_cluster: usize,
) -> PyResult<PyObject> {
    let candles = py_candles_to_candles(candles);
    let result = supertrend_ai(
        &candles,
        atr_period,
        min_mult,
        max_mult,
        step,
        perf_alpha,
        from_cluster,
    );

    let dict = PyDict::new_bound(py);
    dict.set_item("trend", result.trend)?;
    dict.set_item("upper", result.upper)?;
    dict.set_item("lower", result.lower)?;
    dict.set_item("selected_factor", result.selected_factor)?;
    dict.set_item("cluster_perfs", result.cluster_perfs.to_vec())?;

    Ok(dict.into())
}

/// Python module for the Kala-Vyapti Rust signal engine.
#[pymodule]
fn kala_vyapti_core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyCandle>()?;
    m.add_function(wrap_pyfunction!(hello_world, m)?)?;
    m.add_function(wrap_pyfunction!(py_ema, m)?)?;
    m.add_function(wrap_pyfunction!(py_atr, m)?)?;
    m.add_function(wrap_pyfunction!(py_adx, m)?)?;
    m.add_function(wrap_pyfunction!(py_macd, m)?)?;
    m.add_function(wrap_pyfunction!(py_supertrend, m)?)?;
    m.add_function(wrap_pyfunction!(py_supertrend_ai, m)?)?;
    Ok(())
}
