# agents.md — Master Context File
> Read this file completely before writing any code or making any decisions.
> Last updated: see status.md

---

## Project Overview

**Name:** Kala-Vyapti — Automated Options Trading System
**Goal:** A fully automated, rule-based algorithmic trading system for Indian markets (NSE/MCX) that eliminates emotional decision-making and executes a predefined strategy with zero discretion.

**Owner:** Vandan (B.Tech AI/ML, VIT Pune)
**Broker:** Zerodha (live) — Kite Connect API
**Markets:** Nifty/BankNifty index options (primary), Crude Oil / Gold MCX options (secondary)
**Exchange timezone:** IST (UTC+5:30), market hours 09:15–15:30

---

## Why This System Exists (Critical Context)

The owner has experienced significant losses primarily due to:
- Holding losing positions to near-zero (2 trades caused ₹1.75L loss alone)
- CE bias on stock options (stock CE trades: –₹2.41L in one period)
- High win rate (68%) destroyed by 3.3× avg loss vs avg win
- Emotional overrides of exit rules

**The system must make emotional overrides physically impossible, not just discouraged.**

---

## Hard Rules (Enforce in Code — Never Bypass)

These are not configurable. They are hardcoded constraints.

1. **–40% stop-loss:** Every entry must place a GTT stop at –40% of premium paid. No entry without a stop.
2. **No stock option CEs:** Block any order where instrument is a stock CE (non-index CE). Index CEs (NIFTY, BANKNIFTY, FINNIFTY, MIDCPNIFTY, SENSEX) are allowed.
3. **IV Percentile ≤ 80:** Do not enter any new position when IV Percentile > 80.
4. **Max 1 open position** at any time.
5. **Max 2% of total capital** per trade (position sizing).
6. **Daily loss limit 3%** — halt all trading for the day if breached.
7. **Paper mode is default.** Live execution requires an explicit environment flag `LIVE_MODE=true`.

---

## Trading Strategy — Entry Conditions

**All** of the following must be true simultaneously to generate a BUY signal:

### Trend & Momentum
- ADX > 25
- DMI+ > DMI−
- −DI < 15
- +DI > 21

### EMA Alignment
- EMA(9) > EMA(30) > EMA(100) > EMA(300)

### MACD Confirmation
- MACD Histogram > 5

### SuperTrend AI Confirmation
- SuperTrend AI (LuxAlgo clustering variant) must be in bullish state
- Uses k-means clustering (3 clusters: Best/Average/Worst) on ATR-based SuperTrend performance
- Default: use "Best" cluster factor
- Parameters: ATR length=10, factor range 1–5, step=0.5, performance memory=10

### Exit Conditions
- Exit immediately when **any single** entry condition fails
- OR when –40% stop is hit (GTT handles this automatically)

---

## System Architecture

