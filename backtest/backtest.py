# backtest.py
from .backtest_runner import BacktestRunner
from .backtrader_engine import run_backtrader_with_df, BTConfig


def run_backtest():
    """Main backtest function - Backtrader adapter path"""
    runner = BacktestRunner(
        symbol="EURUSD",
        initial_balance=10000
    )

    print("📡 Fetching market data...")
    df = runner.fetch_data(days=65)
    if df is None:
        print("❌ No data fetched. Exiting.")
        return
    if 'volume' not in df.columns:
        if 'tick_volume' in df.columns:
            df = df.rename(columns={'tick_volume': 'volume'})
        elif 'real_volume' in df.columns:
            df = df.rename(columns={'real_volume': 'volume'})

    print("🚀 Running Backtrader with RSI strategy...")
    cerebro, results, analyzers = run_backtrader_with_df(
        df=df,
        strategy_name="rsi",
        strategy_params={"rsi_period": 14, "oversold": 30, "overbought": 70},
        config=BTConfig(symbol="EURUSD", cash=10000, stake=10000, sl_pips=0.001, tp_pips=0.002)
    )

    # Zoomerified output summary
    try:
        sharpe = analyzers.get("sharpe", {})
        dd = analyzers.get("drawdown", {})
        trades = analyzers.get("trades", {})
        
        print("\n" + "✨" * 25)
        print("📊 BACKTEST RESULTS 📊")
        print("✨" * 25)
        
        final_value = cerebro.broker.getvalue()
        profit_loss = final_value - 10000
        pnl_percent = (profit_loss / 10000) * 100
        pnl_emoji = "📈" if profit_loss > 0 else "📉" if profit_loss < 0 else "➖"
        
        print(f"💰 Final Portfolio: ${final_value:,.2f}")
        print(f"🤑 P&L: {pnl_emoji} ${profit_loss:+,.2f} ({pnl_percent:+.2f}%)")
        
        if isinstance(sharpe, dict):
            sharpe_val = sharpe.get('sharperatio', 'N/A')
            print(f"🎯 Sharpe Ratio: {sharpe_val}")
        
        if isinstance(dd, dict):
            max_dd = dd.get('max', {}).get('drawdown', 'N/A')
            print(f"📉 Max Drawdown: {max_dd}%")
        
        if isinstance(trades, dict):
            total_trades = trades.get('total', {}).get('total', 0)
            won_trades = trades.get('won', {}).get('total', 0)
            lost_trades = trades.get('lost', {}).get('total', 0)
            win_rate = (won_trades / total_trades * 100) if total_trades > 0 else 0
            
            print(f"🎮 Total Trades: {total_trades}")
            print(f"✅ Wins: {won_trades} | ❌ Losses: {lost_trades}")
            print(f"🏆 Win Rate: {win_rate:.1f}%")
        
        # Vibe check
        if profit_loss > 500:
            print("\n💎🙌 BAG ALERT! Strategy is CRUSHING IT! 🚀")
        elif profit_loss > 0:
            print("\n😎 Solid gains! W strategy! 💯")
        elif profit_loss > -200:
            print("\n🤷‍♂️ Meh... Could be worse. Sideways vibe. 🎭")
        else:
            print("\n💀 RIP Portfolio... Time to touch grass 🌿")
            
        print("✨" * 25)
        
    except Exception as e:
        print("❌ Could not print analyzers:", e)


if __name__ == "__main__":
    run_backtest()