import json
from datetime import datetime, timedelta

def needs_weekly_update():
    try:
        with open("best_parameters.json", "r") as file:
            data = json.load(file)
        last_update_str = data.get("last_update")
        if not last_update_str:
            return True  # If no last update is found, run weekly update

        last_update = datetime.strptime(last_update_str, "%Y-%m-%d")
        return last_update < datetime.today() - timedelta(days=7)
    
    except (FileNotFoundError, json.JSONDecodeError):
        return True  # If file is missing or corrupted, run weekly update
    
def load_best_parameters():
    try:
        with open("best_parameters.json", "r") as file:
            data = json.load(file)
            return data.get("best_parameters", {})
    except (FileNotFoundError, json.JSONDecodeError):
        print("⚠️ No valid best_parameters.json found. Running default parameters.")
        return {}