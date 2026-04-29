# Aura Retail OS

**Aura Retail OS** is an autonomous, modular smart-city retail kiosk simulation built using object-oriented programming principles. It demonstrates how a smart kiosk can adapt to different real-world environments such as hospitals, metro stations, campuses, and disaster-response zones.

The project implements multiple OOP design patterns, including **Command**, **Strategy**, **State**, **Memento**, **Chain of Responsibility**, and **Event-driven communication**.

## Project Overview

Aura Retail OS simulates a smart retail kiosk that can:

- Manage product inventory
- Process purchases and refunds
- Restock products
- Apply dynamic pricing strategies
- Handle operational states such as active, maintenance, and emergency mode
- Recover from simulated hardware failures
- Roll back inventory changes when a transaction fails
- Persist inventory and transaction data using JSON

This project was developed as part of an Object-Oriented Programming group project under **Path A: Adaptive Autonomous System**.

## Features

- Modular architecture with separate subsystems
- Inventory management
- GUI-based kiosk interface using PySide6
- CLI demo simulation
- Dynamic pricing strategies: Standard, Discount, and Emergency
- Payment strategy support
- Transaction execution using the Command pattern
- Failure handling using Chain of Responsibility
- State-based kiosk behavior
- Inventory rollback using the Memento pattern
- Event publishing for transaction success and failure
- JSON-based persistence for inventory and transactions

## Repository Structure

```text
Aura_Kiosk-main/
├── core/
│   ├── kiosk.py
│   ├── kiosk_interface.py
│   └── central_registry.py
├── inventory/
│   └── inventory.py
├── payment/
│   ├── command.py
│   └── strategy.py
├── pricing/
│   └── strategy.py
├── failure/
│   └── handler.py
├── state/
│   └── kiosk_state.py
├── memento/
│   └── memento.py
├── events/
│   └── event_bus.py
├── persistence/
│   └── storage.py
├── models/
│   └── product.py
├── ui/
│   └── main_window.py
├── demo/
│   ├── main.py
│   ├── inventory.json
│   └── transactions.json
├── run_gui.py
└── README.md
```

## Design Patterns Used

### 1. Command Pattern

Used for executing kiosk operations such as purchase, refund, and restock.

**File:** `payment/command.py`

**Main classes:**

- `PurchaseCommand`
- `RefundCommand`
- `RestockCommand`

### 2. Strategy Pattern

Used for interchangeable pricing and payment behavior.

**Files:**

- `pricing/strategy.py`
- `payment/strategy.py`

**Pricing strategies:**

- `StandardPricing`
- `DiscountPricing`
- `EmergencyPricing`

### 3. State Pattern

Used to control kiosk behavior based on its current operating mode.

**File:** `state/kiosk_state.py`

**States:**

- `ActiveState`
- `MaintenanceState`
- `EmergencyState`
- `PowerSavingState`

### 4. Memento Pattern

Used to save and restore inventory state during transaction rollback.

**File:** `memento/memento.py`

### 5. Chain of Responsibility Pattern

Used to handle failures through a sequence of handlers.

**File:** `failure/handler.py`

**Handlers:**

- `Retry`
- `Alert`

### 6. Event-driven Communication

Used to publish transaction events such as purchase success or failure.

**File:** `events/event_bus.py`

## Requirements

- Python 3.10 or above
- PySide6

Install PySide6:

```bash
pip install PySide6
```

If a `requirements.txt` file is available:

```bash
pip install -r requirements.txt
```

## How to Run

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/Aura_Kiosk-main.git
cd Aura_Kiosk-main
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment.

**Windows:**

```bash
venv\Scripts\activate
```

**macOS/Linux:**

```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install PySide6
```

### 4. Run the GUI Application

```bash
python run_gui.py
```

### 5. Run the CLI Demo

```bash
python demo/main.py
```

## Demo Scenarios

### Scenario 1: Dynamic Pricing

1. Start the GUI:

```bash
python run_gui.py
```

2. Select product `P1`.
3. Enter a quantity.
4. Choose a pricing strategy: `Standard`, `Discount`, or `Emergency`.
5. Click **Purchase**.

