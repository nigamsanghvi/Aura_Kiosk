# ============================================================
# Module: tests/test_aura_retail_os.py
# Role: Unit tests covering all Path A patterns
# ============================================================

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest

from core.central_registry import CentralRegistry
from core.commands import PurchaseCommand, RefundCommand, RestockCommand, CommandInvoker
from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from core.kiosk_factory import PharmacyKioskFactory, FoodKioskFactory, EmergencyReliefKioskFactory
from events.event_bus import EventBus, EventType, IEventSubscriber
from failure.handler import RetryHandler, RecalibrateHandler, AlertHandler, build_default_chain
from inventory.inventory import Inventory
from memento.memento import InventoryMemento, TransactionCaretaker
from models.product import Product
from payment.strategy import UPIPayment, CardPayment, WalletPayment
from pricing.strategy import StandardPricing, DiscountPricing, EmergencyPricing
from state.kiosk_state import ActiveState, PowerSavingState, MaintenanceState, EmergencyState


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def fresh_registry():
    CentralRegistry._instance = None
    return CentralRegistry.get_instance()


def make_inventory(qty: int = 20) -> tuple[Inventory, Product]:
    inv = Inventory()
    p = Product("P001", "Test Product", 100.0, is_essential=True)
    inv.add_product(p, qty)
    return inv, p


# ─────────────────────────────────────────────────────────────
# 1. Singleton — CentralRegistry
# ─────────────────────────────────────────────────────────────

class TestSingleton(unittest.TestCase):
    def setUp(self):
        fresh_registry()

    def test_single_instance(self):
        a = CentralRegistry.get_instance()
        b = CentralRegistry.get_instance()
        self.assertIs(a, b)

    def test_config_persists(self):
        r = CentralRegistry.get_instance()
        r.set_config("kiosk_mode", "active")
        self.assertEqual(CentralRegistry.get_instance().get_config("kiosk_mode"), "active")

    def test_event_log(self):
        r = CentralRegistry.get_instance()
        r.log("hello test")
        self.assertTrue(any("hello test" in e for e in r.get_event_log()))


# ─────────────────────────────────────────────────────────────
# 2. State pattern
# ─────────────────────────────────────────────────────────────

class TestKioskState(unittest.TestCase):
    def test_active_allows_any_qty(self):
        s = ActiveState()
        ok, _ = s.handle_purchase(100)
        self.assertTrue(ok)

    def test_power_saving_limits_qty(self):
        s = PowerSavingState()
        ok, _ = s.handle_purchase(PowerSavingState.MAX_QTY)
        self.assertTrue(ok)
        ok, _ = s.handle_purchase(PowerSavingState.MAX_QTY + 1)
        self.assertFalse(ok)

    def test_maintenance_blocks_all(self):
        ok, _ = MaintenanceState().handle_purchase(1)
        self.assertFalse(ok)

    def test_emergency_caps_at_two(self):
        s = EmergencyState()
        ok, _ = s.handle_purchase(2)
        self.assertTrue(ok)
        ok, _ = s.handle_purchase(3)
        self.assertFalse(ok)

    def test_state_names(self):
        self.assertEqual(ActiveState().get_name(), "ACTIVE")
        self.assertEqual(PowerSavingState().get_name(), "POWER_SAVING")
        self.assertEqual(MaintenanceState().get_name(), "MAINTENANCE")
        self.assertEqual(EmergencyState().get_name(), "EMERGENCY")


# ─────────────────────────────────────────────────────────────
# 3. Strategy — Pricing
# ─────────────────────────────────────────────────────────────

class TestPricingStrategy(unittest.TestCase):
    def setUp(self):
        self.essential = Product("E", "Essential", 100.0, is_essential=True)
        self.non_essential = Product("N", "NonEssential", 100.0, is_essential=False)

    def test_standard_pricing(self):
        self.assertAlmostEqual(StandardPricing().calculate(self.essential, 3), 300.0)

    def test_discount_pricing(self):
        price = DiscountPricing(0.10).calculate(self.essential, 2)
        self.assertAlmostEqual(price, 180.0)

    def test_emergency_essential_discounted(self):
        price = EmergencyPricing(essential_discount=0.20).calculate(self.essential, 1)
        self.assertAlmostEqual(price, 80.0)

    def test_emergency_non_essential_markup(self):
        price = EmergencyPricing(non_essential_markup=0.15).calculate(self.non_essential, 1)
        self.assertAlmostEqual(price, 115.0)


# ─────────────────────────────────────────────────────────────
# 4. Command pattern
# ─────────────────────────────────────────────────────────────

