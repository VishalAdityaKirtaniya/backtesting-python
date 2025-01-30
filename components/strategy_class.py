from strategies import strategy_tree
import pandas as pd
import os

def create_strategy_class(strategy_name, stop_logic=None):
        from components.base_strategy import BaseStrategy
        UPLOAD_FOLDER = 'static/files'
        if strategy_name not in strategy_tree:
            raise ValueError(f"Strategy '{strategy_name}' not found in the strategy tree.")

        strategy_data = strategy_tree[strategy_name]
        """
        Dynamically create a strategy class.
        - strategy_name: Name of the strategy.
        - params: Parameters dictionary.
        - indicator_definitions: A dictionary of indicator definitions.
        - next_logic: Function implementing the 'next' method logic.
        """
        class CustomStrategy(BaseStrategy):
            def __init__(self, *args, **kwargs):
                params = kwargs.get('params', {})
                # print(f"Creating strategy with params: {params}")
                super().__init__(params=params, indicators=strategy_data["indicator_definitions"], strategy_name=strategy_name)
                # Initialize other instance attributes if needed
                # print(f"indicator defination: {indicator_definitions}")
                self.indicators = strategy_data["indicator_definitions"](self)
                # print(f"indicators: {self.indicators}")
                self.init_logic = strategy_data["init_logic"](self)
    
            def next(self):
                strategy_data["next_logic"](self)

            def stop(self):
                if stop_logic in strategy_data and strategy_data["stop_logic"]:
                    strategy_data["stop_logic"](self)
                    log_data_df = pd.DataFrame(self.log_data)
                    # print(log_df)
                    csv_trade_log = f'trade_log_{strategy_name}.csv'
                    csv_path = os.path.join(UPLOAD_FOLDER, csv_trade_log)
                    log_data_df.to_csv(csv_path, index=False)
                else:
                    print(f"Stopping {strategy_name} strategy with no custom stop logic.")

        CustomStrategy.__name__ = strategy_name
        return CustomStrategy