import backtrader as bt

def run_backtrader_sync(data_feed, strategy_name, params, initial_portfolio_value):
    from components.strategy_class import create_strategy_class
    """Run Backtrader synchronously in a separate thread."""
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    Strategy = create_strategy_class(strategy_name)
    cerebro.addstrategy(Strategy, params=params)
    strategy = cerebro.run()[0]
    final_portfolio_value = cerebro.broker.getvalue()
    
    # Save results
    result = {
        **params,  # Include parameter values in results
        "Portfolio Value": f"{final_portfolio_value:.2f}",
    }

    return result