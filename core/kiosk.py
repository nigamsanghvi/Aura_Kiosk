from persistence.storage import Storage
from payment.command import PurchaseCommand, RefundCommand, RestockCommand
from state.kiosk_state import ActiveState
from memento.memento import Caretaker
from events.event_bus import EventBus

class Kiosk:
    def __init__(self, inventory, failure_handler):
        self.state = ActiveState()
        self.inventory = inventory
        self.failure_handler = failure_handler
        self.caretaker = Caretaker()
        self.event_bus = EventBus()
        self.transactions = []

    def purchase(self, pid, qty, payment, pricing):
        print("\n[KIOSK STATE]:", self.state.get_name())

        if not self.state.handle_purchase(qty):
            return "Blocked"

        if not self.inventory.check_stock(pid, qty):
            return "Out of stock"

        self.caretaker.save(self.inventory.get_state())

        base_price = self.inventory.get_price(pid)
        final_price = pricing.calculate(base_price, qty)

        cmd = PurchaseCommand(self.inventory, pid, qty, payment, final_price)

        try:
            cmd.execute()
            self.transactions.append({"pid": pid, "qty": qty, "amount": final_price})

            Storage.save_inventory(self.inventory.get_state())
            Storage.save_transactions(self.transactions)

            self.event_bus.publish("PurchaseSuccess")
            return "Success"

        except Exception as e:
            print("[ERROR]:", e)

            self.failure_handler.handle(str(e))
            self.inventory.restore(self.caretaker.undo())

            self.event_bus.publish("PurchaseFailed")
            return "Rollback"

    def refund(self, pid, qty=1):
        cmd = RefundCommand(self.inventory, pid, qty)
        cmd.execute()
        return "Refunded"

    def restock(self, pid, qty):
        cmd = RestockCommand(self.inventory, pid, qty)
        cmd.execute()
        return "Restocked"