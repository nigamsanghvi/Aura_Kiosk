
class PaymentStrategy:
    def pay(self, amount): pass

class UPI(PaymentStrategy):
    def pay(self, amount):
        print("Paid via UPI:", amount)
