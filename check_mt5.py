import MetaTrader5 as mt5

terminals = [
    r"C:\Program Files\FBS MetaTrader 5\terminal64.exe",
    r"C:\Program Files\Headway MT5 Terminal\terminal64.exe",
    r"C:\Program Files\MetaTrader 5 Terminal\terminal64.exe"
]

for term in terminals:
    print("=" * 60)
    print(f"Connecting to: {term}")
    if not mt5.initialize(path=term):
        print(f"Failed to initialize: {mt5.last_error()}")
        continue
    
    term_info = mt5.terminal_info()
    acc_info = mt5.account_info()
    
    if term_info:
        print(f"Terminal: {term_info.name} (build {term_info.build})")
        print(f"Connected: {term_info.connected}")
    
    if acc_info:
        print(f"Account Login: {acc_info.login}")
        print(f"Account Name:  {acc_info.name}")
        print(f"Server:        {acc_info.server}")
        print(f"Company:       {acc_info.company}")
        print(f"Currency:      {acc_info.currency}")
        print(f"Balance:       ${acc_info.balance:,.2f} {acc_info.currency}")
        print(f"Equity:        ${acc_info.equity:,.2f} {acc_info.currency}")
        print(f"Profit:        ${acc_info.profit:,.2f} {acc_info.currency}")
        print(f"Leverage:      1:{acc_info.leverage}")
        print(f"Trade Allowed: {acc_info.trade_allowed}")
    else:
        print(f"No account logged in or error: {mt5.last_error()}")
    
    positions = mt5.positions_get()
    if positions:
        print(f"Open Positions: {len(positions)}")
        for p in positions:
            p_type = "BUY" if p.type == mt5.ORDER_TYPE_BUY else "SELL"
            print(f"  #{p.ticket} | {p.symbol} | {p_type} {p.volume} | Open: {p.price_open} | Profit: ${p.profit:.2f}")
    else:
        print("Open Positions: 0")

    mt5.shutdown()
