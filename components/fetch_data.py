import yfinance as yf
import os
import pandas as pd

UPLOAD_FOLDER = "stock_data"  # Folder to store downloaded stock data
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the folder exists

def fetch_stock_data(stock_symbol, start_date, interval):
    csv_path = os.path.join(UPLOAD_FOLDER, f"{stock_symbol}_{interval}.csv")
    
    # Check if file already exists
    if os.path.exists(csv_path):
        print(f"Loading data from {csv_path}")
        stock_data = pd.read_csv(csv_path, index_col=0, parse_dates=True)

        last_date = stock_data.index[-1]
        print(f'Last date in the existing data: {last_date}')
        # Get today's date
        today_date = pd.to_datetime("today").normalize()
        print(f'last date: {last_date}, today_date: {today_date}')
        if last_date < today_date:
            start_fetch_date = last_date + pd.Timedelta(days=1)
            # Download new data from the last date to the present
            print(f"Downloading new data for {stock_symbol} from {start_fetch_date} to present")
            new_data = yf.download(stock_symbol, start=last_date, interval=interval)
            # Clean and format the new data
            if not new_data.empty:
                new_data.iloc[:, 1:] = new_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
                new_data.columns = (
                    ['adj_close', 'close', 'high', 'low', 'open', 'volume'] if 'Adj Close' in new_data.columns else ['close', 'high', 'low', 'open', 'volume']
                )
                new_data.index.name = 'datetime'
            
            # Append the new data
            stock_data = pd.concat([stock_data, new_data]).drop_duplicates()
            print(f"Appended new data for {stock_symbol}")
            stock_data.to_csv(csv_path, index=True) # Save to CSV for future use
        else:
            print(f"No new data available for {stock_symbol}.")
        
    else:
        # If not, download from Yahoo Finance
        print(f"Downloading new data for {stock_symbol} with {interval} interval")
        stock_data = yf.download(stock_symbol, start=start_date, interval=interval)
        stock_data.iloc[:, 1:] = stock_data.iloc[:, 1:].apply(pd.to_numeric, errors='coerce')
        stock_data.columns = (
            ['adj_close', 'close', 'high', 'low', 'open', 'volume'] if 'Adj Close' in stock_data.columns else ['close', 'high', 'low', 'open', 'volume']
        )
        stock_data.index.name = 'datetime'
        stock_data.to_csv(csv_path, index=True) # Save to CSV for future use
    
    return stock_data