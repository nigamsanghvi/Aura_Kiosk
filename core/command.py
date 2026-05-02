# Pattern: Command
# Role: Encapsulate all kiosk operations as executable commands

from __future__ import annotations 
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from inventory.inventory import Inventory
    from payment.strategy import PaymentStrategy
    from pricing.strategy import PricingStrategy
    from models.product import Product


# PATTERN: Command (Abstract Command)
class Command(ABC):
    def __init__(self) -> None:
        self._timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        self._status = "PENDING"
        self._txn_id = str(uuid.uuid4())[:8].upper()

    @abstractmethod
    def execute(self) -> bool: ...

    @property
    def txn_id(self) -> str:
        return self._txn_id

    @property
    def status(self) -> str:
        return self._status

    @property
    def timestamp(self) -> str:
        return self._timestamp

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


# PATTERN: Command (Concrete — Purchase)
class PurchaseCommand(Command):
    """
    Atomic purchase:
      1. Reserve stock
      2. Compute price
      3. Charge payment
      4. Commit inventory deduction
    Each step is rolled back if a later step fails.
    """

    def __init__(
        self,
        inventory: Inventory,
        product_id: str,
        qty: int,
        payment: PaymentStrategy,
        pricing: PricingStrategy,
        user_id: str = "ANON",
    ) -> None:
        super().__init__()
        self._inventory = inventory
        self._pid = product_id
        self._qty = qty
        self._payment = payment
        self._pricing = pricing
        self._user_id = user_id
        self._amount = 0.0

    def execute(self) -> bool:
        product = self._inventory.get_product(self._pid)
        if product is None:
            self._status = "FAILED"
            return False

        # Step 1: Reserve stock
        if not self._inventory.reserve(self._pid, self._qty):
            self._status = "FAILED"
            return False

        # Step 2: Compute price
        self._amount = self._pricing.calculate(product, self._qty)

        # Step 3: Charge payment
        if not self._payment.pay(self._amount, self._user_id):
            self._inventory.release_reservation(self._pid, self._qty)
            self._status = "FAILED"
            return False

        # Step 4: Commit inventory
        self._inventory.commit_deduction(self._pid, self._qty)
        self._status = "SUCCESS"
        return True

    @property
    def amount(self) -> float:
        return self._amount

    @property
    def product_id(self) -> str:
        return self._pid

    @property
    def qty(self) -> int:
        return self._qty

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self._txn_id,
            "type": "PURCHASE",
            "product_id": self._pid,
            "qty": self._qty,
            "amount": self._amount,
            "payment": self._payment.get_name(),
            "pricing": self._pricing.get_name(),
            "user_id": self._user_id,
            "status": self._status,
            "timestamp": self._timestamp,
        }


# PATTERN: Command (Concrete — Refund)
class RefundCommand(Command):
    def __init__(
        self,
        inventory: Inventory,
        product_id: str,
        qty: int,
        amount: float,
        payment: PaymentStrategy,
        ref: str = "",
    ) -> None:
        super().__init__()
        self._inventory = inventory
        self._pid = product_id
        self._qty = qty
        self._amount = amount
        self._payment = payment
        self._ref = ref

    def execute(self) -> bool:
        refunded = self._payment.refund(self._amount, self._ref or self._txn_id)
        if refunded:
            self._inventory.return_stock(self._pid, self._qty)
            self._status = "SUCCESS"
        else:
            self._status = "FAILED"
        return refunded

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self._txn_id,
            "type": "REFUND",
            "product_id": self._pid,
            "qty": self._qty,
            "amount": self._amount,
            "status": self._status,
            "timestamp": self._timestamp,
        }


# PATTERN: Command (Concrete — Restock)
class RestockCommand(Command):
    def __init__(self, inventory: Inventory, product_id: str, qty: int) -> None:
        super().__init__()
        self._inventory = inventory
        self._pid = product_id
        self._qty = qty

    def execute(self) -> bool:
        ok = self._inventory.restock(self._pid, self._qty)
        self._status = "SUCCESS" if ok else "FAILED"
        return ok

    def to_dict(self) -> dict[str, Any]:
        return {
            "txn_id": self._txn_id,
            "type": "RESTOCK",
            "product_id": self._pid,
            "qty": self._qty,
            "status": self._status,
            "timestamp": self._timestamp,
        }


# ── Command Invoker ────────────────────────────────────────────
class CommandInvoker:
    """Executes commands and maintains an auditable history."""

    def __init__(self) -> None:
        self._history: list[Command] = []

    def execute(self, cmd: Command) -> bool:
        result = cmd.execute()
        self._history.append(cmd)
        return result

    def get_history(self) -> list[dict[str, Any]]:
        return [c.to_dict() for c in self._history]

    def print_history(self) -> None:
        for cmd in self._history:
            d = cmd.to_dict()
            print(
                f"  [{d['timestamp']}] {d['type']} {d.get('product_id', '')} "
                f"qty={d.get('qty', '')} amount={d.get('amount', '')} [{d['status']}]"
            )
