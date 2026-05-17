# status.md — Project Status Tracker
> Update this file every time a task is completed or a new task begins.
> All AI agents should read this before starting work.

---

## Current Status

**Phase:** 1 — Backtester + Signal Engine
**Week:** 1 of 3
**Overall progress:** ~33% — Rust signal core and Python SignalEngine implemented
**Last updated:** Premium proxy sizing fixed. Daily backtest results: Total trades 7, Win rate 42.9%, Total PnL Rs.-99, Avg win Rs.246, Avg loss Rs.-209, Max drawdown 0.1%, Sharpe ratio -0.73

---

## Phases Overview

| Phase | Name | Duration | Status |
|---|---|---|---|
| 1 | Backtester + Signal Engine | 3 weeks | 🔄 In Progress |
| 2 | Paper Trading + Journal | 4 weeks | 🔄 In Progress |
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
| 1.1 | Initialize repo structure (folders, .gitignore, README) | You | ✅ Done | Repo: github.com/DevWizard-Vandan/Kala-Vyapti |
| 1.2 | Set up Rust crate `core/` with maturin + PyO3 | Claude Code | ✅ Done | PyO3 0.22, cdylib+rlib, hello_world() binding verified |
| 1.3 | Implement `EMA(period)` in Rust | Jules | ✅ Done | Fixed ATR/ADX from Jules PR |
| 1.4 | Implement `ATR(period)` in Rust | Jules | ✅ Done | Fixed ATR/ADX from Jules PR |
| 1.5 | Implement `ADX + DMI(+/-)(period=14)` in Rust | Jules | ✅ Done | Fixed ATR/ADX from Jules PR |
| 1.6 | Implement `MACD(12,26,9)` + histogram in Rust | Jules | ✅ Done | Fixed ATR/ADX from Jules PR |
| 1.7 | Implement basic `SuperTrend(atr, mult)` in Rust | Claude Code | ✅ Done | Wilder ATR bands + trend flips, tests passing |
| 1.8 | Expose all indicators via PyO3 Python bindings | Claude Code | ✅ Done | PyCandle + py_* wrappers verified with maturin develop |
| 1.9 | Python validation tests vs TA-Lib reference | You + Copilot | ⬜ Todo | Must match to 4 decimal places |

### Week 2 — SuperTrend AI (K-Means Clustering)

#### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 2.1 | Implement basic SuperTrend bands in Rust | Claude Code | ✅ Done | Basic SuperTrend available for AI factor selection |
| 2.2 | Port Pine Script k-means clustering to Rust | Claude Code | ✅ Done | SuperTrend AI factor clustering + PyO3 wrapper |
| 2.3 | Implement performance tracking per factor | Claude Code | ✅ Done | Python SignalEngine evaluates strategy conditions |
| 2.4 | Return best-cluster factor + bullish/bearish state | Claude Code | ✅ Done | Signal dataclass + bullish state surfaced in engine |
| 2.5 | Python `SignalEngine` class wrapping all Rust indicators | You + Copilot | ⬜ Todo | |
| 2.6 | Define Signal dataclass (see agents.md schema) | You + Copilot | ⬜ Todo | |

---

### Week 3 — Backtesting Framework

#### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 3.1 | NSE historical data downloader (15-min OHLCV) | Jules | ✅ Done | Parquet storage |
| 3.2 | `DataLoader` class with get_candles() API | Jules | ✅ Done | |
| 3.3 | Backtesting engine core loop | Claude Code | ✅ Done | |
| 3.4 | Position sizing + brokerage simulation | Claude Code | ✅ Done | ₹20/order Zerodha |
| 3.5 | Performance report generator | Copilot | ✅ Done | |
| 3.6 | Run backtest on 2yr Nifty 15-min data | You | ⬜ Todo | |
| 3.7 | Analyze results + tune parameters if needed | You + Claude Code | ⬜ Todo | |

## Completed Tasks

| Task | Date | Notes |
|---|---|---|
| 1.1 | Phase start | Repo initialized at github.com/DevWizard-Vandan/Kala-Vyapti |
| 1.2 | Phase start | Rust crate with PyO3 0.22 + maturin. Crate: `kala-vyapti-core`, module: `kala_vyapti_core` |
| 1.3–1.6 | 2026-05-10 | Fixed ATR/ADX from Jules PR |
| 1.7 | 2026-05-09 | Basic SuperTrend implemented in Rust with hardcoded 30-candle unit test |
| 1.8 | 2026-05-10 | Exposed all indicators via PyO3 Python bindings and verified with maturin develop |
| 2.1–2.2 | 2026-05-10 | SuperTrend AI k-means clustering implemented in Rust with PyO3 wrapper |
| 2.3–2.4 | 2026-05-10 | Python SignalEngine and Signal dataclass implemented with pytest coverage |
| PR #2 fixes | 2026-05-11 | PR #2 fixes applied - backtesting framework corrected |
| DataLoader source update | 2026-05-17 | DataLoader updated: Kite API for 15m, yfinance daily as fallback |
| Timeframe-aware thresholds | 2026-05-17 | Timeframe-aware thresholds added. Daily backtest results: Total trades 0, Win rate 0.0%, Total PnL Rs.0, Avg win Rs.0, Avg loss Rs.0, Max drawdown 0.0%, Sharpe ratio 0.00 |
| Backtest warmup loop fix | 2026-05-17 | Backtest loop now starts at i=301 and evaluates candles through bar i-1 before executing at bar i open. Verification: Total trades 0, Win rate 0.0%, Total PnL Rs.0, Avg win Rs.0, Avg loss Rs.0, Max drawdown 0.0%, Sharpe ratio 0.00. SignalEngine emits BUY signals, but daily Nifty spot proxy entries size to 0 under the 2% capital cap. |
| Premium proxy sizing fix | 2026-05-17 | Premium proxy sizing fixed. Daily backtest results: Total trades 7, Win rate 42.9%, Total PnL Rs.-99, Avg win Rs.246, Avg loss Rs.-209, Max drawdown 0.1%, Sharpe ratio -0.73. Trades: 2023-05-05 -> 2023-05-18 Rs.53 SIGNAL; 2023-05-30 -> 2023-06-05 Rs.-37 SIGNAL; 2023-06-08 -> 2023-06-12 Rs.-110 SIGNAL; 2023-07-03 -> 2023-07-26 Rs.213 SIGNAL; 2023-09-15 -> 2023-09-22 Rs.-244 SIGNAL; 2023-12-04 -> 2024-01-03 Rs.472 SIGNAL; 2024-09-27 -> 2024-10-04 Rs.-446 SIGNAL. |

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

## Completed Tasks

| Task | Date | Notes |
|---|---|---|
| Phase 2 tasks started | 2026-05-18 | Built Kite WebSocket feed (`engine/data/kite_feed.py`), `CandleBuilder` (`engine/data/candle_builder.py`), `Trade` dataclass (`engine/execution/models.py`), and `PaperTrader` (`engine/execution/paper_trader.py`). Stubbed `RiskGate` (`engine/risk/risk_gate.py`). Tests run and passing. |

## Next Action

Run Python validation tests against a TA-Lib reference for task 1.9.
