import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend
import matplotlib.pyplot as plt
import os

from components.folder_name import UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# RSI Strategy
rsi_parameter_ranges = {
    "Overbought": range(60, 91, 5),
    "Oversold": range(10, 41, 5),
    "RSI Period": range(6, 31, 3)
}

def rsi_init_logic(self):
    self.rsi_signal = []
    self.pre_buy_sell_alert = []

def rsi_indicators(self):
    self.rsi = bt.indicators.RSI(self.data.close, period=self.params["RSI Period"])

def rsi_next_logic(self):
    rsi = self.rsi[0]
    prev_rsi = self.rsi[-1]
    oversold = self.params["Oversold"]
    overbought = self.params["Overbought"]

    # Pre-Buy Alert: RSI is approaching the oversold level
    if prev_rsi > oversold and rsi <= oversold * 1.05 and rsi > oversold:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE BUY'})

    # Buy Condition: RSI crosses below the oversold threshold
    if not self.position and rsi < oversold:
        # print(f"Buy Signal: RSI ({rsi}) crossed below {oversold}")
        self.order = self.buy(size=self.params["Trade Size"])
        self.rsi_signal.append({'Date': self.datas[0].datetime.date(0), 'Type': 'BUY', 'RSI': rsi})

    # Pre-Sell Alert: RSI is approaching the overbought level
    if prev_rsi < overbought and rsi >= overbought * 0.95 and rsi < overbought:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE SELL'})

    # Sell Condition: RSI crosses above the overbought threshold
    elif self.position and rsi > overbought:
        # print(f"Sell Signal: RSI ({rsi}) crossed above {overbought}")
        self.order = self.sell(size=self.position.size)
        self.rsi_signal.append({'Date': self.datas[0].datetime.date(0), 'Type': 'SELL', 'RSI': rsi})

def rsi_stop_logic(self):
    data = pd.DataFrame({
        'Close': self.data.close.array,
        'RSI': self.rsi.array,
    }, index=self.data.datetime.array)
    # print(data)

    data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))
    # print(data.index)

    data = data.dropna(subset=['RSI'])
    logged_trade_dates = {entry['Date'] for entry in self.log_data}

    # Extract buy and sell signal data points
    buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
    sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])
    buy_signals_rsi = pd.DataFrame([
        {'Date': entry['Date'], 'RSI': entry['RSI']} 
        for entry in self.rsi_signal if entry['Type'] == 'BUY'
    ])
    sell_signals_rsi = pd.DataFrame([
        {'Date': entry['Date'], 'RSI': entry['RSI']} 
        for entry in self.rsi_signal if entry['Type'] == 'SELL'
    ])
    
    plt.figure(figsize=(12,6))

    plt.subplot(3, 1, (1, 2))
    plt.plot(data.index, data["Close"], label="Close Price", color="blue", linewidth=0.5)
    plt.scatter(buy_signals['Date'], buy_signals['Price'], label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals['Date'], sell_signals['Price'], label='Sell Signal', marker='v', color='red', alpha=1)
    plt.text(
            x=0.99,  # Use normalized coordinates (1 corresponds to the right side)
            y=0.02,  # Position near the top of the plot (1 corresponds to the top)
            s=f"Portfolio Value: {self.broker.getvalue():.2f}",
            fontsize=10,
            color="black",
            verticalalignment='bottom',
            horizontalalignment='right',
            transform=plt.gca().transAxes,  # Use axes coordinates (normalized)
            bbox=dict(boxstyle="round", facecolor="white", alpha=0.3)  # Background for visibility
        )
    plt.title(f"RSI (RSI Period: {self.params['RSI Period']}, Overbought: {self.params['Overbought']}, Oversold: {self.params['Oversold']})")
    plt.legend()

    plt.subplot(3,1,3)
    plt.plot(data.index, data["RSI"], label="RSI", color="black", linewidth=0.5)
    plt.axhline(y=self.params['Overbought'], color='orange', linestyle='--', label=f"Overbought ({self.params['Overbought']})")
    plt.axhline(y=self.params['Oversold'], color='orange', linestyle='--', label=f"Oversold ({self.params['Oversold']})")
    if not buy_signals_rsi.empty:
        plt.scatter(buy_signals_rsi['Date'], buy_signals_rsi['RSI'], label='Buy Signal', marker='^', color='green', alpha=1)
    if not sell_signals_rsi.empty:
        plt.scatter(sell_signals_rsi['Date'], sell_signals_rsi['RSI'], label='Sell Signal', marker='v', color='red', alpha=1)
    plt.legend()
    # Save the figure to a file
    output_filename = f'rsi_strategy_graph.png'
    graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
    plt.savefig(graph_path, dpi=100)
    print(f"Plot saved to {output_filename}")
    plt.close()  # Free memory