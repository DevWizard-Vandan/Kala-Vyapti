# status.md — Project Status Tracker
> Update this file every time a task is completed or a new task begins.
> All AI agents should read this before starting work.

---

## Current Status

**Phase:** 1 — Backtester + Signal Engine
**Week:** 1 of 3
**Overall progress:** 0% — Project initialized, no code written yet
**Last updated:** Project start

---

## Phases Overview

| Phase | Name | Duration | Status |
|---|---|---|---|
| 1 | Backtester + Signal Engine | 3 weeks | 🔄 In Progress |
| 2 | Paper Trading + Journal | 4 weeks | ⏳ Not Started |
| 3 | AI Brain + Risk Gate | 4 weeks | ⏳ Not Started |
| 4 | Live Execution (1 lot) | Ongoing | ⏳ Not Started |

---

## Phase 1 — Backtester + Signal Engine

### Goal
Validate the trading strategy on historical data before touching real markets.
Output: backtest report showing win rate, avg RR, max drawdown, Sharpe ratio on 2 years of Nifty 15-min data.

---

### Week 1 — Rust Signal Engine Core

#### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 1.1 | Initialize repo structure (folders, .gitignore, README) | You | ⬜ Todo | |
| 1.2 | Set up Rust crate `core/` with maturin + PyO3 | Claude Code | ✅ Done | Created Cargo library crate, PyO3 hello_world binding, maturin pyproject, and Python requirements. |
| 1.3 | Implement `EMA(period)` in Rust | Jules | ⬜ Todo | Delegate to Jules |
| 1.4 | Implement `ATR(period)` in Rust | Jules | ⬜ Todo | Delegate to Jules |
| 1.5 | Implement `ADX + DMI(+/-)(period=14)` in Rust | Jules | ⬜ Todo | Delegate to Jules |
| 1.6 | Implement `MACD(12,26,9)` + histogram in Rust | Jules | ⬜ Todo | Delegate to Jules |
| 1.7 | Implement basic `SuperTrend(atr, mult)` in Rust | Claude Code | ⬜ Todo | Required before k-means |
| 1.8 | Expose all indicators via PyO3 Python bindings | Claude Code | ⬜ Todo | After 1.3–1.7 done |
| 1.9 | Python validation tests vs TA-Lib reference | You + Copilot | ⬜ Todo | Must match to 4 decimal places |

#### Jules Delegation Prompt (Tasks 1.3–1.6)
```
Context: Building a Rust signal engine for an algorithmic trading system.
Repo path: core/src/indicators/

Implement the following technical indicators in Rust.
Each function takes OHLCV data as input and returns Vec<f64> of equal length (NaN-padded at start).

Input struct:
pub struct Candle {
    pub open: f64,
    pub high: f64,
    pub low: f64,
    pub close: f64,
    pub volume: f64,
}

Implement:
1. pub fn ema(candles: &[Candle], period: usize) -> Vec<f64>
2. pub fn atr(candles: &[Candle], period: usize) -> Vec<f64>  
3. pub fn adx(candles: &[Candle], period: usize) -> (Vec<f64>, Vec<f64>, Vec<f64>)
   // returns (adx, plus_di, minus_di)
4. pub fn macd(candles: &[Candle], fast: usize, slow: usize, signal: usize) 
   -> (Vec<f64>, Vec<f64>, Vec<f64>)
   // returns (macd_line, signal_line, histogram)

Requirements:
- Use Wilder's smoothing for ATR and ADX (not simple EMA)
- No external crates for the math — implement from scratch
- Each file: indicators/ema.rs, indicators/atr.rs, indicators/adx.rs, indicators/macd.rs
- Include unit tests in each file with hardcoded 20-candle input and expected output
```

---

### Week 2 — SuperTrend AI (K-Means Clustering)

#### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 2.1 | Implement basic SuperTrend bands in Rust | Claude Code | ⬜ Todo | |
| 2.2 | Port Pine Script k-means clustering to Rust | Claude Code | ⬜ Todo | Hardest task in Phase 1 |
| 2.3 | Implement performance tracking per factor | Claude Code | ⬜ Todo | |
| 2.4 | Return best-cluster factor + bullish/bearish state | Claude Code | ⬜ Todo | |
| 2.5 | Python `SignalEngine` class wrapping all Rust indicators | You + Copilot | ⬜ Todo | |
| 2.6 | Define Signal dataclass (see agents.md schema) | You + Copilot | ⬜ Todo | |

---

### Week 3 — Backtesting Framework

#### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 3.1 | NSE historical data downloader (15-min OHLCV) | Jules | ⬜ Todo | Parquet storage |
| 3.2 | `DataLoader` class with get_candles() API | Jules | ⬜ Todo | |
| 3.3 | Backtesting engine core loop | Claude Code | ⬜ Todo | |
| 3.4 | Position sizing + brokerage simulation | Claude Code | ⬜ Todo | ₹20/order Zerodha |
| 3.5 | Performance report generator | Copilot | ⬜ Todo | |
| 3.6 | Run backtest on 2yr Nifty 15-min data | You | ⬜ Todo | |
| 3.7 | Analyze results + tune parameters if needed | You + Claude Code | ⬜ Todo | |

#### Jules Delegation Prompt (Tasks 3.1–3.2)
```
Build a Python data pipeline:

1. Download Nifty 50 historical OHLCV data at 15-minute intervals
   - Date range: 2022-01-01 to present
   - Primary source: NSE website / nsepy library
   - Fallback: yfinance (symbol "^NSEI")
   - Store as Parquet files partitioned by year/month under data/historical/

2. DataLoader class (data/data_loader.py):
   class DataLoader:
       def get_candles(
           self, 
           symbol: str,          # e.g. "NIFTY 50"
           from_date: date,
           to_date: date,
           timeframe: str        # "15m", "1h", "1d"
       ) -> pd.DataFrame:        # columns: timestamp, open, high, low, close, volume
           ...

Requirements:
- Type hints everywhere
- Cache downloaded data locally, only fetch missing date ranges
- Logging with Python logging module (not print)
- Handle NSE holidays gracefully (skip, don't error)
```

---

## Completed Tasks

- 2026-05-09: Task 1.2 done — scaffolded `core/` Rust library crate with PyO3/maturin, placeholder module folders, `hello_world()` binding, root `pyproject.toml`, and `requirements.txt`.

---

## Blockers

_None currently._

---

## Decisions Log

| Date | Decision | Reason |
|---|---|---|
| Start | Rust core + Python orchestration | Kite SDK is Python; Rust for performance-critical indicator math |
| Start | Zerodha Kite API only | Owner's existing broker |
| Start | Paper mode default, LIVE_MODE=true required | Safety — no accidental live trades |
| Start | No RiskGate override method | Emotional overrides are the #1 loss cause |
| Start | Max 1 open position | Simplicity + risk control during initial phase |

---

## How to Update This File

When you complete a task, change `⬜ Todo` → `✅ Done` and add a note.
When you start a task, change to `🔄 In Progress`.
When blocked, change to `🚫 Blocked` and add to the Blockers section.
Add completed tasks to the Completed Tasks section with date.

---

## Next Action (Right Now)

**You:** Create the repo folder structure on your machine.
**Then:** Paste task 1.2 prompt to Claude Code to scaffold the Rust crate.
**Simultaneously:** Paste the Jules delegation prompt (Week 1) to Jules.

```bash
# Run this to create the folder structure
mkdir -p Kala-Vyapti/{core/src/{indicators,clustering},engine/{data,signals,brain,risk,execution,journal},backtest/reports,dashboard,alerts,infra}
cd Kala-Vyapti
git init
```
