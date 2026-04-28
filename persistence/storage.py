import json

class Storage:
    @staticmethod
    def save_inventory(data, file="inventory.json"):
        with open(file, "w") as f:
            json.dump(data, f)

    @staticmethod
    def load_inventory(file="inventory.json"):
        try:
            with open(file, "r") as f:
                return json.load(f)
        except:
            return {}

    @staticmethod
    def save_transactions(data, file="transactions.json"):
        with open(file, "w") as f:
            json.dump(data, f)