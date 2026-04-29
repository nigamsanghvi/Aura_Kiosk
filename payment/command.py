class Command:
    def execute(self): pass


class PurchaseCommand(Command):
    def __init__(self, inventory, pid, qty, strategy, amount):
        self.inventory = inventory
        self.pid = pid
        self.qty = qty
        self.strategy = strategy
        self.amount = amount

    def execute(self):
        print("[COMMAND] Purchase")
        self.strategy.pay(self.amount)

        if self.qty > 3:
            raise Exception("temporary")

        self.inventory.reduce(self.pid, self.qty)


class RefundCommand(Command):
    def __init__(self, inventory, pid, qty):
        self.inventory = inventory
        self.pid = pid
        self.qty = qty

    def execute(self):
        print("[COMMAND] Refund")
        self.inventory.items[self.pid]["qty"] += self.qty


class RestockCommand(Command):
    def __init__(self, inventory, pid, qty):
        self.inventory = inventory
        self.pid = pid
        self.qty = qty

    def execute(self):
        print("[COMMAND] Restock")
        self.inventory.items[self.pid]["qty"] += self.qty