import json
def save_cached_parameters(data, filename="best_parameters.json"):
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)