class KioskInterface:
    def __init__(self, kiosk):
        self.kiosk = kiosk

    def purchaseItem(self, pid, qty, payment, pricing):
        return self.kiosk.purchase(pid, qty, payment, pricing)

    def refundTransaction(self, transaction_id):
        return self.kiosk.refund(transaction_id)

    def restockInventory(self, pid, qty):
        return self.kiosk.restock(pid, qty)

    def runDiagnostics(self):
        return "System OK"