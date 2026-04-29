# Pattern: Strategy
# Role: Pluggable pricing policies that can be swapped at runtime

from __future__ import annotations
from abc import ABC, abstractmethod
from models.product import Product


# PATTERN: Strategy (Abstract Strategy)
class PricingStrategy(ABC):
    """Abstract pricing policy. Concrete strategies compute final price."""

    @abstractmethod
    def calculate(self, product: Product, qty: int) -> float: ...

    @abstractmethod
    def get_name(self) -> str: ...


# PATTERN: Strategy (Concrete — Standard)
class StandardPricing(PricingStrategy):
    """Full price with no adjustments."""

    def calculate(self, product: Product, qty: int) -> float:
        return round(product.base_price * qty, 2)

    def get_name(self) -> str:
        return "Standard"


# PATTERN: Strategy (Concrete — Discount)
class DiscountPricing(PricingStrategy):
    """Fixed percentage discount off the base price."""

    def __init__(self, discount_rate: float = 0.10) -> None:
        self._rate = max(0.0, min(discount_rate, 0.95))

    def calculate(self, product: Product, qty: int) -> float:
        base = product.base_price * qty
        return round(base * (1 - self._rate), 2)

    def get_name(self) -> str:
        return f"Discount ({int(self._rate * 100)}%)"


# PATTERN: Strategy (Concrete — Emergency)
class EmergencyPricing(PricingStrategy):
    """
    Emergency mode pricing:
    - Essential items receive a relief discount.
    - Non-essential items receive a scarcity markup.
    """

    def __init__(
        self,
        essential_discount: float = 0.20,
        non_essential_markup: float = 0.15,
    ) -> None:
        self._essential_discount = essential_discount
        self._non_essential_markup = non_essential_markup

    def calculate(self, product: Product, qty: int) -> float:
        base = product.base_price * qty
        if product.is_essential:
            return round(base * (1 - self._essential_discount), 2)
        return round(base * (1 + self._non_essential_markup), 2)

    def get_name(self) -> str:
        return "Emergency"
