import concurrent.futures
import base64
import os
import backtrader as bt
import pandas as pd
import concurrent


def run_strategy(strategy_name, trade_size, data_feed, initial_portfolio_value, stock_data, start_date):
    from components.backtrader_sync import run_backtrader_sync
    from components.parameter_combinations import get_parameter_combinations
    from components.folder_name import UPLOAD_FOLDER
    from components.strategy_class import create_strategy_class

    results = []
    param_names, param_combinations = get_parameter_combinations(strategy_name)
    valid_combinations = [
        dict(zip(param_names, combo)) for combo in param_combinations if combo[0] > combo[1]
    ]
    for params in valid_combinations:
        params['Trade Size'] = trade_size

    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                run_backtrader_sync, data_feed, strategy_name, params, initial_portfolio_value, stock_data
            ): params for params in valid_combinations
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)

    log_df = pd.DataFrame(results)
    csv_robustness = f'robustness_test_{strategy_name}.csv'
    csv_path = os.path.join(UPLOAD_FOLDER, csv_robustness)
    log_df.to_csv(csv_path, index=False)

    # Get best strategy
    sorted_results = sorted(results, key=lambda x: float(x["Portfolio Value"]), reverse=True)
    highest_result = sorted_results[0]
    exclude_keys = {"Win Rate", "Sharpe Ratio", "Max Drawdown", "IRR", "Portfolio Value"}
    filtered_params = {key: value for key, value in highest_result.items() if key not in exclude_keys}

    # Backtest the best strategy
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    Graph = create_strategy_class(strategy_name=strategy_name, stop_logic='stop_logic')
    cerebro.addstrategy(Graph, params=filtered_params)
    strategy = cerebro.run()

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
        "Strategy name": strategy_name,
        "Start Date": start_date,
        "Trade Size": trade_size,
        "Robustness Test": encoded_robustness_logs,
        "Trade Log": encoded_trade_log,
        "Graph Img": encoded_graph,
    }
    return backtest_results