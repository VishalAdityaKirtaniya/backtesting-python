import backtrader as bt
import pandas as pd
from datetime import datetime, timedelta
import matplotlib
matplotlib.use("Agg")  # Use non-GUI backend
import matplotlib.pyplot as plt
import numpy as np
import os

from components.folder_name import UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Define parameter ranges
macd_parameter_ranges = {
    "Slow Window Period": range(20, 51, 5),  # 20 to 50 with step of 5
    "Fast Window Period": range(5, 21, 3),  # 5 to 20 with step of 3
    "Signal Window Period": range(3, 16, 3), # 3 to 15 with step of 3
}

def macd_init_logic(self):
    self.macd_signals = []
    self.pre_buy_sell_alert = []

# Example: MACD Strategy Definition
def macd_indicators(self):
    # print(f'self.params: {self.params}')
    macd_line = bt.indicators.EMA(self.data.close, period=self.params["Fast Window Period"]) - bt.indicators.EMA(self.data.close, period=self.params["Slow Window Period"])
    signal_line = bt.indicators.EMA(macd_line, period=self.params["Signal Window Period"])
    histogram = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram
    }

def macd_next_logic(self):
    macd = self.indicators["macd"][0]
    signal = self.indicators["signal"][0]
    prev_macd = self.indicators["macd"][-1]
    prev_signal = self.indicators["signal"][-1]

    # Pre-Buy Alert: MACD is very close to crossing above the signal line
    if prev_macd < prev_signal and macd > signal * 0.98 and macd < signal:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE BUY'})

    # Buy Trigger: MACD crosses above signal line from below and is negative
    if macd > signal and prev_macd <= prev_signal and macd < 0:
        # print(f"Buy Signal: MACD ({macd}) crossed above Signal ({signal})")
        self.order = self.buy(size=self.params["Trade Size"])
        self.macd_signals.append({'Date': self.datas[0].datetime.date(0), 'Type': 'BUY', 'MACD': macd})

    # Pre-Sell Alert: MACD is very close to crossing below the signal line
    if prev_macd > prev_signal and macd < signal * 1.02 and macd > signal:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE SELL'})

    # Sell Trigger: MACD crosses below signal line from above and is positive
    elif self.position and macd < signal and prev_macd >= prev_signal and macd > 0:
        # print(f"Sell Signal: MACD ({macd}) crossed below Signal ({signal})")
        self.order = self.sell(size=self.position.size)
        self.macd_signals.append({'Date': self.datas[0].datetime.date(0), 'Type': 'SELL', 'MACD': macd})

def macd_stop_logic(self):
    # Create a DataFrame for MACD and signals
    data = pd.DataFrame({
        'Close': self.data.close.array,
        'MACD': self.indicators["macd"].array,
        'Signal': self.indicators["signal"].array,
        'Histogram': self.indicators["histogram"].array
    }, index=self.data.datetime.array)
    data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))

    data = data.dropna(subset=['MACD'])
    logged_trade_dates = {entry['Date'] for entry in self.log_data}

    # Extract buy and sell signal data points
    buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
    sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])

    buy_signals_macd = pd.DataFrame([
        {'Date': entry['Date'], 'MACD': entry['MACD']} 
        for entry in self.macd_signals if entry['Type'] == 'BUY'
    ])
    sell_signals_macd = pd.DataFrame([
        {'Date': entry['Date'], 'MACD': entry['MACD']} 
        for entry in self.macd_signals if entry['Type'] == 'SELL'
    ])
    # print(f"sell signal: {sell_signals_macd}")

    # print(f"buy signal macd: {buy_signals_macd}")
    plt.figure(figsize=(12, 6))

    # Plot stock close price
    plt.subplot(3, 1, (1, 2))
    plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=0.7)
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
    plt.title('Stock Price')
    plt.legend()

    # Plot MACD and signal line
    plt.subplot(3, 1, 3)
    plt.plot(data.index, data['MACD'], label='MACD Line', color='black', linewidth=0.7)
    plt.plot(data.index, data['Signal'], label='Signal Line', color='red', linewidth=0.7)
    plt.bar(data.index, data['Histogram'], label='Histogram', color=np.where(data['Histogram'] > 0, 'green', 'red'))
    if not buy_signals_macd.empty:
        plt.scatter(buy_signals_macd['Date'], buy_signals_macd['MACD'], label='Buy Signal', marker='^', color='green', alpha=1)
    if not sell_signals_macd.empty:
        plt.scatter(sell_signals_macd['Date'], sell_signals_macd['MACD'], label='Sell Signal', marker='v', color='red', alpha=1)
    plt.title(f"MACD and Signal Line with Buy/Sell Signals (Slow window: {self.params['Slow Window Period']}, Fast window: {self.params['Fast Window Period']}, Signal window: {self.params['Signal Window Period']})")
    plt.legend()
    plt.tight_layout()
    # Save the figure to a file
    output_filename = f'macd_strategy_graph.png'
    graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
    plt.savefig(graph_path, dpi=100)
    print(f"Plot saved to {output_filename}")
    plt.close()  # Free memory