class TestCommands(unittest.TestCase):
    def setUp(self):
        fresh_registry()
        self.inv, self.product = make_inventory(10)
        self.payment = UPIPayment()
        self.pricing = StandardPricing()
        self.invoker = CommandInvoker()

    def test_purchase_success(self):
        cmd = PurchaseCommand(self.inv, "P001", 3, self.payment, self.pricing)
        self.assertTrue(self.invoker.execute(cmd))
        self.assertEqual(cmd.status, "SUCCESS")
        self.assertEqual(self.inv.available_stock("P001"), 7)

    def test_purchase_insufficient_stock(self):
        cmd = PurchaseCommand(self.inv, "P001", 50, self.payment, self.pricing)
        self.assertFalse(self.invoker.execute(cmd))
        self.assertEqual(cmd.status, "FAILED")
        self.assertEqual(self.inv.available_stock("P001"), 10)  # unchanged

    def test_refund_returns_stock(self):
        # Buy first
        buy = PurchaseCommand(self.inv, "P001", 2, self.payment, self.pricing)
        self.invoker.execute(buy)
        stock_after_buy = self.inv.available_stock("P001")

        # Refund
        ref = RefundCommand(self.inv, "P001", 2, 200.0, self.payment)
        self.assertTrue(self.invoker.execute(ref))
        self.assertEqual(self.inv.available_stock("P001"), stock_after_buy + 2)

    def test_restock_increases_stock(self):
        cmd = RestockCommand(self.inv, "P001", 5)
        self.assertTrue(self.invoker.execute(cmd))
        self.assertEqual(self.inv.available_stock("P001"), 15)

    def test_invoker_records_history(self):
        self.invoker.execute(PurchaseCommand(self.inv, "P001", 1, self.payment, self.pricing))
        self.invoker.execute(RestockCommand(self.inv, "P001", 3))
        history = self.invoker.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["type"], "PURCHASE")
        self.assertEqual(history[1]["type"], "RESTOCK")


# ─────────────────────────────────────────────────────────────
# 5. Chain of Responsibility — Failure Handlers
# ─────────────────────────────────────────────────────────────

class TestFailureHandlers(unittest.TestCase):
    def test_retry_handles_transient(self):
        chain = build_default_chain()
        result = chain.handle("timeout occurred")
        self.assertEqual(result, "RETRY_SUCCESS")

    def test_recalibrate_handles_hardware(self):
        # Skip Retry, go straight to Recalibrate
        alert = AlertHandler()
        recal = RecalibrateHandler(alert)
        result = recal.handle("motor jam detected")
        self.assertEqual(result, "RECALIBRATED")

    def test_alert_is_fallback(self):
        result = AlertHandler().handle("unknown exotic error")
        self.assertEqual(result, "ALERT_SENT")

    def test_chain_escalation(self):
        chain = build_default_chain()
        result = chain.handle("completely unknown failure xyz")
        # Should escalate through Retry → Recalibrate → Alert
        self.assertEqual(result, "ALERT_SENT")


# ─────────────────────────────────────────────────────────────
# 6. Memento — Inventory rollback
# ─────────────────────────────────────────────────────────────

class TestMemento(unittest.TestCase):
    def setUp(self):
        fresh_registry()
        self.inv, _ = make_inventory(10)

    def test_save_and_restore(self):
        caretaker = TransactionCaretaker()
        caretaker.save(self.inv.get_state())

        self.inv.restock("P001", 5)
        self.assertEqual(self.inv.available_stock("P001"), 15)

        snapshot = caretaker.undo()
        self.inv.restore(snapshot)
        self.assertEqual(self.inv.available_stock("P001"), 10)

    def test_memento_is_independent_copy(self):
        state_before = self.inv.get_state()
        m = InventoryMemento(state_before)
        self.inv.restock("P001", 100)
        # Memento should still hold original value
        self.assertEqual(m.get_state()["P001"]["total"], 10)


# ─────────────────────────────────────────────────────────────
# 7. Observer — EventBus
# ─────────────────────────────────────────────────────────────

class RecordingSubscriber(IEventSubscriber):
    def __init__(self):
        self.received = []

    def on_event(self, event_type, payload):
        self.received.append(event_type)


