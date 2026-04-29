# Pattern: Facade
# Role: Simplified external API — hides all subsystem complexity

from __future__ import annotations
from typing import Any, TYPE_CHECKING

from core.kiosk import Kiosk

if TYPE_CHECKING:
    from payment.strategy import PaymentStrategy
    from pricing.strategy import PricingStrategy
    from state.kiosk_state import KioskState


# PATTERN: Facade
class KioskInterface:
    """
    Single entry point for all external interactions with a Kiosk.
    External systems call only these methods; subsystem details are hidden.
    """

    def __init__(self, kiosk: Kiosk) -> None:
        self._kiosk = kiosk

    # ── Core operations ───────────────────────────────────────
    def purchaseItem(
        self,
        product_id: str,
        qty: int,
        payment: PaymentStrategy | None = None,
        pricing: PricingStrategy | None = None,
        user_id: str = "ANON",
    ) -> str:
        return self._kiosk.purchase(product_id, qty, payment, pricing, user_id)

    def refundTransaction(
        self, product_id: str, qty: int = 1, amount: float = 0.0, ref: str = ""
    ) -> str:
        return self._kiosk.refund(product_id, qty, amount, ref)

    def restockInventory(self, product_id: str, qty: int) -> str:
        return self._kiosk.restock(product_id, qty)

    def runDiagnostics(self) -> dict[str, Any]:
        return self._kiosk.run_diagnostics()

    # ── State & strategy controls ─────────────────────────────
    def setKioskState(self, state: KioskState) -> None:
        self._kiosk.set_state(state)

    def setPricingStrategy(self, pricing: PricingStrategy) -> None:
        self._kiosk.set_pricing(pricing)

    def setPaymentMethod(self, payment: PaymentStrategy) -> None:
        self._kiosk.set_payment(payment)

    # ── Query ─────────────────────────────────────────────────
    def getInventory(self) -> list[dict]:
        return self._kiosk.inventory.list_all()

    def getTransactionHistory(self) -> list[dict]:
        return self._kiosk.transaction_history

    def getCurrentState(self) -> str:
        return self._kiosk.get_state().get_name()

    def getCurrentPricing(self) -> str:
        return self._kiosk.get_pricing().get_name()

    # ── Expose underlying kiosk for advanced scenarios ────────
    @property
    def kiosk(self) -> Kiosk:
        return self._kiosk
