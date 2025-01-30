import backtrader as bt
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy_financial as npf
from strategies import strategy_tree
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from components.folder_name import UPLOAD_FOLDER
import base64

app = Flask(__name__)

CORS(app) # Enable CORS for all routes

# Ensure the directory for saving files exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/backtest', methods=['POST'])
def backtest():
    from components.strategy_class import create_strategy_class
    from components.fetch_data import fetch_stock_data
    from components.formulas import calculate_metrics, calculate_cash_flows
    from components.parameter_combinations import get_parameter_combinations
    data = request.json
    print(data)
    strategy_name = data.get('strategy_name', 'macd')
    initial_portfolio_value = data.get('initial_portfolio_value', 100000)
    stock_symbol = data.get('stock_symbol', 'RELIANCE.NS')
    start_date = data.get('start_date', '2023-01-01')
    trade_size = data.get('trade_size', 30)
    interval = '1d'

    # Create MACD Strategy Class
    Strategy = create_strategy_class(strategy_name=strategy_name)

    # Fetch stock data and interval
    stock_data, interval = fetch_stock_data(stock_symbol, start_date, interval)
    # stock_data = yf.download("RELIANCE.NS", start="2023-01-01")
    stock_data.columns = stock_data.columns.droplevel(0)  # Remove multi-index column level
    stock_data.columns = ['close', 'high', 'low', 'open', 'volume']
    stock_data.index.name = 'datetime'
    data_feed = bt.feeds.PandasData(dataname=stock_data)
    print(f'stock data: {stock_data}')

    results = []

    param_names, param_combinations = get_parameter_combinations(strategy_name)

    # Loop through combinations
    for combination in param_combinations:
        params = dict(zip(param_names, combination))
        params["Trade Size"] = trade_size
        # Dynamically extract the parameter values from the params dictionary
        # This assumes all parameter names follow the same structure
        # For instance, if 3 parameters, they are dynamically unpacked
        parameter_values = [params[param] for param in param_names]
        print(f'parameter values: {parameter_values}')
    
        # Skip invalid configurations (for example: if slow < fast, skip)
        if parameter_values[0] <= parameter_values[1]:
            print(f"Skipping invalid combination: {params}")
            continue
    
        # Print the current parameter configuration
        # print(f"Running with parameters: {params}")
    
        # Initialize Cerebro engine
        cerebro = bt.Cerebro()
        cerebro.adddata(data_feed)  # Add data feed to Cerebro
        cerebro.broker.setcash(initial_portfolio_value)  # Set initial portfolio value
        cerebro.addstrategy(Strategy, params=params)
        # print(MACDStrategy)
    
        # print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
        strategy = cerebro.run()[0]  # Run the strategy
        final_portfolio_value = cerebro.broker.getvalue()
        # print(f"Ending Portfolio Value: {final_portfolio_value:.2f}")
    
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
        results.append({
            **params,  # Include parameter values in results
            "Win Rate": win_rate,
            "Sharpe Ratio": f"{sharpe_ratio:.2f}",
            "Max Drawdown": f"{max_drawdown:.2f}%",
            "IRR": f"{irr:.2f}",
            "Portfolio Value": f"{final_portfolio_value:.2f}",
        })

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
    filtered_params = {key: value for key, value in highest_result.items() if key not in exclude_keys}

    # Extract the params used for the highest portfolio value
    best_params = filtered_params
    print("Best Params:", best_params)

    Graph = create_strategy_class(strategy_name=strategy_name, stop_logic='stop_logic')

    cerebro = bt.Cerebro()
    cerebro.adddata(data_feed)
    cerebro.broker.setcash(initial_portfolio_value)
    cerebro.addstrategy(Graph, params=filtered_params)
    strategy = cerebro.run()[0]

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
    from components.strategy_class import create_strategy_class
    from components.fetch_data import fetch_stock_data
    from components.formulas import calculate_metrics, calculate_cash_flows
    from components.parameter_combinations import get_parameter_combinations
    data = request.json
    print(data)
    strategy_list = list(strategy_tree.keys())
    initial_portfolio_value = data.get('initial_portfolio_value', 100000)
    stock_symbol = data.get('stock_symbol', 'RELIANCE.NS')
    start_date = data.get('start_date', '2023-01-01')
    trade_size = data.get('trade_size', 30)
    interval = '1d'

    stock_data, interval = fetch_stock_data(stock_symbol, start_date, interval)
    # stock_data = yf.download("RELIANCE.NS", start="2023-01-01")
    stock_data.columns = ['open', 'high', 'low', 'close', 'volume']
    stock_data.index.name = 'datetime'
    data_feed = bt.feeds.PandasData(dataname=stock_data)
    print(f'stock data: {stock_data}')

    master_results = [] # Initialize a master results list for all strategies

    for strategy_name in strategy_list:
        print(f"Running backtest for strategy: {strategy_name}")
        results = []
        param_names, param_combinations = get_parameter_combinations(strategy_name)
        # Loop through combinations
        for combination in param_combinations:
            params = dict(zip(param_names, combination))
            params["Trade Size"] = trade_size
            # Dynamically extract the parameter values from the params dictionary
            # This assumes all parameter names follow the same structure
            # For instance, if 3 parameters, they are dynamically unpacked
            parameter_values = [params[param] for param in param_names]
            print(f'parameter values: {parameter_values}')
    
            # Skip invalid configurations (for example: if slow < fast, skip)
            if parameter_values[0] <= parameter_values[1]:
                print(f"Skipping invalid combination: {params}")
                continue
    
            # Print the current parameter configuration
            # print(f"Running with parameters: {params}")
    
            # Initialize Cerebro engine
            cerebro = bt.Cerebro()
            cerebro.adddata(data_feed)  # Add data feed to Cerebro
            cerebro.broker.setcash(initial_portfolio_value)  # Set initial portfolio value
            # Create MACD Strategy Class
            Strategy = create_strategy_class(strategy_name=strategy_name)
            cerebro.addstrategy(Strategy, params=params)
            # print(MACDStrategy)
    
            # print(f"Starting Portfolio Value: {cerebro.broker.getvalue():.2f}")
            strategy = cerebro.run()[0]  # Run the strategy
            final_portfolio_value = cerebro.broker.getvalue()
            # print(f"Ending Portfolio Value: {final_portfolio_value:.2f}")
    
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
            results.append({
                **params,  # Include parameter values in results
                "Win Rate": win_rate,
                "Sharpe Ratio": f"{sharpe_ratio:.2f}",
                "Max Drawdown": f"{max_drawdown:.2f}%",
                "IRR": f"{irr:.2f}",
                "Portfolio Value": f"{final_portfolio_value:.2f}",
            })

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
        filtered_params = {key: value for key, value in highest_result.items() if key not in exclude_keys}

        # Extract the params used for the highest portfolio value
        best_params = filtered_params
        print("Best Params:", best_params)

        Graph = create_strategy_class(strategy_name=strategy_name, stop_logic='stop_logic')

        cerebro = bt.Cerebro()
        cerebro.adddata(data_feed)
        cerebro.broker.setcash(initial_portfolio_value)
        cerebro.addstrategy(Graph, params=filtered_params)
        strategy = cerebro.run()[0]

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
        master_results.append(backtest_results)

    return jsonify(master_results)

if __name__ == "__main__":
    app.run(debug=True, port=8080)