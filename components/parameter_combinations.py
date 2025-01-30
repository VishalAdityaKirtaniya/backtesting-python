from strategies import strategy_tree
import itertools
def get_parameter_combinations(strategy_name):
        if strategy_name in strategy_tree:
            parameter_ranges = strategy_tree[strategy_name]["parameter_ranges"]
            param_names = list(parameter_ranges.keys())
            param_values = list(parameter_ranges.values())
            param_combinations = itertools.product(*param_values)
            return param_names, param_combinations
        else:
            raise ValueError(f"Strategy {strategy_name} not found in configurations.")