from strategies import strategy_tree
import backtrader as bt
from datetime import timedelta

# Base Strategy Class
class BaseStrategy(bt.Strategy):
    def __init__(self, params, indicators, strategy_name):
        if strategy_name not in strategy_tree:
            raise ValueError(f"Strategy '{strategy_name}' not found.")
        strategy_data = strategy_tree[strategy_name]
        self.params = params
        self.strategy_name = strategy_name
        self.indicators = indicators

        self.order = None
        self.log_data = []
        self.buy_signals = []
        self.sell_signals = []

    def log(self, txt, dt=None):
        """Logging function for this strategy."""
        dt = dt or self.datas[0].datetime.datetime(0)
        # print(f"{dt.isoformat()} - {txt}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f"BUY EXECUTED, Price: {order.executed.price}, Size: {order.executed.size}, Portfolio Value: {self.broker.getvalue()}")
                self.log_data.append({'Date': self.datas[0].datetime.date(0) - timedelta(days=1), 'Type': 'BUY', 'Price': order.executed.price, 'Size': order.executed.size, 'Portfolio Value': self.broker.getvalue()})
            elif order.issell():
                self.log(f"SELL EXECUTED, Price: {order.executed.price}, Size: {order.executed.size}, Portfolio Value: {self.broker.getvalue()}")
                self.log_data.append({'Date': self.datas[0].datetime.date(0) - timedelta(days=1), 'Type': 'SELL', 'Price': order.executed.price, 'Size': order.executed.size, 'Portfolio Value': self.broker.getvalue()})
            self.order = None
        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log("Order Canceled/Margin/Rejected")
            self.order = None

    def next(self):
        raise NotImplementedError("The 'next' method should be implemented in the subclass.")