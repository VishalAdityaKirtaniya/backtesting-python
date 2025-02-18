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

# Donchain Strategy
trend_following_parameter_ranges = {
    "High Period": range(20, 101, 5),  # 20 to 50 with step of 5
    "Lower Period": range(10, 51, 5),  # 5 to 20 with step of 3
}
def trend_following_init_logic(self):
    self.pre_buy_sell_alert = []

def trend_following_indicators(self):
    # Upper Band: Highest high over the high_period
    self.upper_band = bt.ind.Highest(self.data.high, period=self.params["High Period"])
    # Lower Band: Lowest low over the low_period
    self.lower_band = bt.ind.Lowest(self.data.low, period=self.params["Lower Period"])
    # Mid Band: Average of upper and lower bands
    self.mid_band = (self.upper_band + self.lower_band) / 2

def trend_following_next_logic(self):
        upper_band = self.upper_band[-1]
        lower_band = self.lower_band[-1]
        mid_band = self.mid_band[-1]
        close = self.data.close[0]
        close_yesterday = self.data.close[-1]

        # Pre-Buy Alert: Price is approaching the Upper Band
        if close_yesterday < upper_band and close >= upper_band * 0.98 and close < upper_band:
            self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE BUY'})

        # Buy Condition: Price crosses above the Upper Band
        if close > upper_band and close_yesterday <= upper_band: 
            # print(f"Buy Signal: Price ({close}) crossed above Upper Band ({upper_band})")
            self.order = self.buy(size=self.params["Trade Size"])

        # Pre-Sell Alert: Price is approaching the Lower Band
        if close_yesterday > lower_band and close <= lower_band * 1.02 and close > lower_band:
            self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE SELL'})

        # Sell Condition: Price crosses below the Lower Band
        elif self.position and close < lower_band and close_yesterday >= lower_band:
            # print(f"Sell Signal: Price ({close}) crossed below Lower Band ({lower_band})")
            self.order = self.sell(size=self.position.size)

def trend_following_stop_logic(self):
        # This method is used for visualization after the strategy finishes
        data = pd.DataFrame({
            'Close': self.data.close.array,
            'High Period': self.upper_band.array,
            'Mid Period': self.mid_band.array,
            'Low Period': self.lower_band.array
        }, index=self.data.datetime.array)
        # print(data)

        data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))

        # Shift the bands **to the right**
        shift_value = -1  # Adjust this as needed
        data['High Period'] = data['High Period'].shift(-shift_value)
        data['Mid Period'] = data['Mid Period'].shift(-shift_value)
        data['Low Period'] = data['Low Period'].shift(-shift_value)
        # print(data.index)

        # Extract buy and sell signal data points
        buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
        sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=0.3)
        plt.plot(data.index, data['High Period'], label=f"Upper ({self.params['High Period']}) Channel", color="green", alpha=0.7, linewidth=0.7)
        plt.plot(data.index, data['Mid Period'], label="Middle Channel", color="black", alpha=0.7, linewidth=0.3)
        plt.plot(data.index, data['Low Period'], label=f"Lower ({self.params['Lower Period']}) Channel", color="red", alpha=0.7, linewidth=0.7)
        plt.fill_between(data.index, data["High Period"], data["Low Period"], color="lightgray", alpha=0.3)  # Shade the area between bands
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
        plt.title(f"Trend Following Strategy (High Period: {self.params['High Period']}, Lower Period: {self.params['Lower Period']})")
        plt.legend()
        plt.tight_layout()
        # Save the figure to a file
        output_filename = f'trend_following_strategy_graph.png'
        graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
        plt.savefig(graph_path, dpi=100)
        print(f"Plot saved to {output_filename}")
        plt.close()  # Free memory