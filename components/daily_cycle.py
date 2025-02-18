import backtrader as bt
import numpy_financial as npf
import os
import base64
def daily_cycle(strategy_name, trade_size, data_feed, initial_portfolio_value, stock_data, start_date, filtered_params):
    from components.strategy_class import create_strategy_class
    from components.formulas import calculate_cash_flows, calculate_metrics
    from components.segregated_trades import segregate_trades

    # Backtest the best strategy
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    Graph = create_strategy_class(strategy_name=strategy_name, stop_logic='stop_logic')
    cerebro.addstrategy(Graph, params=filtered_params)
    strategy = cerebro.run()[0]
    portfolio_value = cerebro.broker.getvalue()

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

    segregated_trades = segregate_trades(strategy.log_data)

    # Check if the file exists
    csv_trade_log = f'static/files/trade_log_{strategy_name}.csv'
    if os.path.exists(csv_trade_log):
        # Read the file and encode it as Base64
        with open(csv_trade_log, 'rb') as f:
            encoded_trade_log = base64.b64encode(f.read()).decode('utf-8')
    
    graph_img = f'static/files/{strategy_name}_strategy_graph.png'
    if os.path.exists(graph_img):
        with open(graph_img, "rb") as image_file:
            encoded_graph = base64.b64encode(image_file.read()).decode('utf-8')

    # Encode CSV file as base64
    csv_robustness = f'static/files/robustness_test_{strategy_name}.csv'
    if os.path.exists(graph_img):
        with open(csv_robustness, "rb") as f:
            encoded_robustness_logs = base64.b64encode(f.read()).decode('utf-8')
        
    backtest_results = {
        "Strategy Name": strategy_name,
        "Start Date": start_date,
        "Trade Size": trade_size,
        "Robustness Test": encoded_robustness_logs,
        "Trade Log": encoded_trade_log,
        "Graph Img": encoded_graph,
        "Win Rate": win_rate,
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Max Drawdown": f"{max_drawdown:.2f}%",
        "IRR": f"{irr:.2f}",
        "Portfolio Value": portfolio_value,
        "Best Parameters": filtered_params,
        "Segregated Trades": segregated_trades,
        "Pre Buy/Sell Indicator": strategy.pre_buy_sell_alert
    }
    return backtest_results
