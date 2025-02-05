import pandas as pd
import numpy as np


def calculate_portfolio_value(order_log_file, date_str, stock_data, cash_flows, initial_portfolio_value):
    # Initialize variables for tracking cash and shares
    cash = initial_portfolio_value
    shares_owned = 0
    
    # Convert peak_date to a datetime object to compare with order dates
    target_date = pd.to_datetime(date_str)
    
    # Iterate over each order in the order log and     filter trades before the peak date
    for order in order_log_file:
        order_date = pd.to_datetime(order['Date'])
        # Process the order only if the order is before or on the peak date
        if order_date <= target_date:
            order_type = order['Type']
            price = float(order['Price'])
            size = int(order['Size'])
            
             # Adjust cash and shares based on the order type
            if order_type == 'BUY':
                cash -= price * size  # Decrease cash when buying
                shares_owned += size  # Increase shares when buying
            elif order_type == 'SELL':
                cash += price * shares_owned  # Increase cash when selling
                shares_owned = 0  # Decrease shares when selling
        
        # After processing orders, ensure price is defined
    if 'price' not in locals():
        # Fetch the price from stock data on the target date
        if target_date in stock_data.index:
            price = stock_data.loc[target_date, 'close']
        else:
            raise ValueError(f"Price data for target date {target_date} is not available.")

        # After each trade, calculate the current portfolio value and append to cash_flows
        portfolio_value = cash + (shares_owned * price)  # Cash + value of owned shares
        cash_flows.append(portfolio_value)  # Append the updated portfolio value to cash flows
    
    # Get the final portfolio value (after the last order)
    final_portfolio_value = cash + (shares_owned * stock_data['close'].iloc[-1])
    cash_flows.append(final_portfolio_value)  # Append final portfolio value to cash flows
    
    # Now, find the price of the stock at the peak date
    target_date_data = stock_data[stock_data.index == target_date]
    
    if not target_date_data.empty:
        peak_price = target_date_data['close'].iloc[0]
        portfolio_value_at_target = cash + (shares_owned * peak_price)
        return portfolio_value_at_target
    else:
        return None

    # Calculate performance metrics
def calculate_metrics(strategy, initial_portfolio_value, final_portfolio_value, stock_data, cash_flows):

    # Extract portfolio values and returns
    portfolio_values = final_portfolio_value
    risk_free_rate = 0.055
    stock_data['Returns'] = stock_data['close'].pct_change()
    std_dev = stock_data['Returns'].std() * np.sqrt(252)  # Annualized std dev
    # print("standard deviation: ", f"{std_dev:.4f}%")
    mean_portfolio_return = (portfolio_values - initial_portfolio_value) / initial_portfolio_value * 100
    # print('Mean Portfolio Return: ', f"{mean_portfolio_return:.2f}%")
    sharpe_ratio = (mean_portfolio_return - risk_free_rate) / std_dev
    # print("sharpe ratio: ", f"{sharpe_ratio:.2f}")

    # Win Rate
    # Initialize variables
    total_winning_shares = 0
    total_shares_traded = 0

    # Iterate through order logs to find buy and sell sequences
    buy_orders = []
    for log in strategy.log_data:
        if log["Type"] == "BUY":
            buy_orders.append(log)  # Store buy orders
            total_shares_traded += abs(log["Size"])
        elif log["Type"] == "SELL" and buy_orders:
            # Calculate the average buy price
            total_buy_cost = sum(buy["Price"] * buy["Size"] for buy in buy_orders)
            # print('total_buy_cost: ', total_buy_cost)
            total_buy_quantity = sum(buy["Size"] for buy in buy_orders)
            # print('total_buy_quantity: ', total_buy_quantity)
            average_buy_price = total_buy_cost / total_buy_quantity if total_buy_quantity > 0 else 0

            shares_sold = abs(log["Size"])  # Convert negative size to positive
            # Compare the sell price to the average buy price
            if log["Price"] > average_buy_price:
                total_winning_shares += shares_sold
            
            buy_orders = []
    # print('wins: ', total_winning_shares)
    # print('total: ', total_shares_traded)

# Calculate the win rate
    if total_shares_traded > 0 or total_winning_shares >0:
        win_rate = total_winning_shares / total_shares_traded * 100
        win_rate_output = f"{win_rate:.2f}%"
    else:
        win_rate_output = "No Trades"

    # Max DrawDown
    close_price = stock_data['close']
    # Get the dates corresponding to peak and trough
    peak_date = close_price.idxmax()  # Date of the peak value
    trough_date = close_price.idxmin()  # Date of the trough value
    # peak_date_str = peak_date.strftime('%Y-%m-%d') # Convert peak date to string for comparison
    # trough_date_str = trough_date.strftime('%Y-%m-%d') # Convert trough date to string for comparison
    portfolio_value_at_peak = calculate_portfolio_value(strategy.log_data, peak_date, stock_data, cash_flows, initial_portfolio_value=initial_portfolio_value)
    portfolio_value_at_trough = calculate_portfolio_value(strategy.log_data, trough_date, stock_data, cash_flows, initial_portfolio_value=initial_portfolio_value)
    # print('portfolio value at peak: ',portfolio_value_at_peak)
    # print('portfolio value at trough: ',portfolio_value_at_trough)

    max_drawdown = (portfolio_value_at_peak - portfolio_value_at_trough) / portfolio_value_at_peak * 100 # calculation of     Max DrawDown

    return win_rate_output, sharpe_ratio, max_drawdown

def calculate_cash_flows(order_log_file, initial_value, stock_data):
    cash_flows = [-initial_value]
    cash = initial_value  # Initialize cash as the initial portfolio value
    shares_owned = 0  # Initialize the number of shares owned

    # Iterate over the orders and calculate cash flows
    for order in order_log_file:
        order_date = pd.to_datetime(order['Date'])
        order_type = order['Type']
        price = float(order['Price'])
        size = int(order['Size'])

        # Calculate the portfolio value at the time of the trade
        if order_type == 'BUY':
            cash -= price * size  # Decrease cash when buying shares
            shares_owned += size  # Increase shares owned
        elif order_type == 'SELL':
            cash += price * shares_owned  # Increase cash when selling shares
            shares_owned = 0  # Decrease shares owned
        
        # After each trade, calculate the current portfolio value and append to cash_flows
        portfolio_value = cash + (shares_owned * price)  # Cash + value of owned shares
        cash_flows.append(portfolio_value)  # Append the updated portfolio value to cash flows
    
    # Get the final portfolio value (after the last order)
    final_portfolio_value = cash + (shares_owned * stock_data['close'].iloc[-1])
    cash_flows.append(final_portfolio_value)  # Append final portfolio value to cash flows
    # print(f"Cash flow internal: {cash_flows}")
        
    return cash_flows