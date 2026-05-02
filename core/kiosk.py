# Role: Kiosk core — orchestrates all Path A subsystems

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from core.central_registry import CentralRegistry
from core.command import PurchaseCommand, RefundCommand, RestockCommand, CommandInvoker
from events.event_bus import EventBus, EventType
from inventory.inventory import Inventory
from memento.memento import TransactionCaretaker
from state.kiosk_state import KioskState, ActiveState

if TYPE_CHECKING:
    from failure.handler import FailureHandler
    from payment.strategy import PaymentStrategy
    from pricing.strategy import PricingStrategy


class Kiosk:
    """
    Path A Kiosk Core.

    Patterns in use:
      • State       — operational mode (Active/PowerSaving/Maintenance/Emergency)
      • Strategy    — pricing & payment (swappable at runtime)
      • Command     — every operation is a Command object
      • Memento     — snapshot before purchase; rollback on failure
      • Chain of Responsibility — failure handler chain
      • Observer    — publishes events to subscribers via EventBus
      • Singleton   — CentralRegistry for global config/logging
    """

    def __init__(
        self,
        kiosk_id: str,
        inventory: Inventory,
        failure_handler: FailureHandler,
        event_bus: EventBus,
        default_pricing: PricingStrategy | None = None,
        default_payment: PaymentStrategy | None = None,
    ) -> None:
        self._id = kiosk_id
        self._inventory = inventory
        self._failure_handler = failure_handler
        self._event_bus = event_bus

        from pricing.strategy import StandardPricing
        from payment.strategy import UPIPayment

        self._pricing: PricingStrategy = default_pricing or StandardPricing()
        self._payment: PaymentStrategy = default_payment or UPIPayment()

        self._state: KioskState = ActiveState()
        self._caretaker = TransactionCaretaker()
        self._invoker = CommandInvoker()
        self._registry = CentralRegistry.get_instance()
        self._transactions: list[dict] = []

        self._registry.log(f"Kiosk {kiosk_id!r} initialised.")

    # ── State management (PATTERN: State) ─────────────────────
    def set_state(self, new_state: KioskState) -> None:
        old = self._state.get_name()
        self._state = new_state
        self._registry.log(f"[{self._id}] State change: {old} → {new_state.get_name()}")
        self._event_bus.publish(
            EventType.STATE_CHANGED,
            {
                "kiosk_id": self._id,
                "old_state": old,
                "new_state": new_state.get_name(),
                "detail": new_state.describe(),
            },
        )
        if new_state.get_name() == "EMERGENCY":
            self._event_bus.publish(
                EventType.EMERGENCY_ACTIVATED,
                {"kiosk_id": self._id, "detail": new_state.describe()},
            )

    def get_state(self) -> KioskState:
        return self._state

    # ── Strategy swaps (PATTERN: Strategy) ────────────────────
    def set_pricing(self, strategy: PricingStrategy) -> None:
        self._pricing = strategy
        self._registry.log(f"[{self._id}] Pricing changed to {strategy.get_name()!r}")
        self._event_bus.publish(
            EventType.PRICING_CHANGED,
            {
                "kiosk_id": self._id,
                "pricing": strategy.get_name(),
                "detail": strategy.get_name(),
            },
        )

    def set_payment(self, strategy: PaymentStrategy) -> None:
        self._payment = strategy
        self._registry.log(f"[{self._id}] Payment changed to {strategy.get_name()!r}")

    def get_pricing(self) -> PricingStrategy:
        return self._pricing

    def get_payment(self) -> PaymentStrategy:
        return self._payment

    # ── Purchase (Command + Memento + State + Observer) ────────
    def purchase(
        self,
        pid: str,
        qty: int,
        payment: PaymentStrategy | None = None,
        pricing: PricingStrategy | None = None,
        user_id: str = "ANON",
    ) -> str:
        payment = payment or self._payment
        pricing = pricing or self._pricing

        print(
            f"\n[{self._id}] Purchase attempt — product={pid}, qty={qty}, state={self._state.get_name()}"
        )

        # ── State check ───────────────────────────────────────
        allowed, reason = self._state.handle_purchase(qty)
        if not allowed:
            self._registry.log(f"[{self._id}] Purchase BLOCKED by state: {reason}")
            return f"Blocked: {reason}"

        # ── Stock check ───────────────────────────────────────
        if not self._inventory.check_stock(pid, qty):
            avail = self._inventory.available_stock(pid)
            self._registry.log(
                f"[{self._id}] Purchase FAILED — insufficient stock (have {avail}, need {qty})"
            )
            return "OutOfStock"

        # ── Hardware check ────────────────────────────────────
        product = self._inventory.get_product(pid)
        if product:
            for hw in product.requires_hardware:
                if not self._registry.get_status(f"hw_{hw}", True):
                    msg = f"Required hardware module '{hw}' is currently unavailable."
                    self._registry.log(f"[{self._id}] {msg}")
                    return f"HardwareFault: {msg}"

        # ── Memento: save state BEFORE attempting ─────────────
        self._caretaker.save(self._inventory.get_state())

        # ── Execute Command ───────────────────────────────────
        cmd = PurchaseCommand(self._inventory, pid, qty, payment, pricing, user_id)
        success = self._invoker.execute(cmd)

        if success:
            record = cmd.to_dict()
            self._transactions.append(record)
            self._registry.log(
                f"[{self._id}] Purchase SUCCESS — {pid} x{qty} ₹{cmd.amount:.2f}"
            )
            self._event_bus.publish(
                EventType.PURCHASE_SUCCESS,
                {
                    "kiosk_id": self._id,
                    "product_id": pid,
                    "qty": qty,
                    "amount": cmd.amount,
                    "detail": f"{pid} x{qty} purchased by {user_id}",
                },
            )
            # Low-stock check
            if self._inventory.is_low_stock(pid):
                self._event_bus.publish(
                    EventType.LOW_STOCK,
                    {
                        "kiosk_id": self._id,
                        "product_id": pid,
                        "current_qty": self._inventory.available_stock(pid),
                        "detail": f"Low stock on {pid}",
                    },
                )
            return f"Success (txn={cmd.txn_id}, amount=₹{cmd.amount:.2f})"
        else:
            # ── Failure: run handler chain ─────────────────────
            self._event_bus.publish(
                EventType.PURCHASE_FAILED,
                {
                    "kiosk_id": self._id,
                    "product_id": pid,
                    "detail": "Command execution failed",
                },
            )
            result = self._failure_handler.handle("temporary")
            self._registry.log(f"[{self._id}] Failure handler result: {result}")

            # ── Memento: rollback inventory ────────────────────
            snapshot = self._caretaker.undo()
            if snapshot:
                self._inventory.restore(snapshot)
                self._registry.log(f"[{self._id}] Inventory rolled back via Memento.")
            self._event_bus.publish(
                EventType.TRANSACTION_ROLLBACK,
                {
                    "kiosk_id": self._id,
                    "product_id": pid,
                    "detail": "Inventory rolled back",
                },
            )
            return "Rollback"

    # ── Refund (Command) ───────────────────────────────────────
    def refund(self, pid: str, qty: int = 1, amount: float = 0.0, ref: str = "") -> str:
        cmd = RefundCommand(self._inventory, pid, qty, amount, self._payment, ref)
        ok = self._invoker.execute(cmd)
        status = "Success" if ok else "Failed"
        self._registry.log(f"[{self._id}] Refund {status} — {pid}")
        if ok:
            self._event_bus.publish(
                EventType.REFUND_SUCCESS,
                {
                    "kiosk_id": self._id,
                    "product_id": pid,
                    "amount": amount,
                    "detail": ref,
                },
            )
        return status

    # ── Restock (Command) ──────────────────────────────────────
    def restock(self, pid: str, qty: int) -> str:
        cmd = RestockCommand(self._inventory, pid, qty)
        ok = self._invoker.execute(cmd)
        status = "Restocked" if ok else "Failed"
        self._registry.log(f"[{self._id}] Restock {status} — {pid} +{qty}")
        if ok:
            self._event_bus.publish(
                EventType.RESTOCK_DONE,
                {
                    "kiosk_id": self._id,
                    "product_id": pid,
                    "qty": qty,
                    "detail": f"+{qty} units",
                },
            )
        return status

    # ── Diagnostics ────────────────────────────────────────────
    def run_diagnostics(self) -> dict[str, Any]:
        return {
            "kiosk_id": self._id,
            "state": self._state.get_name(),
            "state_desc": self._state.describe(),
            "pricing": self._pricing.get_name(),
            "payment": self._payment.get_name(),
            "inventory_summary": self._inventory.list_all(),
        }

    # ── Accessors ──────────────────────────────────────────────
    @property
    def kiosk_id(self) -> str:
        return self._id

    @property
    def inventory(self) -> Inventory:
        return self._inventory

    @property
    def transactions(self) -> list[dict]:
        return list(self._transactions)

    @property
    def transaction_history(self) -> list[dict]:
        return self._invoker.get_history()

    def print_transaction_history(self) -> None:
        self._invoker.print_history()
