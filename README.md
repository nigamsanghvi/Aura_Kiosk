# 🛒 Aura Retail OS — Path A: Adaptive Autonomous System

> Python 3.10+ · OOP design patterns · IT620 Project

---

## Overview

**Aura Retail OS** is a modular retail kiosk simulation for the smart city of Zephyrus.
It uses **Path A — Adaptive Autonomous System**, demonstrating how a kiosk can dynamically
react to emergencies, hardware failures, pricing changes, and system events entirely through
object-oriented design patterns.

---

## Design Patterns Implemented

| # | Pattern | Location | Role |
|---|---------|----------|------|
| 1 | **Singleton** | `core/central_registry.py` | Global config, status, and event log |
| 2 | **Abstract Factory** | `core/kiosk_factory.py` | Create compatible kiosk component families |
| 3 | **State** | `state/kiosk_state.py` | Kiosk operational modes (Active/PowerSaving/Maintenance/Emergency) |
| 4 | **Strategy** | `pricing/strategy.py`, `payment/strategy.py` | Swappable pricing and payment algorithms |
| 5 | **Command** | `core/commands.py` | Encapsulate purchase/refund/restock as executable objects |
| 6 | **Chain of Responsibility** | `failure/handler.py` | Retry → Recalibrate → Alert failure recovery chain |
| 7 | **Memento** | `memento/memento.py` | Snapshot inventory before purchase; rollback on failure |
| 8 | **Observer** | `events/event_bus.py` | Event-driven communication (LowStock, HardwareFailure, Emergency) |
| 9 | **Facade** | `core/kiosk_interface.py` | Simplified external API hiding all subsystem complexity |

---

## Folder Structure

```
aura_retail_os/
├── main.py                     # Entry point — 5 simulation scenarios
├── core/
│   ├── central_registry.py     # SINGLETON — global store
│   ├── kiosk.py                # Kiosk core orchestrator
│   ├── kiosk_interface.py      # FACADE — external API
│   ├── kiosk_factory.py        # ABSTRACT FACTORY — Pharmacy/Food/Emergency
│   └── commands.py             # COMMAND — Purchase/Refund/Restock + Invoker
├── state/
│   └── kiosk_state.py          # STATE — Active/PowerSaving/Maintenance/Emergency
├── pricing/
│   └── strategy.py             # STRATEGY — Standard/Discount/Emergency pricing
├── payment/
│   └── strategy.py             # STRATEGY — UPI/Card/Wallet payment methods
├── failure/
│   └── handler.py              # CHAIN OF RESPONSIBILITY — Retry→Recalibrate→Alert
├── memento/
│   └── memento.py              # MEMENTO — inventory snapshot & rollback
├── events/
│   └── event_bus.py            # OBSERVER — EventBus + 3 built-in subscribers
├── inventory/
│   └── inventory.py            # Thread-safe inventory with derived attributes
├── models/
│   └── product.py              # Product data model
├── persistence/
│   └── storage.py              # JSON persistence
├── data/                       # JSON files (auto-created on run)
└── tests/
    └── test_aura_retail_os.py  # 41 unit tests
```

---

## How to Run

### Prerequisites

- Python 3.10+
- No external dependencies (stdlib only)

### Console Simulation (all 5 scenarios)

```bash
python main.py
```

### Unit Tests

```bash
python -m unittest tests.test_aura_retail_os -v
```

---

## Simulation Scenarios

### Scenario 1 — Dynamic Pricing Change
Demonstrates the **Strategy** pattern.  
Switches between Standard → Discount (10%) → Emergency pricing at runtime.  
Essential vs non-essential item pricing differs under Emergency mode.  
Payment method also swapped at runtime from Card to UPI.

### Scenario 2 — Kiosk State Transitions
Demonstrates the **State** pattern.  
Walks through Active → PowerSaving → Maintenance → Emergency → Active.  
Each state enforces different purchase rules automatically.

### Scenario 3 — Hardware Failure Recovery
Demonstrates **Chain of Responsibility** + **Memento**.  
Simulates a hardware fault, triggers the Retry→Recalibrate→Alert chain,  
then verifies inventory is properly rolled back via Memento if the purchase failed.

### Scenario 4 — Event-Driven Notifications
Demonstrates the **Observer** pattern.  
Three subscribers (MaintenanceService, SupplyChain, CityMonitor) automatically  
receive events: LowStockEvent, HardwareFailureEvent, EmergencyModeActivated.

### Scenario 5 — Purchase, Refund & JSON Persistence
Full transaction lifecycle: purchase → refund → restock.  
All data saved to `data/inventory_kiosk005.json` and `data/transactions_kiosk005.json`.

---

## OOP Principles

| Principle | Where demonstrated |
|-----------|-------------------|
| **Encapsulation** | `Inventory` private `_items` dict, `Product` private attributes |
| **Abstraction** | `KioskState`, `PricingStrategy`, `PaymentStrategy`, `FailureHandler` are all abstract |
| **Inheritance** | All concrete states/strategies/handlers extend abstract base classes |
| **Low coupling** | Kiosk talks to `EventBus` (not subscribers directly); commands use interfaces not concrete classes |

---

## System Constraints Addressed

| Constraint | Implementation |
|---|---|
| Purchase limit during emergencies | `EmergencyState.handle_purchase()` caps at 2 units |
| Atomic transactions | `PurchaseCommand` rolls back stock reservation if payment fails |
| Hardware dependency | `Inventory.available_stock()` returns 0 when `hw_ok=False` |
| Inventory consistency | Stock committed only after full command success |
| Concurrent transactions | `Inventory` uses `threading.Lock` on all mutations |
