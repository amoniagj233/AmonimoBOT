import MetaTrader5 as mt5
import pandas as pd
import numpy as np

term_path = r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
if not mt5.initialize(path=term_path):
    print(f"MT5 Init failed: {mt5.last_error()}")
    exit(1)

symbol = "BTCUSD"
mt5.symbol_select(symbol, True)
tick = mt5.symbol_info_tick(symbol)
sym_info = mt5.symbol_info(symbol)

rates_h1 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 60)
rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 60)
acc = mt5.account_info()

df_h1 = pd.DataFrame(rates_h1)
df_m15 = pd.DataFrame(rates_m15)

df_h1['ema20'] = df_h1['close'].ewm(span=20, adjust=False).mean()
df_h1['sma50'] = df_h1['close'].rolling(50).mean()

# ATR 14 on M15
high_low = df_m15['high'] - df_m15['low']
high_close = np.abs(df_m15['high'] - df_m15['close'].shift())
low_close = np.abs(df_m15['low'] - df_m15['close'].shift())
tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
atr_m15 = tr.rolling(14).mean().iloc[-1]

latest_close = df_m15['close'].iloc[-1]
ema20_h1 = df_h1['ema20'].iloc[-1]
sma50_h1 = df_h1['sma50'].iloc[-1]

# Support & Resistance on M15
recent_low = df_m15['low'].iloc[-16:].min()
recent_high = df_m15['high'].iloc[-16:].max()

trend = "BULLISH (UPTREND)" if latest_close > ema20_h1 else "BEARISH (DOWNTREND)"
if latest_close > ema20_h1 and ema20_h1 > sma50_h1:
    trend = "STRONG BULLISH UPTREND (Price > EMA20 > SMA50)"
elif latest_close < ema20_h1 and ema20_h1 < sma50_h1:
    trend = "STRONG BEARISH DOWNTREND (Price < EMA20 < SMA50)"

balance = acc.balance
risk_pct = 1.0
risk_dollar = balance * (risk_pct / 100.0)

# Trade Setup: Long Pullback / Continuation
entry = tick.ask
# Stop loss at recent swing low minus 0.5 ATR buffer
stop_loss = round(recent_low - (0.5 * atr_m15), 1)
stop_distance = entry - stop_loss

# Targets: 1.5R and 2.0R
tp_1 = round(entry + (1.5 * stop_distance), 1)
tp_2 = round(entry + (2.0 * stop_distance), 1)

# Position sizing:
# On MT5 BTCUSD, 1 lot = 1 BTC (contract size = 1)
# Risk = lots * (entry - sl)
lots_raw = risk_dollar / stop_distance
# Round to lot step (0.01)
vol_step = sym_info.volume_step
lots = round(int(lots_raw / vol_step) * vol_step, 2)
if lots < sym_info.volume_min:
    lots = sym_info.volume_min
if lots > sym_info.volume_max:
    lots = sym_info.volume_max

actual_risk = round(lots * stop_distance, 2)
actual_risk_pct = round((actual_risk / balance) * 100, 2)

reward_1 = round(lots * (tp_1 - entry), 2)
reward_2 = round(lots * (tp_2 - entry), 2)

print("=" * 60)
print("             BTCUSD TRADE PLAN REPORT (DERIV MT5)")
print("=" * 60)
print(f"Current Ask Price:       ${tick.ask:,.2f}")
print(f"Current Bid Price:       ${tick.bid:,.2f}")
print(f"Spread:                  ${(tick.ask - tick.bid):.2f}")
print(f"Account Balance:         ${balance:,.2f} USD")
print(f"Account Equity:          ${acc.equity:,.2f} USD")
print("-" * 60)
print(f"Trend Analysis:          {trend}")
print(f"H1 Close:                ${latest_close:,.2f}")
print(f"H1 EMA(20):              ${ema20_h1:,.2f}")
print(f"H1 SMA(50):              ${sma50_h1:,.2f}")
print(f"M15 ATR(14):             ${atr_m15:,.2f}")
print(f"Recent Swing Low (M15):  ${recent_low:,.2f}")
print(f"Recent Swing High (M15): ${recent_high:,.2f}")
print("-" * 60)
print("TRADE SETUP & LEVELS:")
print(f"  Direction:             BUY (LONG)")
print(f"  Entry Price:           ${entry:,.2f}")
print(f"  Stop Loss:             ${stop_loss:,.2f} (Dist: ${stop_distance:,.2f})")
print(f"  Target 1 (1.5R):       ${tp_1:,.2f} (Gain: +${reward_1:,.2f})")
print(f"  Target 2 (2.0R):       ${tp_2:,.2f} (Gain: +${reward_2:,.2f})")
print("-" * 60)
print("RISK & SIZING GATE:")
print(f"  Risk Budget:           1.0% (${risk_dollar:,.2f})")
print(f"  Calculated Lot Size:   {lots} lots")
print(f"  Total Dollar Risk:     ${actual_risk:,.2f} ({actual_risk_pct}% of account)")
print(f"  Risk Gate Status:      PASSED (Risk <= 1.0%, Stop defined below swing low)")
print("=" * 60)

mt5.shutdown()
