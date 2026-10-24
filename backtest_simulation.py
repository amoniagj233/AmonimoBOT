import MetaTrader5 as mt5
import numpy as np

if not mt5.initialize():
    print("MT5 Init Failed:", mt5.last_error())
    exit(1)

symbols = [
    "BTCUSD",
    "Volatility 100 (1s) Index"
]

print("Backtesting Multi-Timeframe Alignment (H1 Trend Filter + M15 Momentum Breakout)...")

for sym in symbols:
    info = mt5.symbol_info(sym)
    if not info:
        continue
    rates_m15 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 1500)
    rates_h1 = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_H1, 0, 400)
    if rates_m15 is None or rates_h1 is None:
        continue
    
    # H1 Trend (EMA 50)
    h1_closes = rates_h1['close']
    h1_times = rates_h1['time']
    h1_ema50 = np.zeros(len(h1_closes))
    alpha_h1 = 2.0 / (50 + 1)
    h1_ema50[0] = h1_closes[0]
    for idx in range(1, len(h1_closes)):
        h1_ema50[idx] = alpha_h1 * h1_closes[idx] + (1 - alpha_h1) * h1_ema50[idx-1]
        
    # Map H1 EMA50 to M15 times
    closes = rates_m15['close']
    highs = rates_m15['high']
    lows = rates_m15['low']
    times_m15 = rates_m15['time']
    n = len(rates_m15)
    
    # ATR 14
    tr0 = highs[1:] - lows[1:]
    tr1 = np.abs(highs[1:] - closes[:-1])
    tr2 = np.abs(lows[1:] - closes[:-1])
    tr = np.maximum(tr0, np.maximum(tr1, tr2))
    tr = np.insert(tr, 0, tr0[0])
    atr = np.zeros(n)
    for idx in range(14, n):
        atr[idx] = np.mean(tr[idx-14:idx])
        
    # EMA 20
    ema20 = np.zeros(n)
    alpha = 2.0 / (20 + 1)
    ema20[0] = closes[0]
    for idx in range(1, n):
        ema20[idx] = alpha * closes[idx] + (1 - alpha) * ema20[idx-1]
        
    # RSI 14
    deltas = np.diff(closes)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    rsi = np.full(n, 50.0)
    for idx in range(15, n):
        avg_g = np.mean(gains[idx-15:idx-1]) or 0.0001
        avg_l = np.mean(losses[idx-15:idx-1]) or 0.0001
        rs = avg_g / avg_l
        rsi[idx] = 100.0 - (100.0 / (1.0 + rs))

    strat_pnls = {
        'No H1 Filter (Standard M15)': [],
        'WITH H1 Trend Filter (EMA50 Alignment)': []
    }
    
    for filter_mode in ['No H1 Filter (Standard M15)', 'WITH H1 Trend Filter (EMA50 Alignment)']:
        for i in range(50, n - 30):
            t_m15 = times_m15[i]
            c, prev_c = closes[i], closes[i-1]
            e, prev_e = ema20[i], ema20[i-1]
            r, a = rsi[i], atr[i]
            
            if a <= 0:
                continue
                
            # Find active H1 candle
            h1_idx = np.searchsorted(h1_times, t_m15, side='right') - 1
            h1_trend_bias = 'BULLISH' if h1_closes[h1_idx] > h1_ema50[h1_idx] else 'BEARISH'
            
            signal = None
            if c > e and prev_c <= prev_e and 40 < r < 65:
                if filter_mode == 'WITH H1 Trend Filter (EMA50 Alignment)':
                    if h1_trend_bias == 'BULLISH':  # Only buy in bull trend!
                        signal = 'BUY'
                else:
                    signal = 'BUY'
            elif c < e and prev_c >= prev_e and 35 < r < 60:
                if filter_mode == 'WITH H1 Trend Filter (EMA50 Alignment)':
                    if h1_trend_bias == 'BEARISH':  # Only sell in bear trend!
                        signal = 'SELL'
                else:
                    signal = 'SELL'
                    
            if not signal:
                continue
                
            entry = c
            risk_dist = a * 1.5
            sl_initial = entry - risk_dist if signal == 'BUY' else entry + risk_dist
            tp1 = entry + (risk_dist * 1.2) if signal == 'BUY' else entry - (risk_dist * 1.2)
            tp2 = entry + (risk_dist * 3.0) if signal == 'BUY' else entry - (risk_dist * 3.0)
            tp3 = entry + (risk_dist * 9.0) if signal == 'BUY' else entry - (risk_dist * 9.0)
            
            t1_pnl, t2_pnl, t3_pnl = None, None, None
            for k in range(i+1, min(i+31, n)):
                hi, lo = highs[k], lows[k]
                if t1_pnl is None:
                    if (signal == 'BUY' and hi >= tp1) or (signal == 'SELL' and lo <= tp1):
                        t1_pnl = 20.0
                    elif (signal == 'BUY' and lo <= sl_initial) or (signal == 'SELL' and hi >= sl_initial):
                        t1_pnl = -16.67
                if t2_pnl is None:
                    if (signal == 'BUY' and hi >= tp2) or (signal == 'SELL' and lo <= tp2):
                        t2_pnl = 50.0
                    elif (signal == 'BUY' and lo <= sl_initial) or (signal == 'SELL' and hi >= sl_initial):
                        t2_pnl = -16.67
                if t3_pnl is None:
                    if (signal == 'BUY' and hi >= tp3) or (signal == 'SELL' and lo <= tp3):
                        t3_pnl = 150.0
                    elif (signal == 'BUY' and lo <= sl_initial) or (signal == 'SELL' and hi >= sl_initial):
                        t3_pnl = -16.67
                if t1_pnl is not None and t2_pnl is not None and t3_pnl is not None:
                    break
                    
            last_c = closes[min(i+30, n-1)]
            p_c = (last_c - entry) / risk_dist if signal == 'BUY' else (entry - last_c) / risk_dist
            t1_pnl = t1_pnl if t1_pnl is not None else round(p_c * 16.67, 2)
            t2_pnl = t2_pnl if t2_pnl is not None else round(p_c * 16.67, 2)
            t3_pnl = t3_pnl if t3_pnl is not None else round(p_c * 16.67, 2)
            
            strat_pnls[filter_mode].append(t1_pnl + t2_pnl + t3_pnl)
            
    print(f"\n=========================================================================")
    print(f"SYMBOL: {sym}")
    print(f"=========================================================================")
    for fname, pnls in strat_pnls.items():
        net = sum(pnls)
        wins = sum(1 for p in pnls if p > 0)
        losses = sum(abs(p) for p in pnls if p < 0)
        wr = round((wins / len(pnls)) * 100, 1) if pnls else 0
        pf = round(sum(p for p in pnls if p > 0) / losses, 2) if losses > 0 else 99.0
        print(f"• {fname:45}: Trades = {len(pnls):3d} | Net P&L = ${net:+8.2f} | Win Rate = {wr:4.1f}% | Profit Factor = {pf:4.2f}")

mt5.shutdown()
