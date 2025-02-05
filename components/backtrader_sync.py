import backtrader as bt
import numpy_financial as npf

def run_backtrader_sync(data_feed, strategy_name, params, initial_portfolio_value, stock_data):
    from components.strategy_class import create_strategy_class
    from components.formulas import calculate_metrics, calculate_cash_flows
    """Run Backtrader synchronously in a separate thread."""
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    Strategy = create_strategy_class(strategy_name)
    cerebro.addstrategy(Strategy, params=params)
    strategy = cerebro.run()[0]
    final_portfolio_value = cerebro.broker.getvalue()
    # Calculate cash flows
    cash_flows = calculate_cash_flows(strategy.log_data, initial_portfolio_value, stock_data)
    # print(f"Cash flow: {cash_flows}")
    irr = npf.irr(cash_flows)
    
    # Calculate additional metrics
    win_rate, sharpe_ratio, max_drawdown = calculate_metrics(
        strategy,
        initial_portfolio_value=initial_portfolio_value,
        final_portfolio_value=cerebro.broker.getvalue(), stock_data=stock_data, cash_flows=cash_flows
    )
    
    # Save results
    result = {
        **params,  # Include parameter values in results
        "Win Rate": win_rate,
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Max Drawdown": f"{max_drawdown:.2f}%",
        "IRR": f"{irr:.2f}",
        "Portfolio Value": f"{final_portfolio_value:.2f}",
    }

    return result