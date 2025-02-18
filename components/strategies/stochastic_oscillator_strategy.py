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

# Stochastic Strategy
stochastic_parameter_ranges = {
    "Stochastic Oscillator Period": range(5, 23, 4),
    "Signal Period": range(3, 8, 2),
    "Overbought": range(70, 91, 4),
    "Oversold": range(10, 31, 4)
}

def stochastic_init_logic(self):
    self.stochastic_buy = []
    self.stochastic_sell = []
    self.stochastic_line = []
    self.signal_line = []
    self.pre_buy_sell_alert = []


def stochastic_indicators(self):
    # Add Stochastic indicator
     self.stochastic = bt.indicators.Stochastic(
        self.data,
        period=self.params["Stochastic Oscillator Period"],
        period_dfast=self.params['Signal Period']
    )
     
def stochastic_next_logic(self):
    stochastic_line = self.stochastic.percK[0]
    signal_line = self.stochastic.percD[0]
    prev_stochastic = self.stochastic.percK[-1]
    prev_signal = self.stochastic.percD[-1]
    
    oversold = self.params['Oversold']
    overbought = self.params['Overbought']
    
    self.stochastic_line.append(stochastic_line)
    self.signal_line.append(signal_line)

    # Pre-Buy Alert: %K is approaching the oversold level
    if prev_stochastic > oversold and stochastic_line <= oversold * 1.05 and stochastic_line > oversold:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE BUY'})

    # Buy Signal: %K crosses above %D in the oversold region
    if stochastic_line > signal_line and stochastic_line < oversold and prev_stochastic < prev_signal:
        # print(f"Buy Signal: Stochastic %K ({stochastic_line}) crossed above %D in the Oversold region")
        self.order = self.buy(size=self.params["Trade Size"])
        self.stochastic_buy.append({
            'Date': self.datas[0].datetime.date(0), 
            'Type': 'BUY', 
            'Stochastic': stochastic_line
        })

    # Pre-Sell Alert: %K is approaching the overbought level
    if prev_stochastic < overbought and stochastic_line >= overbought * 0.95 and stochastic_line < overbought:
        self.pre_buy_sell_alert.append({'Date': self.datas[0].datetime.date(0), 'Type': 'PRE SELL'})

    # Sell Signal: %K crosses below %D in the overbought region
    elif stochastic_line < signal_line and stochastic_line > overbought and prev_stochastic > prev_signal:
        # print(f"Sell Signal: Stochastic %K ({stochastic_line}) crossed below %D in the Overbought region")
        self.order = self.sell(size=self.position.size)
        self.stochastic_sell.append({
            'Date': self.datas[0].datetime.date(0), 
            'Type': 'SELL',
            'Stochastic': stochastic_line
        })

def stochastic_stop_logic(self):
    data = pd.DataFrame({
        'Close': self.data.close.array,
        'Stochastic Line': self.stochastic.percK.array,
        'Signal Line': self.stochastic.percD.array,
    }, index=self.data.datetime.array)
    data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))

    data = data.dropna(subset=['Stochastic Line', 'Signal Line'])

    logged_trade_dates = {entry['Date'] for entry in self.log_data}
    # Extract buy and sell signal data points
    buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
    sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])
    # print(f'self.stochastic_sell: {self.stochastic_sell}')
    buy_signals_stochastic = pd.DataFrame([
        {'Date': entry['Date'], 'Stochastic': entry['Stochastic']} 
        for entry in self.stochastic_buy if entry['Type'] == 'BUY' and entry['Date'] in logged_trade_dates
    ])
    sell_signals_stochastic = pd.DataFrame([
        {'Date': entry['Date'], 'Stochastic': entry['Stochastic']} 
        for entry in self.stochastic_sell if entry['Type'] == 'SELL' and entry['Date'] in logged_trade_dates
    ])

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

    plt.subplot(3, 1, 3)
    plt.plot(data.index, data['Stochastic Line'], label='Stochastic Line', color='black', linewidth=0.7)
    plt.plot(data.index, data['Signal Line'], label='Signal Line', color='red', linewidth=0.7)
    plt.axhline(y=self.params['Overbought'], color='orange', linestyle='--', label=f"Overbought ({self.params['Overbought']})")
    plt.axhline(y=self.params['Oversold'], color='orange', linestyle='--', label=f"Oversold ({self.params['Oversold']})")
    plt.axhspan(
        self.params['Oversold'], self.params['Overbought'], 
        color='grey', alpha=0.3
    )

    if not buy_signals_stochastic.empty:
        plt.scatter(buy_signals_stochastic['Date'], buy_signals_stochastic['Stochastic'], label='Buy Signal', marker='^', color='green', alpha=1)
    if not sell_signals_stochastic.empty:
        plt.scatter(sell_signals_stochastic['Date'], sell_signals_stochastic['Stochastic'], label='Sell Signal', marker='v', color='red', alpha=1)
    plt.legend()

    plt.title(f"Stochastic Oscillator Strategy, (Stochastic Period: {self.params['Stochastic Oscillator Period']}, Signal Period: {self.params['Signal Period']}, Overbought: {self.params['Overbought']}, Oversold: {self.params['Oversold']})")
    plt.legend()

    plt.tight_layout()
    # Save the figure to a file
    output_filename = f'stochastic_strategy_graph.png'
    graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
    plt.savefig(graph_path, dpi=100)
    print(f"Plot saved to {output_filename}")
    plt.close()  # Free memory