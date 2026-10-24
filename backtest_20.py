import MetaTrader5 as mt5
import numpy as np
import time

def main():
    if not mt5.initialize():
        print("Failed to initialize MT5")
        return

    symbols = ['Step Index', 'Jump 75 Index', 'Volatility 75 Index', 'Boom 500 Index', 'Crash 300 Index']
    
    starting_balance = 20.0
    balance = starting_balance
    peak = balance
    max_dd = 0.0
    trade_log = []
    skipped_heavy = 0
    
    for sym in symbols:
        mt5.symbol_select(sym, True)
        time.sleep(0.3)
        rates = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_M15, 0, 400)
        if rates is None or len(rates) < 100:
            continue
            
        info = mt5.symbol_info(sym)
        closes = rates['close']
        highs = rates['high']
        lows = rates['low']
        
        tr = np.maximum(highs[1:] - lows[1:], np.abs(highs[1:] - closes[:-1]))
        tr = np.maximum(tr, np.abs(lows[1:] - closes[:-1]))
        
        weights20 = np.exp(np.linspace(-1., 0., 20))
        weights20 /= weights20.sum()
        
        deltas = np.diff(closes)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        i = 50
        while i < len(closes) - 20:
            cur_p = closes[i]
            cur_tr = tr[max(0, i-14):i]
            cur_atr = float(np.mean(cur_tr))
            
            sub_closes = closes[i-19:i+1]
            cur_ema = float(np.sum(sub_closes * weights20))
            
            sub_g = gains[i-14:i]
            sub_l = losses[i-14:i]
            ag = float(np.mean(sub_g)) if len(sub_g) > 0 else 0.001
            al = float(np.mean(sub_l)) if len(sub_l) > 0 else 0.001
            cur_rsi = 100.0 - (100.0 / (1.0 + (ag / al)))
            
            is_buy = (cur_p > cur_ema) and (closes[i] > closes[i-2]) and (46 <= cur_rsi <= 60)
            is_sell = (cur_p < cur_ema) and (closes[i] < closes[i-2]) and (40 <= cur_rsi <= 54)
            
            if not is_buy and not is_sell:
                i += 1
                continue
                
            bias = 'BUY' if is_buy else 'SELL'
            stop_dist = cur_atr * 1.5
            
            # Dollar risk per minimum lot
            if sym == 'Step Index':
                dollar_risk = stop_dist * 0.1
            elif sym == 'Jump 75 Index':
                dollar_risk = stop_dist * 0.01
            elif sym == 'Volatility 75 Index':
                dollar_risk = stop_dist * 0.01
            elif sym == 'Boom 500 Index':
                dollar_risk = stop_dist * 0.2
            elif sym == 'Crash 300 Index':
                dollar_risk = stop_dist * 0.5
            else:
                dollar_risk = stop_dist * info.volume_min
                
            # $20 Safety Gate:
            # If minimum lot stop distance exceeds $1.20 (6% max risk of $20), SKIP!
            # Heavy symbols like Crash 300 / Boom 500 would wipe out 35% on a single loss.
            if dollar_risk > 1.20:
                skipped_heavy += 1
                i += 1
                continue
                
            entry = cur_p
            sl_price = entry - stop_dist if is_buy else entry + stop_dist
            tp_price = entry + (stop_dist * 2.0) if is_buy else entry - (stop_dist * 2.0)
            
            outcome = None
            exit_bar = i
            for j in range(i + 1, min(i + 25, len(closes))):
                if is_buy:
                    if lows[j] <= sl_price:
                        outcome = 'SL'
                        exit_bar = j
                        break
                    elif highs[j] >= tp_price:
                        outcome = 'TP'
                        exit_bar = j
                        break
                else:
                    if highs[j] >= sl_price:
                        outcome = 'SL'
                        exit_bar = j
                        break
                    elif lows[j] <= tp_price:
                        outcome = 'TP'
                        exit_bar = j
                        break
                        
            if outcome == 'TP':
                pnl = dollar_risk * 2.0
                balance += pnl
                trade_log.append({'sym': sym, 'bias': bias, 'res': 'WIN', 'pnl': round(pnl, 2), 'bal': round(balance, 2)})
            elif outcome == 'SL':
                pnl = -dollar_risk
                balance += pnl
                trade_log.append({'sym': sym, 'bias': bias, 'res': 'LOSS', 'pnl': round(pnl, 2), 'bal': round(balance, 2)})
                
            if balance > peak:
                peak = balance
            dd = (peak - balance) / peak * 100.0
            if dd > max_dd:
                max_dd = dd
            i = exit_bar + 1

    mt5.shutdown()
    
    total = len(trade_log)
    wins = [t for t in trade_log if t['res'] == 'WIN']
    losses = [t for t in trade_log if t['res'] == 'LOSS']
    wr = len(wins) / total * 100 if total > 0 else 0
    gp = sum(t['pnl'] for t in wins)
    gl = abs(sum(t['pnl'] for t in losses))
    pf = gp / gl if gl > 0 else 999
    net = balance - starting_balance
    pct = net / starting_balance * 100
    
    print("BACKTEST_20_START")
    print(f"STARTING_BALANCE: ${starting_balance:.2f}")
    print(f"FINAL_BALANCE: ${balance:.2f}")
    print(f"NET_PROFIT: ${net:+.2f} ({pct:+.1f}%)")
    print(f"TOTAL_TRADES: {total}")
    print(f"WINS: {len(wins)} ({wr:.1f}%)")
    print(f"LOSSES: {len(losses)} ({100-wr:.1f}%)")
    print(f"PROFIT_FACTOR: {pf:.2f}")
    print(f"MAX_DRAWDOWN: {max_dd:.1f}%")
    print(f"HEAVY_RISK_SYMBOLS_SKIPPED: {skipped_heavy}")
    print("SAMPLE_TRADES:")
    for t in trade_log[:8]:
        print(f"  {t['sym']} {t['bias']}: {t['res']} | PnL: ${t['pnl']:+.2f} | Balance: ${t['bal']:.2f}")
    print("BACKTEST_20_END")

if __name__ == '__main__':
    main()