**Expected Result:**

The system calculates the total price based on the selected pricing strategy and displays the purchase result in the output section.

### Scenario 2: Simulated Hardware Failure and Rollback

1. Run the CLI demo:

```bash
python demo/main.py
```

2. The demo attempts a purchase with quantity greater than `3`.

**Expected Result:**

The system simulates a temporary failure, triggers the failure handler, restores the inventory to its previous state, and returns `Rollback`.

### Scenario 3: Emergency Mode Purchase Limit

Emergency mode restricts large purchases.

```python
from state.kiosk_state import EmergencyState
from payment.strategy import UPI
from pricing.strategy import StandardPricing

kiosk.state = EmergencyState()

print(interface.purchaseItem("P1", 3, UPI(), StandardPricing()))  # Blocked
print(interface.purchaseItem("P1", 2, UPI(), StandardPricing()))  # Success
```

**Expected Result:**

Purchases above the emergency limit are blocked, while smaller purchases are allowed.

### Scenario 4: Inventory Consistency

1. Trigger a purchase that causes a simulated failure.
2. Check inventory before and after the failed transaction.

**Expected Result:**

Inventory remains consistent after rollback. Failed transactions do not permanently reduce stock.

### Scenario 5: Failure Handler Customization

The failure handling chain can be customized.

```python
from failure.handler import Retry, Alert

handler = Retry(Alert())
kiosk = Kiosk(inventory, handler)
```

**Expected Result:**

The system attempts retry handling first. If retry handling cannot resolve the issue, the alert handler is used.

## Sample CLI Output

```text
=== PURCHASE ===

[KIOSK STATE]: ACTIVE
[COMMAND] Purchase
Paid via UPI: 200
[EVENT]: PurchaseSuccess
Success

=== FAILURE CASE ===

[KIOSK STATE]: ACTIVE
[COMMAND] Purchase
Paid via UPI: 500
[ERROR]: temporary
[EVENT]: PurchaseFailed
Rollback

=== RESTOCK ===
[COMMAND] Restock
Restocked

=== REFUND ===
[COMMAND] Refund
Refunded
```

## Key Classes

| Class | Purpose |
|---|---|
| `Kiosk` | Main controller for kiosk operations |
| `KioskInterface` | Simplified interface for external interaction |
| `Inventory` | Manages products and stock |
| `Product` | Represents product information |
| `PurchaseCommand` | Handles purchase execution |
| `RefundCommand` | Handles refund execution |
| `RestockCommand` | Handles restocking |
| `StandardPricing` | Calculates normal price |
| `DiscountPricing` | Applies discount pricing |
| `EmergencyPricing` | Applies emergency markup pricing |
| `ActiveState` | Allows normal operations |
| `MaintenanceState` | Blocks purchases |
| `EmergencyState` | Restricts purchase quantity |
| `Caretaker` | Saves and restores inventory state |
| `Retry` | Handles temporary failures |
| `Alert` | Sends failure alerts |

## Troubleshooting

### PySide6 is not installed

If you see this error:

```text
ModuleNotFoundError: No module named 'PySide6'
```

Install PySide6:

```bash
pip install PySide6
```

### GUI does not start

Make sure you are running the command from the project root:

```bash
python run_gui.py
```

### Product pricing does not update

Check that the GUI is passing the selected pricing strategy to:

```python
KioskInterface.purchaseItem()
```

You can also verify pricing manually:

```python
from pricing.strategy import StandardPricing, DiscountPricing, EmergencyPricing

base_price = 100

print(StandardPricing().calculate(base_price, 2))
print(DiscountPricing().calculate(base_price, 2))
print(EmergencyPricing().calculate(base_price, 2))
```

## Future Enhancements

- Add user authentication
- Add real payment gateway integration
- Improve transaction history tracking
- Add admin dashboard
- Add product search and filtering
- Add database support instead of JSON files
- Add detailed logging
- Add automated unit tests

## Conclusion

Aura Retail OS demonstrates how object-oriented programming and design patterns can be used to build a modular, adaptive kiosk system. The project focuses on clean architecture, loose coupling, transaction safety, and extensible behavior for smart-city retail environments.
