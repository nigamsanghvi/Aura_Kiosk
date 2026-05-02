from __future__ import annotations
from typing import Any


class PaymentStrategy:
    """Abstract payment strategy interface (duck-typed)."""

    def pay(self, amount: float, user_id: str = "ANON") -> bool: ...

    def refund(self, amount: float, ref: str = "") -> bool: ...

    def get_name(self) -> str: ...


class UPIPayment(PaymentStrategy):
    def pay(self, amount: float, user_id: str = "ANON") -> bool:
        return True

    def refund(self, amount: float, ref: str = "") -> bool:
        return True

    def get_name(self) -> str:
        return "UPI"


class CardPayment(PaymentStrategy):
    def pay(self, amount: float, user_id: str = "ANON") -> bool:
        return True

    def refund(self, amount: float, ref: str = "") -> bool:
        return True

    def get_name(self) -> str:
        return "Card"


class WalletPayment(PaymentStrategy):
    def pay(self, amount: float, user_id: str = "ANON") -> bool:
        return True

    def refund(self, amount: float, ref: str = "") -> bool:
        return True

    def get_name(self) -> str:
        return "Wallet"
