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
    if self.indicators["macd"][0] > self.indicators["signal"][0] and self.indicators["macd"][-1] <= self.indicators["signal"][-1] and self.indicators["macd"][0] < 0:
        self.order = self.buy(size=self.params["Trade Size"])
        self.macd_signals.append({'Date': self.datas[0].datetime.date(0), 'Type': 'BUY', 'MACD': self.indicators["macd"][0]})
    elif self.indicators["macd"][0] < self.indicators["signal"][0] and self.indicators["macd"][-1] >= self.indicators["signal"][-1] and self.position  and self.indicators["macd"][0] > 0:
        self.order = self.sell(size=self.position.size)
        self.macd_signals.append({'Date': self.datas[0].datetime.date(0), 'Type': 'SELL', 'MACD': self.indicators["macd"][0]})

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
    print(f"logged_trade_dates: {logged_trade_dates}")

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
    print(f"sell signal: {sell_signals_macd}")

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
    plt.title(f'MACD and Signal Line with Buy/Sell Signals (Slow window: {self.params["Slow Window Period"]}, Fast window: {self.params["Fast Window Period"]}, Signal window: {self.params['Signal Window Period']})')
    plt.legend()
    plt.tight_layout()
    # Save the figure to a file
    output_filename = f'macd_strategy_graph.png'
    graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
    plt.savefig(graph_path, dpi=300)
    print(f"Plot saved to {output_filename}")
    plt.close()  # Free memory