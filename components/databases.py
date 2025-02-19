from sqlalchemy import create_engine
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import json

# ✅ Create an SQLAlchemy engine for Pandas
def get_db_engine():
    return create_engine("mysql+mysqlconnector://vishal:vishalkvsatna@localhost/stock_market")


# ✅ Connect to the MySQL database
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="vishal",
        password="vishalkvsatna",
        database="stock_market"
    )

# ✅ Get the last available date for a stock
def get_last_date(stock_symbol):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT MAX(datetime) FROM stock_data WHERE stock_symbol = %s", (stock_symbol,))
    last_date = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return last_date

# ✅ Fetch existing stock data from the database
def fetch_stock_data_from_db(stock_symbol):
    engine = get_db_engine()
    query = "SELECT datetime, close, high, low, open, volume FROM stock_data WHERE stock_symbol = %s ORDER BY datetime"
    stock_data = pd.read_sql(query, engine, params=(stock_symbol,))
    
    if stock_data.empty:
        return None  # Return None if no data is found
    
    stock_data.set_index("datetime", inplace=True)
    return stock_data

# ✅ Insert stock data into the database
def insert_stock_data(stock_symbol, stock_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert each row of stock data
    for index, row in stock_data.iterrows():
        cursor.execute("""
            INSERT INTO stock_data (stock_symbol, datetime, close, high, low, open, volume)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE close=%s, high=%s, low=%s, open=%s, volume=%s
        """, (stock_symbol, index, row['close'], row['high'], row['low'], row['open'], row['volume'],
              row['close'], row['high'], row['low'], row['open'], row['volume']))
    
    conn.commit()
    cursor.close()
    conn.close()

def save_parameters_to_db(strategy_name, best_parameter, portfolio_value):
    conn = get_db_connection()
    cursor = conn.cursor()
    update_date = datetime.today().strftime('%Y-%m-%d')
    try:
        # Step 1: Insert or get the update_date from weekly_metadata
        cursor.execute("""
            INSERT INTO weekly_metadata (update_date)
            VALUES (%s)
            ON DUPLICATE KEY UPDATE update_date=update_date
        """, (update_date,))

        strategy_id = get_or_create_strategy(strategy_name)
        
        # Get the metadata_id of the inserted update_date (whether it's new or existing)
        cursor.execute("SELECT id FROM weekly_metadata WHERE update_date = %s", (update_date,))
        metadata_id = cursor.fetchone()[0]

        # Step 2: Insert the strategy data into weekly_parameters
        cursor.execute("""
            INSERT INTO weekly_parameters (metadata_id, strategy_id, parameters, portfolio_value)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE parameters = %s, portfolio_value = %s
        """, (metadata_id, strategy_id, json.dumps(best_parameter), portfolio_value, json.dumps(best_parameter), portfolio_value))
        
        # Commit the changes
        conn.commit()

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        # Close the connection
        cursor.close()
        conn.close()

# ✅ Fetch Latest Weekly Parameters
def fetch_weekly_parameters():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT strategy_name, parameters FROM weekly_parameters ORDER BY update_date DESC")
    best_params = {row["strategy_name"]: json.loads(row["parameters"]) for row in cursor.fetchall()}

    cursor.close()
    conn.close()
    
    return best_params

def load_best_parameters():
    try:
        # Step 1: Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 2: Get the latest update_date from the weekly_metadata table
        cursor.execute("SELECT update_date FROM weekly_metadata ORDER BY update_date DESC LIMIT 1")
        latest_update_date = cursor.fetchone()

        if not latest_update_date:
            print("⚠️ No data found in weekly_metadata.")
            return {}

        # Step 3: Get the metadata_id for the latest update_date
        cursor.execute("SELECT id FROM weekly_metadata WHERE update_date = %s", (latest_update_date[0],))
        metadata_id = cursor.fetchone()[0]

        # Step 4: Get the strategy parameters from the weekly_parameters table based on metadata_id
        cursor.execute("""
            SELECT sl.name AS strategy_name, wp.parameters, wp.portfolio_value 
            FROM weekly_parameters wp
            JOIN strategy_list sl ON wp.strategy_id = sl.id  -- Join to get strategy names
            WHERE wp.metadata_id = %s
        """, (metadata_id,))

        # Fetch all strategy parameters
        best_parameters = {}
        for row in cursor.fetchall():
            strategy_name = row[0]
            parameters = json.loads(row[1])  # The parameters are stored as JSON
            portfolio_value = row[2]
            best_parameters[strategy_name] = {
                "parameters": parameters,
                "portfolio_value": portfolio_value
            }

        # Close the database connection
        cursor.close()
        conn.close()

        return best_parameters

    except mysql.connector.Error as err:
        print(f"⚠️ Error while loading parameters from DB: {err}")
        return {}
    
def needs_weekly_update():
    try:
        # Step 1: Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        # Step 2: Get the latest update_date from the weekly_metadata table
        cursor.execute("SELECT update_date FROM weekly_metadata ORDER BY update_date DESC LIMIT 1")
        latest_update_date = cursor.fetchone()

        # Step 3: Check if there is a valid update_date in the database
        if not latest_update_date:
            print("⚠️ No update date found in weekly_metadata, running weekly update.")
            return True  # If no data found, run weekly update
        
        # Step 4: Compare the latest update_date with the current date
        last_update = latest_update_date[0]
        if last_update < (datetime.today() - timedelta(days=7)).date():
            return True  # Run weekly update if the last update was more than 7 days ago
        
        # No update needed if the last update is within the past 7 days
        return False
    
    except mysql.connector.Error as err:
        print(f"⚠️ Error while checking weekly update status: {err}")
        return True  # In case of any error, default to running the weekly update
    
    finally:
        # Step 5: Close the database connection
        cursor.close()
        conn.close()

def get_or_create_strategy(strategy_name):
    """Gets the strategy ID if it exists, otherwise inserts and returns the new ID."""
    conn = get_db_connection()  # Connect to database
    cursor = conn.cursor()

    # Check if strategy exists
    cursor.execute("SELECT id FROM strategy_list WHERE name = %s", (strategy_name,))
    result = cursor.fetchone()

    if result:
        strategy_id = result[0]
    else:
        # Insert new strategy and get its ID
        cursor.execute("INSERT INTO strategy_list (name) VALUES (%s)", (strategy_name,))
        strategy_id = cursor.lastrowid  # Get the ID of the new strategy
        conn.commit()

    conn.close()
    return strategy_id  # Return strategy ID

def insert_trade_logs(strategy_name, log_data):
    """
    Inserts multiple trade logs into the trade_logs table.
    
    Parameters:
    - strategy_name (str): Name of the trading strategy.
    - log_data (list of dict): List of trade logs with keys ['Date', 'Type', 'Price', 'Size', 'Portfolio Value'].
    """
    if not log_data:
        print("⚠️ No trade logs to insert.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get or create the strategy ID
        strategy_id = get_or_create_strategy(strategy_name)

        # Define the table name dynamically
        table_name = f"trade_logs_{strategy_name}"  # Replace spaces with underscores

        # Create table only if it doesn't exist
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                trade_date DATE NOT NULL,
                trade_type ENUM('BUY', 'SELL') NOT NULL,
                price DECIMAL(10, 2) NOT NULL,
                size INT NOT NULL,
                portfolio_value DECIMAL(15, 2) NOT NULL
            )
        """)
        conn.commit()

        # Prepare the data for bulk insertion
        trade_values = [
            (trade['Date'], trade['Type'], trade['Price'], trade['Size'], trade['Portfolio Value'])
            for trade in log_data
        ]

        # Bulk insert trade logs
        cursor.executemany(f"""
            INSERT INTO `{table_name}` (trade_date, trade_type, price, size, portfolio_value)
            VALUES (%s, %s, %s, %s, %s)
        """, trade_values)

        # Commit the transaction
        conn.commit()
        print(f"✅ {len(trade_values)} trade logs inserted successfully for strategy: {strategy_name}")

    except mysql.connector.Error as err:
        print(f"⚠️ Error inserting trade logs: {err}")
        conn.rollback()

    finally:
        cursor.close()
        conn.close()
