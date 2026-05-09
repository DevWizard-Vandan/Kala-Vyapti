//! Technical indicator implementations for the signal engine.

pub mod supertrend;

pub use supertrend::supertrend;

/// One OHLCV candle used by all technical indicators.
#[derive(Debug, Clone, Copy, PartialEq)]
pub struct Candle {
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}
