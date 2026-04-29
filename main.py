# Role: Entry point — demonstrates all scenarios

from __future__ import annotations
import sys, os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.central_registry import CentralRegistry
from core.kiosk_factory import (
    PharmacyKioskFactory,
    FoodKioskFactory,
    EmergencyReliefKioskFactory,
)
from events.event_bus import (
    EventBus,
    MaintenanceServiceSubscriber,
    SupplyChainSubscriber,
    CityMonitoringSubscriber,
    EventType,
)
from state.kiosk_state import (
    ActiveState,
    PowerSavingState,
    MaintenanceState,
    EmergencyState,
)
from pricing.strategy import StandardPricing, DiscountPricing, EmergencyPricing
from payment.strategy import UPIPayment, CardPayment, WalletPayment
from persistence.storage import Storage

# ─────────────────────────────────────────────────────────────
# Shared infrastructure
# ─────────────────────────────────────────────────────────────


def build_event_bus() -> EventBus:
    bus = EventBus()
    bus.subscribe(EventType.HARDWARE_FAILURE, MaintenanceServiceSubscriber())
    bus.subscribe(EventType.HARDWARE_RECALIBRATED, MaintenanceServiceSubscriber())
    bus.subscribe(EventType.LOW_STOCK, SupplyChainSubscriber())
    bus.subscribe(EventType.EMERGENCY_ACTIVATED, CityMonitoringSubscriber())
    bus.subscribe(EventType.TRANSACTION_ROLLBACK, CityMonitoringSubscriber())
    return bus


def sep(title: str) -> None:
    print("\n" + "=" * 65)
    print(f"  {title}")
    print("=" * 65)


# ─────────────────────────────────────────────────────────────
# Scenario 1: Dynamic Pricing Change
# ─────────────────────────────────────────────────────────────


def scenario_1() -> None:
    sep("SCENARIO 1 — Dynamic Pricing Strategy Change")

    bus = build_event_bus()
    interface = PharmacyKioskFactory().create_kiosk("KIOSK-001", bus)

    print("\nStep 1: Purchase with Standard pricing")
    result = interface.purchaseItem("MED-001", 2, user_id="USER-001")
    print(f"  Result: {result}")

    print("\nStep 2: Switch to Discount pricing (10% off)")
    interface.setPricingStrategy(DiscountPricing(0.10))
    result = interface.purchaseItem("MED-001", 2, user_id="USER-001")
    print(f"  Result: {result}")

    print("\nStep 3: Switch to Emergency pricing")
    interface.setPricingStrategy(EmergencyPricing())
    result = interface.purchaseItem("MED-001", 2, user_id="USER-001")
    print(f"  Result (essential item — discounted): {result}")

    result = interface.purchaseItem("MED-004", 1, user_id="USER-001")
    print(f"  Result (non-essential — markup): {result}")

    print("\nStep 4: Runtime payment method swap")
    interface.setPaymentMethod(UPIPayment())
    result = interface.purchaseItem("MED-002", 1, user_id="USER-002")
    print(f"  Result (paid via UPI): {result}")

    print("\nInventory after scenario 1:")
    for row in interface.getInventory():
        print(f"  {row['product_id']} {row['name']:25s} avail={row['available']}")


# ─────────────────────────────────────────────────────────────
# Scenario 2: Kiosk State Transitions
# ─────────────────────────────────────────────────────────────


def scenario_2() -> None:
    sep("SCENARIO 2 — Kiosk Operational State Transitions")

    bus = build_event_bus()
    interface = FoodKioskFactory().create_kiosk("KIOSK-002", bus)

    print(f"\nCurrent state: {interface.getCurrentState()}")

    print("\nStep 1: Normal purchase in ACTIVE state")
    result = interface.purchaseItem("FOOD-001", 2, user_id="USER-010")
    print(f"  Result: {result}")

    print("\nStep 2: Switch to POWER_SAVING mode")
    interface.setKioskState(PowerSavingState())
    result = interface.purchaseItem("FOOD-001", 10, user_id="USER-010")
    print(f"  Purchase of 10 units: {result}  (should be blocked — exceeds limit)")
    result = interface.purchaseItem("FOOD-001", 3, user_id="USER-010")
    print(f"  Purchase of 3 units: {result}   (should succeed)")

    print("\nStep 3: Switch to MAINTENANCE mode")
    interface.setKioskState(MaintenanceState())
    result = interface.purchaseItem("FOOD-001", 1, user_id="USER-010")
    print(f"  Purchase attempt: {result}  (should be blocked)")

    print("\nStep 4: Switch to EMERGENCY mode")
    interface.setKioskState(EmergencyState())
    result = interface.purchaseItem("FOOD-002", 3, user_id="USER-010")
    print(f"  Purchase of 3 units: {result}  (should be blocked — cap is 2)")
    result = interface.purchaseItem("FOOD-002", 2, user_id="USER-010")
    print(f"  Purchase of 2 units: {result}  (should succeed)")

    print("\nStep 5: Restore to ACTIVE mode")
    interface.setKioskState(ActiveState())
    result = interface.purchaseItem("FOOD-001", 5, user_id="USER-010")
    print(f"  Purchase of 5 units: {result}  (should succeed)")

    print(f"\nFinal state: {interface.getCurrentState()}")


# ─────────────────────────────────────────────────────────────
# Scenario 3: Hardware Failure Recovery
# ─────────────────────────────────────────────────────────────


