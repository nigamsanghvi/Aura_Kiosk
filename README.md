# Aura Retail OS

Designing an Autonomous Modular Smart-City Retail Infrastructure (Path A — Adaptive Autonomous System)

## Project Overview

Aura Retail OS is a modular kiosk platform designed for adaptive operation across multiple deployment environments (hospitals, metro stations, campuses, disaster zones). The system demonstrates object-oriented design and patterns including Command, Strategy, State, Memento, Chain of Responsibility, and Event-driven communication.

## Repository Layout

- `core/` — Kiosk core, `Kiosk` and `KioskInterface` implementations
- `inventory/` — Inventory management and persistence
- `payment/` — Payment command and strategy implementations
- `pricing/` — Pricing strategies (Standard, Discount, Emergency)
- `failure/` — Failure handlers (retry, alert)
- `state/` — Kiosk operational states (Active, Maintenance, Emergency)
- `memento/` — Inventory state saving and restore (rollback)
- `ui/` — GUI (`run_gui.py` launches UI)
- `demo/` — Small demo scripts and sample data

## Requirements Implemented (high level)

- Encapsulation, abstraction, inheritance, and loose coupling between subsystems.
- JSON persistence for inventory and transactions (see `persistence/`).
- `CentralRegistry` and `KioskInterface` expose simplified operations: `purchaseItem()`, `refundTransaction()`, `restockInventory()`, `runDiagnostics()`.
- Transaction system implemented with Command pattern (`payment/command.py`).
- Adaptive Path A features: dynamic pricing, operational states, failure handling chain, transaction rollback via Memento.

---

**How to run (quick)**

1. Create and activate virtualenv (if not already):

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies (if any). This project uses PySide6 for GUI; install with:

```bash
pip install -r requirements.txt
# If requirements.txt not present, install PySide6 directly:
pip install PySide6
```

3. Launch the GUI:

```bash
python run_gui.py
```

4. Run the demo script (CLI simulation):

```bash
python demo/main.py
```

---

**Simulation Demonstrations & Step-by-step Scenarios**

Below are reproducible scenarios that demonstrate Path A capabilities. Each scenario lists the steps and the expected output.

- **Scenario 1 — Dynamic Pricing Change (Discount / Emergency)**

  Steps:
  - Start the GUI with `python run_gui.py` (or run `python demo/main.py` to see CLI output).
  - Select product `P1` (or enter `P1` in Product ID).
  - Enter a quantity (e.g., `1`).
  - Choose `Discount` from the Pricing Strategy dropdown and click `Purchase`.
  - Expected (GUI): a purchase message showing applied pricing (in the demo CLI you will see the computed amount printed).

  Notes: If the GUI does not display the computed price, run the CLI demo (`python demo/main.py`) which prints pricing computation and shows the effect of different strategies.

- **Scenario 2 — Hardware Failure Recovery (Automatic Retry + Rollback)**

  Steps:
  - Start GUI or run `python demo/main.py`.
  - Choose `P1` and use quantity `5` (any value greater than 3 triggers a simulated temporary hardware error in the core logic).
  - Click `Purchase`.
  - Expected: The system will detect the simulated failure, the Chain-of-Responsibility will recommend a retry, the kiosk will attempt an automatic retry, and either complete successfully (recover) or restore state and report a rollback.

  CLI expected output (from `demo/main.py`):
  - `=== FAILURE CASE ===`
  - `Rollback` or `Success (Recovered)` depending on retries and handler behavior.

- **Scenario 3 — Emergency Mode Enforcement (Purchase Limit)**

  Steps:
  - Launch a small Python snippet or modify `demo/main.py` to set kiosk state to `EmergencyState`:

  ```python
  from state.kiosk_state import EmergencyState
  kiosk.state = EmergencyState()
  interface = KioskInterface(kiosk)
  print(interface.purchaseItem('P1', 3, UPI(), StandardPricing()))  # should be blocked
  print(interface.purchaseItem('P1', 2, UPI(), StandardPricing()))  # should be allowed
  ```

  - Expected: Purchases exceeding the emergency limit (default 2) are blocked with a `Blocked` response.

- **Scenario 4 — Transaction Atomicity & Inventory Consistency**

  Steps:
  - Trigger a purchase that causes a simulated failure (qty > 3) and confirm that after rollback the inventory counts are unchanged from before the transaction.
  - Use `demo/main.py` or the GUI to inspect inventory before and after the failed transaction.

  Expected: Inventory restored to previous state after rollback.

- **Scenario 5 — Failure Handler Customization**

  Steps:
  - Inspect or change the handlers connected in `demo/main.py`:

  ```python
  from failure.handler import Retry, Alert
  handler = Retry(Alert())
  kiosk = Kiosk(inventory, handler)
  ```

  - Add or reorder handlers to test different recovery flows (e.g., add a `RecalibrateHandler` before `Alert`).

  Expected: Handler order changes how failures are resolved (retry, recalibrate, then alert).

---

**Troubleshooting / Tips**

- If `Discount` or `Emergency` pricing appears to "do nothing" in the GUI, verify the GUI is passing the chosen pricing strategy to `KioskInterface.purchaseItem()` (the CLI `demo/main.py` shows pricing behavior clearly).
- To inspect pricing logic quickly, run a Python REPL in project root:

```python
>>> from pricing.strategy import DiscountPricing, EmergencyPricing, StandardPricing
>>> base = 100
>>> DiscountPricing().calculate(base, 2)
>>> EmergencyPricing().calculate(base, 3)
```

- Logs and prints from `core/kiosk.py` provide step-by-step traces for payment execution, simulated hardware failures, retries, and rollback.

---
