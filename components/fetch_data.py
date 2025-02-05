# Download Data and Initialize Backtest
import yfinance as yf
def fetch_stock_data(stock_symbol, start_date, interval):
    stock_data = yf.download(stock_symbol, start=start_date, interval=interval)
    return stock_data