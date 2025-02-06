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

# Ichimoku Clouds Strategy
ichimoku_parameter_ranges = {
     "Base Line Period": range(20, 41, 4),
     "Conversion Line Period": range(5, 16, 2),
     "Leading Span B Period": range(40, 100, 10)
}
def ichimoku_indicators(self):
        high = self.data.high
        low = self.data.low
        close = self.data.close

        # Tenkan-sen (Conversion Line)
        self.lines.conversion_line = (bt.indicators.Highest(high, period=self.params["Conversion Line Period"]) +
                                 bt.indicators.Lowest(low, period=self.params["Conversion Line Period"])) / 2

        # Kijun-sen (Base Line)
        self.lines.base_line = (bt.indicators.Highest(high, period=self.params["Base Line Period"]) +
                                bt.indicators.Lowest(low, period=self.params["Base Line Period"])) / 2

        # Senkou Span A (Leading Span A)
        self.lines.leading_span_a = (self.lines.conversion_line + self.lines.base_line) / 2

        # Senkou Span B (Leading Span B)
        self.lines.leading_span_b = (bt.indicators.Highest(high, period=self.params["Leading Span B Period"]) +
                                    bt.indicators.Lowest(low, period=self.params["Leading Span B Period"])) / 2

def ichimoku_next_logic(self):
        # Buy if price is above Senkou Span A and Senkou Span B
        if self.data.close[0] > self.lines.leading_span_a[0] and self.data.close[0] > self.lines.leading_span_b[0]:
            if not self.position:
                self.order = self.buy(size=self.params["Trade Size"])
        # Sell if price is below Senkou Span A and Senkou Span B
        elif self.data.close[0] < self.lines.leading_span_a[0] and self.data.close[0] < self.lines.leading_span_b[0]:
            if self.position:
                self.order = self.sell(size=self.position.size)

def ichimoku_stop_logic(self):
        # This method is used for visualization after the strategy finishes
        data = pd.DataFrame({
            'Close': self.data.close.array,
            'Conversion Line': self.lines.conversion_line.array,
            'Base Line': self.lines.base_line.array,
            'Leading Span A': self.lines.leading_span_a.array,
            'Leading Span B': self.lines.leading_span_b.array,
        }, index=self.data.datetime.array)
        # print(data)

        data.index = pd.to_datetime(data.index.map(lambda x: datetime.fromordinal(int(x)) + timedelta(days=x % 1)))
        # print(data.index)

        data = data.dropna(subset=['Leading Span A', 'Leading Span B'])

        # Extract buy and sell signal data points
        buy_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'BUY'], columns=['Date', 'Price', 'Type'])
        sell_signals = pd.DataFrame([entry for entry in self.log_data if entry['Type'] == 'SELL'], columns=['Date', 'Price', 'Type'])

        plt.figure(figsize=(12, 6))
        plt.plot(data.index, data['Close'], label='Close Price', color='blue', linewidth=0.9)
        # plt.plot(data.index, data['Conversion Line'], label=f"Conversion Line", color="black", alpha=0.7, linewidth=0.6)
        # plt.plot(data.index, data['Mid Period'], label="Middle Channel", color="black", alpha=0.7, linewidth=0.3)
        # plt.plot(data.index, data['Base Line'], label=f"Base Line", color="yellow", alpha=0.7, linewidth=0.6)
        plt.plot(data.index, data['Leading Span A'], label=f"Leading Span A", color="green", alpha=0.7, linewidth=0.7)
        plt.plot(data.index, data['Leading Span B'], label=f"Leading Span B", color="red", alpha=0.7, linewidth=0.7)

        # Dynamic fill between Leading Span A and B
        greater = data['Leading Span A'] > data['Leading Span B']
        less_equal = ~greater

        # Fill green where Span A > Span B
        plt.fill_between(
            data.index,
            data["Leading Span A"],
            data["Leading Span B"],
            where=greater,
            color="green",
            alpha=0.3,
            interpolate=True
        )
        # Fill red where Span A <= Span B
        plt.fill_between(
            data.index,
            data["Leading Span A"],
            data["Leading Span B"],
            where=less_equal,
            color="red",
            alpha=0.3,
            interpolate=True
        )

        plt.scatter(buy_signals['Date'], buy_signals['Price'], label='Buy Signal', marker='^', color='green', alpha=0.6)
        plt.scatter(sell_signals['Date'], sell_signals['Price'], label='Sell Signal', marker='v', color='red', alpha=0.6)
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
        plt.title(f"Ichimoku Clouds Strategy (Base Line: {self.params['Base Line Period']}, Conversion Line: {self.params['Conversion Line Period']}, Leading Span B: {self.params['Leading Span B Period']})")
        plt.legend()
        plt.tight_layout()
        # Save the figure to a file
        output_filename = f'ichimoku_clouds_strategy_graph.png'
        graph_path = os.path.join(UPLOAD_FOLDER, output_filename)
        plt.savefig(graph_path, dpi=100)
        print(f"Plot saved to {output_filename}")
        plt.close()  # Free memory