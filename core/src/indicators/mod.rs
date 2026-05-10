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
pub mod ema;
pub use ema::ema;
pub mod atr;
pub use atr::atr;
pub mod adx;
pub use adx::adx;
pub mod macd;
pub use macd::macd;
