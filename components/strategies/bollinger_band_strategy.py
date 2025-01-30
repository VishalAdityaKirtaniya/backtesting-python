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

# Bollinger Bands Strategy
bollingerband_parameter_ranges = {
"Window Period": range(10, 31, 2),  # 10 to 30 with step of 2
"Devfactor": [1 + i * 0.25 for i in range(9)]  # 1.0 to 3.0 with step of 0.25
}
def bollingerband_indicators(self):
    # Initialize Bollinger Bands indicator
    self.bb = bt.indicators.BollingerBands(period=self.params["Window Period"], devfactor=self.params["Devfactor"])  # Use Backtrader's Bollinger Bands

def bollingerband_init_logic(self):
    self.upper_band = []  # List for upper band values
    self.lower_band = []  # List for lower band values

def bollingerband_next_logic(self):
        upper_band = self.bb.lines.top[0]  # Get the upper band value
        lower_band = self.bb.lines.bot[0]  # Get the lower band value
        close = self.data.close[0]

        # Store Bollinger Band values for plotting
        self.upper_band.append(upper_band)  # Save upper band value
        self.lower_band.append(lower_band)  # Save lower band value

        # Buy for the first time if not in position and price crosses above upper band
        if close < lower_band: 
            self.order = self.buy(size=self.params["Trade Size"])

        # After the first buy, check if price goes below upper band and then back up above it
        # if self.data.close[-1] < self.upper_band[-1] and self.data.close[0] > self.upper_band[0]:
        #     self.order = self.buy(size=self.params.trade_size)

        # Optional Sell logic: Sell if price drops below the lower band
        elif self.position and close > upper_band:
            self.order = self.sell(size=self.position.size)

def bollingerband_stop_logic(self):
        # This method is used for visualization after the strategy finishes
        print(f"Upper band: {self.bb.lines.top.array}")
        data = pd.DataFrame({
            'Close': self.data.close.array,
            'Upper Band': self.bb.lines.top.array,
            'Lower Band': self.bb.lines.bot.array
        }, index=self.data.datetime.array)
        print(f"before line 203: {data.index}")
        data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))
        print(f"after line 203: {data.index}")

        # Extract buy and sell signal data points
        buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
        sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=0.3)
        plt.plot(data.index, data['Upper Band'], label=f"Upper Band", color="green", alpha=0.7, linewidth=0.7)
        # plt.plot(data.index, data['Mid Period'], label="Middle Channel", color="black", alpha=0.7, linewidth=0.3)
        plt.plot(data.index, data['Lower Band'], label=f"Lower Band", color="red", alpha=0.7, linewidth=0.7)
        plt.scatter(buy_signals['Date'], buy_signals['Price'], label='Buy Signal', marker='^', color='green', alpha=1)
        plt.scatter(sell_signals['Date'], sell_signals['Price'], label='Sell Signal', marker='v', color='red', alpha=1)
        plt.fill_between(data.index, data["Upper Band"], data["Lower Band"], color="lightgray", alpha=0.3)  # Shade the area between bands

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
        plt.title(f'Bollinger Band Strategy (Window Period: {self.params["Window Period"]}, Devfactor: {self.params["Devfactor"]})')
        plt.legend()
        plt.tight_layout()
        # Save the figure to a file
        output_filename = f'bollinger_band_strategy_graph.png'
        graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
        plt.savefig(graph_path, dpi=300)
        print(f"Plot saved to {output_filename}")
        plt.close()  # Free memory