def scenario_3() -> None:
    sep("SCENARIO 3 — Hardware Failure Recovery (Chain of Responsibility + Memento)")

    bus = build_event_bus()
    interface = EmergencyReliefKioskFactory().create_kiosk("KIOSK-003", bus)
    registry = CentralRegistry.get_instance()

    print("\nStep 1: Normal purchase — succeeds")
    result = interface.purchaseItem("EMRG-001", 2, user_id="USER-020")
    print(f"  Result: {result}")

    print("\nStep 2: Check inventory stock before forced failure")
    for row in interface.getInventory():
        if row["product_id"] == "EMRG-001":
            print(f"  EMRG-001 available stock: {row['available']}")

    print("\nStep 3: Simulate hardware fault — mark product hardware unavailable")
    interface.kiosk.inventory.set_hardware_ok("EMRG-001", False)
    bus.publish(
        EventType.HARDWARE_FAILURE,
        {"kiosk_id": "KIOSK-003", "detail": "Dispenser motor stall on EMRG-001"},
    )

    result = interface.purchaseItem("EMRG-001", 1, user_id="USER-020")
    print(f"  Purchase with faulted hardware: {result}  (should be HardwareFault)")

    print("\nStep 4: Failure handler chain resolves the issue")
    print("  (Retry → Recalibrate → Alert chain in action)")
    from failure.handler import build_default_chain

    chain = build_default_chain()
    outcome = chain.handle("hardware motor jam")
    print(f"  Chain resolution: {outcome}")
    bus.publish(
        EventType.HARDWARE_RECALIBRATED,
        {"kiosk_id": "KIOSK-003", "detail": "Dispenser recalibrated successfully"},
    )

    print("\nStep 5: Restore hardware — purchase should succeed again")
    interface.kiosk.inventory.set_hardware_ok("EMRG-001", True)
    result = interface.purchaseItem("EMRG-001", 1, user_id="USER-020")
    print(f"  Result after recovery: {result}")

    print("\nStep 6: Verify Memento rollback is functioning")
    print("  (Check that stock was NOT incorrectly deducted during fault window)")
    for row in interface.getInventory():
        if row["product_id"] == "EMRG-001":
            print(
                f"  EMRG-001 available stock (should be consistent): {row['available']}"
            )


# ─────────────────────────────────────────────────────────────
# Scenario 4: Event-Driven Notification System
# ─────────────────────────────────────────────────────────────


def scenario_4() -> None:
    sep("SCENARIO 4 — Event-Driven Notifications (Observer)")

    bus = build_event_bus()
    interface = PharmacyKioskFactory().create_kiosk("KIOSK-004", bus)

    print("\nStep 1: Buy nearly all of MED-002 stock to trigger LowStockEvent")
    # MED-002 starts at qty=60; low stock threshold is 5
    result = interface.purchaseItem("MED-002", 56, user_id="USER-030")
    print(f"  Result: {result}")

    print("\nStep 2: One more purchase — triggers low stock event to SupplyChain")
    result = interface.purchaseItem("MED-002", 2, user_id="USER-030")
    print(f"  Result: {result}")

    print("\nStep 3: Activate Emergency mode — CityMonitor is notified")
    interface.setKioskState(EmergencyState())

    print("\nStep 4: Restock via event log")
    result = interface.restockInventory("MED-002", 100)
    print(f"  Restock result: {result}")

    print("\nStep 5: Review event log")
    print("\n--- Event log (last 8 entries) ---")
    for entry in bus.get_log()[-8:]:
        print(f"  [{entry.get('event_type')}] {entry.get('detail', '')}")


# ─────────────────────────────────────────────────────────────
# Scenario 5: Full Transaction with Refund & Persistence
# ─────────────────────────────────────────────────────────────


def scenario_5() -> None:
    sep("SCENARIO 5 — Purchase, Refund & JSON Persistence")

    bus = build_event_bus()
    interface = FoodKioskFactory().create_kiosk("KIOSK-005", bus)

    print("\nStep 1: Purchase")
    result = interface.purchaseItem("FOOD-003", 2, user_id="USER-040")
    print(f"  Purchase: {result}")

    print("\nStep 2: Refund")
    result = interface.refundTransaction("FOOD-003", qty=2, amount=190.0)
    print(f"  Refund: {result}")

    print("\nStep 3: Restock")
    result = interface.restockInventory("FOOD-003", 10)
    print(f"  Restock: {result}")

    print("\nStep 4: Save to JSON")
    inv_data = interface.getInventory()
    txn_data = interface.getTransactionHistory()
    Storage.save_inventory(inv_data, "data/inventory_kiosk005.json")
    Storage.save_transactions(txn_data, "data/transactions_kiosk005.json")
    print("  Saved inventory   → data/inventory_kiosk005.json")
    print("  Saved transactions → data/transactions_kiosk005.json")

    print("\nStep 5: Transaction history")
    interface.kiosk.print_transaction_history()


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────


def main() -> None:
    CentralRegistry._instance = None  # clean slate for demo
    registry = CentralRegistry.get_instance()
    registry.log("=== Aura Retail OS — Path A Demo Starting ===")

    scenario_1()
    scenario_2()
    scenario_3()
    scenario_4()
    scenario_5()

    print("\n" + "=" * 65)
    print("  All scenarios complete.")
    print("=" * 65)


if __name__ == "__main__":
    main()
