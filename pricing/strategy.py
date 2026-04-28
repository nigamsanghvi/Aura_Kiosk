
class PricingStrategy:
    def calculate(self, base, qty): pass

class StandardPricing(PricingStrategy):
    def calculate(self, base, qty):
        return base * qty

class DiscountPricing(PricingStrategy):
    def calculate(self, base, qty):
        return base * qty * 0.9

class EmergencyPricing(PricingStrategy):
    def calculate(self, base, qty):
        return base * qty * 1.2
