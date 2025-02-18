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

# Parabolic SAR
parabolic_sar_parameter_ranges = {
    "Maximum Acceleration Factor Period": [x / 10 for x in range(1, 11)],
    "Acceleration Factor Period": [x / 100.0 for x in range(1, 11)]
}

def parabolic_sar_init_logic(self):
    self.sar_values = []
    self.pre_buy_sell_alert = []

def parabolic_sar_indicators(self):
    self.sar = bt.indicators.ParabolicSAR(self.data, af=self.params["Acceleration Factor Period"], afmax=self.params["Maximum Acceleration Factor Period"])

def parabolic_sar_next_logic(self):
    self.sar_values.append(self.sar[0])
    price = self.data.close[0]
    prev_price = self.data.close[-1]
    sar = self.sar[0]

    # Pre-Buy Alert: Price is approaching the SAR from below
    if prev_price < sar and price > sar * 0.98 and price < sar:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE BUY'})

    # Buy Condition: Price crosses above SAR
    if not self.position:
        if price > sar:
            # print(f"Buy Signal: Price ({price}) crossed above SAR ({sar})")
            self.order = self.buy(size=self.params["Trade Size"])

    # Pre-Sell Alert: Price is approaching the SAR from above
    if prev_price > sar and price < sar * 1.02 and price > sar:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE SELL'})

    # Sell Condition: Price crosses below SAR
    elif price < sar and self.position:
        # print(f"Sell Signal: Price ({price}) crossed below SAR ({sar})")
        self.order = self.sell(size=self.position.size)

def parabolic_sar_stop_logic(self):
    data = pd.DataFrame({
        'Close': self.data.close.array,
        'Parabolic SAR': self.sar.array,
     }, index=self.data.datetime.array)
    # print(data)

    data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))
    # print(data.index)

    # data = data.dropna(subset=['Leading Span A', 'Leading SpanB'])

    # Extract buy and sell signal data points
    buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
    sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])
    
    plt.figure(figsize=(12, 6))
    plt.plot(data.index, data["Close"], label="Close Price", color="blue", linewidth=0.5)
    plt.scatter(data.index, data["Parabolic SAR"], label="Parabolic SAR", color="red", s=3, marker="o")
    plt.scatter(buy_signals['Date'], buy_signals['Price'], label='Buy Signal', marker='^', color='green', alpha=1)
    plt.scatter(sell_signals['Date'], sell_signals['Price'], label='Sell Signal', marker='v', color='red', alpha=1)
    plt.title(f"Parabolic SAR (Maximum Acceleration Factor: {self.params['Maximum Acceleration Factor Period']}, Acceleration Factor: {self.params['Acceleration Factor Period']})")
    plt.legend()
    # Save the figure to a file
    output_filename = f'parabolic_sar_strategy_graph.png'
    graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
    plt.savefig(graph_path, dpi=100)
    print(f"Plot saved to {output_filename}")
    plt.close()  # Free memory