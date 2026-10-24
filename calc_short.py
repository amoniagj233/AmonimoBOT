import MetaTrader5 as mt5
import pandas as pd
import numpy as np

term_path = r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
if not mt5.initialize(path=term_path):
    print("MT5 Init failed")
    exit(1)

symbol = "BTCUSD"
mt5.symbol_select(symbol, True)
tick = mt5.symbol_info_tick(symbol)
sym_info = mt5.symbol_info(symbol)
acc = mt5.account_info()

rates_m15 = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 40)
df_m15 = pd.DataFrame(rates_m15)

high_low = df_m15['high'] - df_m15['low']
high_close = np.abs(df_m15['high'] - df_m15['close'].shift())
low_close = np.abs(df_m15['low'] - df_m15['close'].shift())
tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
atr_m15 = tr.rolling(14).mean().iloc[-1]

recent_high = df_m15['high'].iloc[-16:].max()
recent_low = df_m15['low'].iloc[-16:].min()

entry = tick.bid
# Stop Loss placed above recent M15 swing high + 0.5 ATR
stop_loss = round(recent_high + (0.5 * atr_m15), 2)
stop_distance = round(stop_loss - entry, 2)

# Targets: 1.5R and 2.0R
tp_1 = round(entry - (1.5 * stop_distance), 2)
tp_2 = round(entry - (2.0 * stop_distance), 2)

balance = acc.balance
risk_budget = balance * 0.01

lots_raw = risk_budget / stop_distance
vol_step = sym_info.volume_step
lots = round(int(lots_raw / vol_step) * vol_step, 2)
if lots < sym_info.volume_min:
    lots = sym_info.volume_min
if lots > sym_info.volume_max:
    lots = sym_info.volume_max

actual_risk = round(lots * stop_distance, 2)
actual_risk_pct = round((actual_risk / balance) * 100, 2)

gain_tp1 = round(lots * (entry - tp_1), 2)
gain_tp2 = round(lots * (entry - tp_2), 2)

print(f"BID_ENTRY={entry}")
print(f"ASK={tick.ask}")
print(f"STOP_LOSS={stop_loss}")
print(f"STOP_DIST={stop_distance}")
print(f"TP_1={tp_1}")
print(f"TP_2={tp_2}")
print(f"LOTS={lots}")
print(f"ACTUAL_RISK={actual_risk}")
print(f"ACTUAL_RISK_PCT={actual_risk_pct}")
print(f"GAIN_TP1={gain_tp1}")
print(f"GAIN_TP2={gain_tp2}")
print(f"BALANCE={balance}")

mt5.shutdown()
