from components.strategies.rsi_strategy import rsi_parameter_ranges, rsi_init_logic, rsi_indicators, rsi_next_logic, rsi_stop_logic
from components.strategies.stochastic_oscillator_strategy import stochastic_parameter_ranges, stochastic_indicators, stochastic_init_logic, stochastic_next_logic, stochastic_stop_logic
from components.strategies.bollinger_band_strategy import bollingerband_parameter_ranges, bollingerband_indicators, bollingerband_init_logic, bollingerband_next_logic, bollingerband_stop_logic
from components.strategies.macd_strategy import macd_parameter_ranges, macd_indicators, macd_init_logic, macd_next_logic, macd_stop_logic
from components.strategies.trend_following_strategy import trend_following_indicators, trend_following_next_logic,trend_following_parameter_ranges,trend_following_stop_logic, trend_following_init_logic
from components.strategies.ichimoku_strategy import ichimoku_parameter_ranges, ichimoku_indicators, ichimoku_next_logic, ichimoku_stop_logic, ichimoku_init_logic
from components.strategies.parabolic_sar_strategy import parabolic_sar_parameter_ranges, parabolic_sar_indicators, parabolic_sar_init_logic, parabolic_sar_next_logic, parabolic_sar_stop_logic
from components.strategies.macs_strategy import macs_parameter_ranges, macs_init_logic, macs_indicators, macs_next_logic, macs_stop_logic


strategy_tree = {
    "macd": {
        "parameter_ranges": macd_parameter_ranges,
        "indicator_definitions": macd_indicators,
        "init_logic": macd_init_logic,
        "next_logic": macd_next_logic,
        "stop_logic": macd_stop_logic,
    },
    "trend_following": {
        "parameter_ranges": trend_following_parameter_ranges,
        "indicator_definitions": trend_following_indicators,
        "init_logic": trend_following_init_logic,
        "next_logic": trend_following_next_logic,
        "stop_logic": trend_following_stop_logic,
    },
    "bollinger_band": {
        "parameter_ranges": bollingerband_parameter_ranges,
        "indicator_definitions": bollingerband_indicators,
        "init_logic": bollingerband_init_logic,
        "next_logic": bollingerband_next_logic,
        "stop_logic": bollingerband_stop_logic,
    },
    "macs": {
        "parameter_ranges": macs_parameter_ranges,
        "indicator_definitions": macs_indicators,
        "init_logic": macs_init_logic,
        "next_logic": macs_next_logic,
        "stop_logic": macs_stop_logic,
    },
    "ichimoku_clouds": {
        "parameter_ranges": ichimoku_parameter_ranges,
        "indicator_definitions": ichimoku_indicators,
        "init_logic": ichimoku_init_logic,
        "next_logic": ichimoku_next_logic,
        "stop_logic": ichimoku_stop_logic,
    },
    "parabolic_sar": {
       "parameter_ranges": parabolic_sar_parameter_ranges,
        "indicator_definitions": parabolic_sar_indicators,
        "init_logic": parabolic_sar_init_logic,
        "next_logic": parabolic_sar_next_logic,
        "stop_logic": parabolic_sar_stop_logic,
    },
    "stochastic": {
       "parameter_ranges": stochastic_parameter_ranges,
        "indicator_definitions": stochastic_indicators,
        "init_logic": stochastic_init_logic,
        "next_logic": stochastic_next_logic,
        "stop_logic": stochastic_stop_logic,
    },
    "rsi": {
       "parameter_ranges": rsi_parameter_ranges,
        "indicator_definitions": rsi_indicators,
        "init_logic": rsi_init_logic,
        "next_logic": rsi_next_logic,
        "stop_logic": rsi_stop_logic,
    }
}