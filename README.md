# AmonimoBOT

> **Next-Generation Autonomous Quantitative Day Trading Workstation & MT5 Execution Engine**

AmonimoBOT is an institutional-grade algorithmic trading terminal and web dashboard built on Python and MetaTrader 5 (Deriv), engineered for high-frequency technical analysis, multi-timeframe regime detection, multi-tier risk management, and automatic execution.

---

## 🚀 Key Features

### 1. ⚡ Automatic 3-Trade Multi-TP Power System
- **3 Concurrent Positions:** Simultaneously opens 3 separate positions in the same direction on the symbol, maximizing capital efficiency without crowding broker position limits.
- **Shared 5% Account Stop Loss:** Combined planned loss across all 3 trades is strictly bounded to **5% of the reference account balance** (\$50.00 max on a \$1,000 balance; \$16.67 planned risk per trade). All 3 positions share the exact same protective Stop Loss price level.
- **Dynamic 3-Tier Profit Targets:**
  - **Trade 1:** TP 2% (+\$20.00 on \$1,000) — High hit rate (~65%), locks in guaranteed quick cash, covers spreads/commissions.
  - **Trade 2:** TP 5% (+\$50.00 on \$1,000) — Core trend move capture (~35%), banks the meat of the move.
  - **Trade 3:** Dynamic AI Runner (+\$150.00 / 2.5× ATR) — Infinite upside trailing stop for massive breakout days.
- **Independent Position Lifecycle:** When an individual TP target is reached, only that position closes, securing realized profit while other runners remain active. If the shared Stop Loss is breached, all remaining positions in the group close simultaneously.

### 2. 📡 Automated Recommended Trade Setups & Technical Invalidation
- **Continuous 3-Minute Re-Scan:** Auto-refreshes trading opportunities every 3 minutes across 21+ Deriv synthetic indices, forex pairs, and crypto assets.
- **Weekend / Closed Market Filtering:** Automatically verifies market open status. Any symbol whose market is closed (e.g. weekend Forex/Gold) is completely filtered out of active recommendations.
- **Duplicate Prevention:** Tracks open positions and previously executed setups. If a position is active or already journaled, duplicate recommendations are blocked.
- **Technical Invalidation:** Each setup includes precise Entry, Direction, Stop Loss, Take Profit, Risk-to-Reward ratio, supporting technical signals (EMA20, RSI(14), ATR(14)), and strict invalidation criteria.

### 3. 🎯 High-Confidence Auto-Trade Engine
- **Confidence Scoring (0–100%):** Weighted multi-factor model evaluating trend alignment, momentum zone, ATR volatility expansion, and spread efficiency.
- **Autonomous Execution:** When enabled, setups scoring **90% to 100% confidence** are automatically executed without manual intervention, subject to pre-trade risk and margin verification.
- **Emergency Protection:** Real-time broker position limit checks, margin pre-calculation, and 1-click **Panic Close All** emergency circuit breaker.

### 4. 📊 Symbol Trading Performance & Trade Analytics Dashboard
- Analyzes MT5 historical deals across all traded symbols.
- Metrics per symbol: Total Trades, Win Rate %, Net P&L, Profit Factor, Expectancy, Max Drawdown, and Risk-Adjusted Score.
- **Priority Ranking (1 to 5):** Recommends symbols to **INCREASE FOCUS**, **MAINTAIN**, or **AVOID**.

---

## 🛠️ Tech Stack & Requirements

- **Platform:** MetaTrader 5 (Deriv Demo/Live)
- **Language:** Python 3.11+
- **Key Libraries:** `MetaTrader5`, `uv`
- **Frontend:** Responsive Dark Mode UI with Tailwind CSS, Chart.js, Lucide Icons, and real-time polling.

---

## ⚡ Quick Start

1. **Launch MetaTrader 5:**
   Open the MT5 terminal and ensure algorithmic trading is enabled under `Tools -> Options -> Expert Advisors -> Allow algorithmic trading`.

2. **Run Workstation:**
   ```bash
   uv run --python 3.11 --with MetaTrader5 python web_app.py
   ```

3. **Open Dashboard:**
   Navigate to [http://127.0.0.1:8765/](http://127.0.0.1:8765/) in any web browser.

---

## 📄 License
MIT License
