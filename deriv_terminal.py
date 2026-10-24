import MetaTrader5 as mt5
import sys

DERIV_TERMINAL_PATH = r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"

def connect():
    if not mt5.initialize(path=DERIV_TERMINAL_PATH):
        print(f"Failed to connect to Deriv MT5: {mt5.last_error()}", file=sys.stderr)
        return False
    return True

def get_status():
    if not connect():
        return
    
    term = mt5.terminal_info()
    acc = mt5.account_info()
    
    print("=" * 55)
    print("           DERIV MT5 TERMINAL STATUS")
    print("=" * 55)
    print(f"Terminal:          {term.name} (Build {term.build})")
    print(f"Server Connection: {'CONNECTED' if term.connected else 'DISCONNECTED'}")
    print(f"Server Ping:       {term.ping_last / 1000:.2f} ms")
    print(f"Account Login:     {acc.login}")
    print(f"Account Name:      {acc.name}")
    print(f"Broker Server:     {acc.server}")
    print(f"Company:           {acc.company}")
    print(f"Currency:          {acc.currency}")
    print(f"Balance:           ${acc.balance:,.2f} {acc.currency}")
    print(f"Equity:            ${acc.equity:,.2f} {acc.currency}")
    print(f"Free Margin:       ${acc.margin_free:,.2f} {acc.currency}")
    print(f"Margin Level:      {acc.margin_level:.2f}%")
    print(f"Leverage:          1:{acc.leverage}")
    print(f"Trading Allowed:   {acc.trade_allowed}")
    print(f"Algo/EA Allowed:   {acc.trade_expert}")
    print("-" * 55)
    
    positions = mt5.positions_get()
    if positions:
        print(f"Active Positions: {len(positions)}")
        for p in positions:
            p_type = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
            print(f"  #{p.ticket} | {p.symbol} | {p_type} {p.volume} | Open: {p.price_open} | Current: {p.price_current} | P/L: ${p.profit:.2f}")
    else:
        print("Active Positions: 0 (No open trades)")

    orders = mt5.orders_get()
    if orders:
        print(f"Pending Orders: {len(orders)}")
        for o in orders:
            print(f"  #{o.ticket} | {o.symbol} | Type: {o.type} | Volume: {o.volume_initial} | Price: {o.price_open}")
    else:
        print("Pending Orders: 0")

    print("=" * 55)
    mt5.shutdown()

if __name__ == "__main__":
    get_status()
