from datetime import datetime, timedelta

def segregate_trades(log_data):
    today = datetime.today().date()
    start_of_week = today - timedelta(days=today.weekday())  # Monday of this week
    start_of_last_30_days = today - timedelta(days=30)

    segregated_data = {
        "today": {"BUY": [], "SELL": []},
        "week": {"BUY": [], "SELL": []},
        "month": {"BUY": [], "SELL": []},
    }

    for trade in log_data:
        trade_date = trade["Date"]
        trade_type = trade["Type"]  # "BUY" or "SELL"

        if trade_date == today:
            segregated_data["today"][trade_type].append(trade)
        if trade_date >= start_of_week:
            segregated_data["week"][trade_type].append(trade)
        if trade_date >= start_of_last_30_days:
            segregated_data["month"][trade_type].append(trade)

    return segregated_data

# Example usage:
# result = segregate_trades(self.log_data)
# print(result["today"]["BUY"])
# print(result["week"]["SELL"])
# print(result["month"])
