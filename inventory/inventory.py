
class Inventory:
    def __init__(self):
        self.items = {}

    def add_product(self, product, qty):
        self.items[product.id] = {"product": product, "qty": qty}

    def check_stock(self, pid, qty):
        return self.items.get(pid, {}).get("qty", 0) >= qty

    def reduce(self, pid, qty):
        self.items[pid]["qty"] -= qty

    def get_price(self, pid):
        return self.items[pid]["product"].price

    def get_state(self):
        return {k: v["qty"] for k,v in self.items.items()}

    def restore(self, state):
        for k in state:
            self.items[k]["qty"] = state[k]
