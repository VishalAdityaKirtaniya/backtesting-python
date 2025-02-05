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
macs_parameter_ranges = {
    "Long Term": range(50, 191, 10),
    "Short Term": range(10, 81, 5)
}
# MACS strategy
def macs_indicators(self):
        # Initialize moving averages
        self.short_ma = bt.indicators.SMA(self.data.close, period=self.params["Short Term"])
        self.long_ma = bt.indicators.SMA(self.data.close, period=self.params["Long Term"])

        # CrossOver indicator
        self.crossover = bt.indicators.CrossOver(self.short_ma, self.long_ma)

def macs_next_logic(self):
        
        # Buy condition: Short MA crosses above Long MA
        if self.crossover > 0:
            self.order = self.buy(size=self.params["Trade Size"])

        # Sell condition: Short MA crosses below Long MA
        elif self.crossover < 0 and self.position:
            self.order = self.sell(size=self.position.size)

def macs_stop_logic(self):
        # This method is used for visualization after the strategy finishes
        data = pd.DataFrame({
            'Close': self.data.close.array,
            'Short MA': self.short_ma.array,
            'Long MA': self.long_ma.array,
        }, index=self.data.datetime.array)
        print(data)

        data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))
        print(data.index)

        # Extract buy and sell signal data points
        buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
        sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=0.3)
        plt.plot(data.index, data['Short MA'], label=f"Short ({self.params['Short Term']}) MA", color="green", alpha=0.7, linewidth=0.7)
        # plt.plot(data.index, data['Mid Period'], label="Middle Channel", color="black", alpha=0.7, linewidth=0.3)
        plt.plot(data.index, data['Long MA'], label=f"Long ({self.params['Long Term']}) MA", color="red", alpha=0.7, linewidth=0.7)
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
        plt.title(f"Moving Average Crossover Strategy(Long Term: {self.params['Long Term']}, Short Term: {self.params['Short Term']})")
        plt.legend()
        plt.tight_layout()
        # Save the figure to a file
        output_filename = f'macs_strategy_graph.png'
        graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
        plt.savefig(graph_path, dpi=100)
        print(f"Plot saved to {output_filename}")
        plt.close()  # Free memory