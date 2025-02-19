import yfinance as yf
import pandas as pd
from components.databases import get_last_date, insert_stock_data, fetch_stock_data_from_db

def fetch_stock_data(stock_symbol, start_date, interval):
    """
    Fetches stock data for a given stock symbol.
    If the data is already up to date, it returns the existing data.
    Otherwise, it fetches new data from yFinance and stores it in the database.
    """

    # ✅ Check the latest date in the database for this stock
    last_date = get_last_date(stock_symbol)

    if last_date:
        today_date = pd.to_datetime("today").normalize()
        print(f'today_date: {today_date}')

        # ✅ If data is already up-to-date, return existing data
        if last_date >= today_date:
            print(f'last_date : {last_date}')
            print(f"Stock data for {stock_symbol} is already up-to-date.")
            return fetch_stock_data_from_db(stock_symbol)  # Fetch from the database

        # ✅ If data is outdated, fetch only new records
        start_fetch_date = last_date + pd.Timedelta(days=1)
        print(f'start_fetch-date : {start_fetch_date}')
        print(f"Fetching new data for {stock_symbol} from {start_fetch_date} onwards")
    else:
        # ✅ If no data exists, fetch from the given start_date
        start_fetch_date = start_date
        print(f"Downloading full data for {stock_symbol} from {start_fetch_date}")

    # ✅ Fetch stock data from Yahoo Finance
    stock_data = yf.download(stock_symbol, start=start_fetch_date, interval=interval)

    if not stock_data.empty:
        stock_data.iloc[:, 1:] = stock_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        
        # ✅ Ensure 'Adj Close' is removed
        stock_data.columns = (
            ['adj_close', 'close', 'high', 'low', 'open', 'volume']
            if 'Adj Close' in stock_data.columns else ['close', 'high', 'low', 'open', 'volume']
        )
        stock_data.index.name = 'datetime'

        # ✅ Drop 'adj_close' column if it exists
        stock_data.drop(columns=['adj_close'], errors='ignore', inplace=True)

        # ✅ Insert the new data into the database
        insert_stock_data(stock_symbol, stock_data)

    return fetch_stock_data_from_db(stock_symbol)  # Always return the full data from DB