```
Kala-Vyapti/
├── core/                  # Rust — signal engine (indicators + SuperTrend AI)
│   ├── src/
│   │   ├── indicators/    # ADX, DMI, EMA, MACD, SuperTrend, ATR
│   │   ├── clustering/    # K-means for SuperTrend AI
│   │   └── lib.rs         # PyO3 bindings
│   └── Cargo.toml
│
├── engine/                # Python — orchestration layer
│   ├── data/              # WebSocket feed, Kite data fetcher, NSE data loader
│   ├── signals/           # Calls Rust core via PyO3
│   ├── brain/             # AI contract selection (scoring model)
│   ├── risk/              # RiskGate — hard rule enforcement
│   ├── execution/         # Kite order placement + GTT management
│   ├── journal/           # Trade logging, PostgreSQL
│   └── main.py
│
├── backtest/              # Python — backtesting framework
│   ├── engine.py
│   ├── data_loader.py
│   └── reports/
│
├── dashboard/             # Streamlit — analytics + monitoring UI
├── alerts/                # Telegram bot
└── infra/                 # Docker, systemd, config
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Signal engine | Rust (stable), PyO3 + maturin for Python bindings |
| Orchestration | Python 3.11+ |
| Broker API | Zerodha Kite Connect (kiteconnect Python SDK) |
| Data — live | Kite WebSocket (KiteTicker) |
| Data — historical | NSE direct + yfinance fallback, stored as Parquet |
| IV / Option chain | Sensibull API or Kite option chain endpoint |
| Database | PostgreSQL 15 (SQLAlchemy ORM) |
| Dashboard | Streamlit |
| Alerts | python-telegram-bot |
| Build system | maturin (Rust/Python), pip + pyproject.toml |
| Infra | Docker Compose (local dev), systemd (VPS deploy) |

---

## AI Contract Selection — Scoring Model

When a BUY signal fires, score all qualifying option contracts and select the top-ranked one.

**Pre-screening (eliminate before scoring):**
- Remove all stock CEs
- Remove contracts with IV Percentile > 80
- Remove contracts with bid-ask spread > 0.5%
- Remove contracts with OI < 10,000
- Remove contracts with DTE < 2 or DTE > 21

**Scoring weights:**
```
liquidity_score(oi, bid_ask_spread)     30%
iv_percentile_score(ivp)               25%   # lower IVP = better for buying
delta_score(delta, target=0.35)        20%   # prefer 0.3–0.45 delta
trend_alignment_score(strike_vs_spot)  15%
theta_score(dte)                       10%   # prefer DTE 7–14
```

---

## RiskGate Interface

Every order must pass through `RiskGate.validate(signal)` which returns `(bool, reason: str)`.

```python
class RiskGate:
    def validate(self, signal: Signal) -> tuple[bool, str]:
        # Returns (True, "ok") or (False, "reason for block")
        ...
```

**There is no override method. There is no admin bypass. If validate() returns False, the order is not placed.**

---

## Data Schemas

### Signal
```python
@dataclass
class Signal:
    timestamp: datetime
    symbol: str          # e.g. "NIFTY"
    action: Literal["BUY", "EXIT", "NONE"]
    timeframe: str       # "15m"
    adx: float
    dmi_plus: float
    dmi_minus: float
    ema_aligned: bool
    macd_hist: float
    supertrend_bullish: bool
    confidence: float    # 0.0–1.0
```

### Trade
```python
@dataclass
class Trade:
    id: str
    entry_time: datetime
    exit_time: datetime | None
    symbol: str
    strike: int
    option_type: Literal["CE", "PE"]
    expiry: date
    lots: int
    entry_price: float
    exit_price: float | None
    stop_loss_price: float        # entry_price * 0.60
    realized_pnl: float | None
    exit_reason: str | None       # "stop_loss" | "signal_exit" | "daily_limit"
    mode: Literal["paper", "live"]
```

---

## Environment Variables

```bash
KITE_API_KEY=
KITE_API_SECRET=
KITE_ACCESS_TOKEN=       # refreshed daily
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
DATABASE_URL=postgresql://...
LIVE_MODE=false          # MUST be explicitly true for live orders
PAPER_CAPITAL=500000     # simulated capital for paper trading
```

---

## Coding Conventions

- Python: type hints everywhere, dataclasses or Pydantic models for all data structures
- Rust: safe Rust only, no unsafe blocks unless absolutely necessary with comment explaining why
- All functions must have docstrings explaining purpose + parameters
- Logging: use Python `logging` module (not print), structured JSON logs in production
- Errors: never silently swallow exceptions; log + alert on every unexpected error
- Tests: pytest for Python, cargo test for Rust; minimum coverage for risk/execution modules = 90%

---

## What Each AI Agent Should Do

### Claude Code
- Architecture decisions and complex logic
- SuperTrend AI k-means port (Pine Script → Rust)
- RiskGate implementation
- Debugging and code review
- PRD → implementation planning

### GitHub Copilot
- Inline autocomplete while writing
- Boilerplate: SQLAlchemy models, Pydantic schemas, test stubs

### Google Jules (async)
- Isolated, well-defined modules with clear input/output specs
- Suggested delegation tasks are listed in status.md under each phase

### OpenAI Codex
- Alternative implementations for comparison
- Algorithm validation (compare indicator output vs reference)

---

## Current Phase

See `status.md` for current phase, completed tasks, and active workstreams.