class TestEventBus(unittest.TestCase):
    def test_subscribe_and_publish(self):
        bus = EventBus()
        sub = RecordingSubscriber()
        bus.subscribe(EventType.PURCHASE_SUCCESS, sub)
        bus.publish(EventType.PURCHASE_SUCCESS, {"detail": "test"})
        self.assertIn(EventType.PURCHASE_SUCCESS, sub.received)

    def test_unsubscribe(self):
        bus = EventBus()
        sub = RecordingSubscriber()
        bus.subscribe(EventType.LOW_STOCK, sub)
        bus.unsubscribe(EventType.LOW_STOCK, sub)
        bus.publish(EventType.LOW_STOCK, {})
        self.assertEqual(len(sub.received), 0)

    def test_event_log_persists(self):
        bus = EventBus()
        bus.publish(EventType.STATE_CHANGED, {"detail": "test"})
        log = bus.get_log()
        self.assertTrue(any(e["event_type"] == EventType.STATE_CHANGED for e in log))

    def test_multiple_subscribers(self):
        bus = EventBus()
        s1, s2 = RecordingSubscriber(), RecordingSubscriber()
        bus.subscribe(EventType.RESTOCK_DONE, s1)
        bus.subscribe(EventType.RESTOCK_DONE, s2)
        bus.publish(EventType.RESTOCK_DONE, {})
        self.assertEqual(len(s1.received), 1)
        self.assertEqual(len(s2.received), 1)


# ─────────────────────────────────────────────────────────────
# 8. Inventory derived attributes
# ─────────────────────────────────────────────────────────────

class TestInventory(unittest.TestCase):
    def setUp(self):
        self.inv, _ = make_inventory(20)

    def test_available_stock_derived(self):
        self.inv.reserve("P001", 5)
        self.assertEqual(self.inv.available_stock("P001"), 15)

    def test_hardware_fault_zeroes_stock(self):
        self.inv.set_hardware_ok("P001", False)
        self.assertEqual(self.inv.available_stock("P001"), 0)
        self.assertFalse(self.inv.check_stock("P001", 1))

    def test_reservation_is_atomic(self):
        self.inv.reserve("P001", 18)
        # Only 2 remain; reserving 3 should fail
        self.assertFalse(self.inv.reserve("P001", 3))
        self.assertEqual(self.inv.available_stock("P001"), 2)

    def test_commit_deducts_total(self):
        self.inv.reserve("P001", 5)
        self.inv.commit_deduction("P001", 5)
        self.assertEqual(self.inv.available_stock("P001"), 15)

    def test_low_stock_flag(self):
        self.inv.reserve("P001", 16)
        self.assertTrue(self.inv.is_low_stock("P001"))


# ─────────────────────────────────────────────────────────────
# 9. Abstract Factory
# ─────────────────────────────────────────────────────────────

class TestAbstractFactory(unittest.TestCase):
    def setUp(self):
        fresh_registry()

    def _make(self, factory_cls):
        bus = EventBus()
        return factory_cls().create_kiosk("TEST", bus)

    def test_pharmacy_factory(self):
        iface = self._make(PharmacyKioskFactory)
        self.assertIn("Card", iface.getCurrentPricing() + iface.kiosk.get_payment().get_name())
        products = {p["product_id"] for p in iface.getInventory()}
        self.assertIn("MED-001", products)

    def test_food_factory(self):
        iface = self._make(FoodKioskFactory)
        products = {p["product_id"] for p in iface.getInventory()}
        self.assertIn("FOOD-001", products)

    def test_emergency_factory(self):
        iface = self._make(EmergencyReliefKioskFactory)
        products = {p["product_id"] for p in iface.getInventory()}
        self.assertIn("EMRG-001", products)


# ─────────────────────────────────────────────────────────────
# 10. Facade (KioskInterface)
# ─────────────────────────────────────────────────────────────

class TestFacade(unittest.TestCase):
    def setUp(self):
        fresh_registry()
        bus = EventBus()
        self.iface = PharmacyKioskFactory().create_kiosk("FACADE-TEST", bus)

    def test_purchase_via_facade(self):
        result = self.iface.purchaseItem("MED-001", 1)
        self.assertIn("Success", result)

    def test_restock_via_facade(self):
        result = self.iface.restockInventory("MED-001", 10)
        self.assertEqual(result, "Restocked")

    def test_refund_via_facade(self):
        result = self.iface.refundTransaction("MED-001", qty=1, amount=25.0)
        self.assertEqual(result, "Success")

    def test_diagnostics_via_facade(self):
        d = self.iface.runDiagnostics()
        self.assertIn("kiosk_id", d)
        self.assertIn("state", d)

    def test_set_state_via_facade(self):
        self.iface.setKioskState(MaintenanceState())
        self.assertEqual(self.iface.getCurrentState(), "MAINTENANCE")

    def test_blocked_in_maintenance(self):
        self.iface.setKioskState(MaintenanceState())
        result = self.iface.purchaseItem("MED-001", 1)
        self.assertIn("Blocked", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)