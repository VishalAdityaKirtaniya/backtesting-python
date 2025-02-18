import concurrent.futures
import backtrader as bt
import pandas as pd
import numpy_financial as npf
from strategies import strategy_tree
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from components.folder_name import UPLOAD_FOLDER
import base64
import concurrent
import time
from datetime import datetime

app = Flask(__name__)

CORS(app) # Enable CORS for all routes

os.makedirs(UPLOAD_FOLDER, exist_ok=True) # Ensure the directory for saving files exists

@app.route('/backtest', methods=['POST'])
def backtest():
    start_time = time.time()
    from components.strategy_class import create_strategy_class
    from components.fetch_data import fetch_stock_data
    from components.parameter_combinations import get_parameter_combinations
    from components.backtrader_sync import run_backtrader_sync
    from components.formulas import calculate_metrics, calculate_cash_flows
    data = request.json
    print(data)
    strategy_name = data.get('strategy_name', 'macd')
    initial_portfolio_value = data.get('initial_portfolio_value', 100000)
    stock_symbol = data.get('stock_symbol', 'RELIANCE.NS')
    start_date = data.get('start_date', '2023-01-01')
    trade_size = data.get('trade_size', 30)
    interval = '1d'

    # Fetch stock data and interval
    stock_data = fetch_stock_data(stock_symbol, start_date, interval)
    data_feed = bt.feeds.PandasData(dataname=stock_data)
    print(f'stock data: {stock_data}')
    results = []
    param_names, param_combinations = get_parameter_combinations(strategy_name)
    # Filter invalid parameter combinations before running
    valid_combinations = [
        dict(zip(param_names, combo)) for combo in param_combinations if combo[0] > combo[1]
    ]
    # Add 'Trade Size' to each parameter set
    for params in valid_combinations:
        params['Trade Size'] = trade_size  # Ensure trade size is included
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = {
            executor.submit(
                run_backtrader_sync, data_feed, strategy_name, params, initial_portfolio_value, stock_data
            ): params for params in valid_combinations
        }
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
    # Convert log data to a DataFrame and save to CSV 
    log_df = pd.DataFrame(results)
    # print(log_df)
    csv_robustness = f'robustness_test_{strategy_name}.csv'
    csv_path = os.path.join(UPLOAD_FOLDER, csv_robustness)
    log_df.to_csv(csv_path, index=False)

    # Sort the results list in descending order based on Portfolio Value (convert to float for correct sorting)
    sorted_results = sorted(results, key=lambda x: float(x["Portfolio Value"]), reverse=True)

    highest_result = sorted_results[0]
    exclude_keys = {"Win Rate", "Sharpe Ratio", "Max Drawdown", "IRR", "Portfolio Value"}
    best_params = {key: value for key, value in highest_result.items() if key not in exclude_keys}
    print("Best Params:", best_params)
    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    Graph = create_strategy_class(strategy_name=strategy_name, stop_logic='stop_logic')
    cerebro.addstrategy(Graph, params=best_params)
    strategy = cerebro.run()[0]

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
        "Win Rate": win_rate,
        "Sharpe Ratio": f"{sharpe_ratio:.2f}",
        "Max Drawdown": f"{max_drawdown:.2f}%",
        "IRR": f"{irr:.2f}",
    }
    end_time = time.time()
    print(f'Time Taken: {end_time - start_time}')
    return jsonify(backtest_results)

@app.route('/strategies', methods=['GET'])
def get_strategies():
    """
    Fetch all available strategies.
    """
    strategy_list = list(strategy_tree.keys())
    print(f'strategies list: {strategy_list}')
    return jsonify({"strategies": strategy_list})

@app.route('/execute-strategies', methods=['POST'])
def execute_strategies():
    start_time = time.time()
    from components.fetch_data_v2 import fetch_stock_data
    from components.run_strategy import run_strategy
    from components.save_cached_parameters import save_cached_parameters
    from components.weekly_update_checker import needs_weekly_update
    from components.daily_cycle import daily_cycle
    from components.databases import save_parameters_to_db, load_best_parameters
    data = request.json
    print(data)
    initial_portfolio_value = data.get('initial_portfolio_value', 100000)
    stock_symbol = data.get('stock_symbol', 'RELIANCE.NS')
    start_date = data.get('start_date', '2023-01-01')
    trade_size = data.get('trade_size', 30)
    interval = '1d'

    stock_data = fetch_stock_data(stock_symbol, start_date, interval)
    data_feed = bt.feeds.PandasData(dataname=stock_data)
    print(f'stock data: {stock_data}')

    master_results = [] # Initialize a master results list for all strategies

    if needs_weekly_update():
        print('🟢 Running weekly cycle...')
    
        with concurrent.futures.ProcessPoolExecutor() as excutor:
            futures = {
                excutor.submit(
                    run_strategy, strategy, trade_size, data_feed, initial_portfolio_value, stock_data, start_date
                ): strategy for strategy in strategy_tree
            }
            for future in concurrent.futures.as_completed(futures):
                backtest_results = future.result()
                master_results.append(backtest_results)

                strategy_name = backtest_results.get('Strategy Name')
                best_parameter = backtest_results.get('Best Parameters')
                portfolio_value = backtest_results.get('Portfolio Value')

                if strategy_name and best_parameter and portfolio_value:
                    save_parameters_to_db(strategy_name, best_parameter, portfolio_value)
                else:
                    print(f"⚠️ Warning: Missing values for {strategy_name}: Best Params={best_parameter}, Portfolio={portfolio_value}")

        print("✅ Weekly best parameters saved successfully.")
    else:
        print('🟢 Running daily cycle...')
        best_params = load_best_parameters()
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = {}
    
            for strategy_name in strategy_tree:
                # Get the best parameters for the current strategy
                strategy_params = best_params.get(strategy_name, {}).get("parameters", {})

                futures[executor.submit(
                    daily_cycle, strategy_name, trade_size, data_feed, initial_portfolio_value, stock_data, start_date, strategy_params
                )] = strategy_name  # Store strategy_name for reference

            for future in concurrent.futures.as_completed(futures):
                strategy_name = futures[future]  # Retrieve strategy name for debugging
                try:
                    backtest_results = future.result()
                    master_results.append(backtest_results)
                except Exception as e:
                    print(f"⚠️ Error in {strategy_name}: {e}")
    
    end_time = time.time()
    print(f'Time Taken: {end_time - start_time}')
    return jsonify(master_results)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080,debug=True)