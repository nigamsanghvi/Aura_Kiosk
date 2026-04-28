from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
	sys.path.insert(0, str(PROJECT_ROOT))

from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from inventory.inventory import Inventory
from models.product import Product
from payment.strategy import UPI
from pricing.strategy import StandardPricing
from failure.handler import Retry, Alert

inventory = Inventory()
inventory.add_product(Product("P1","Medicine",100),10)

handler = Retry(Alert())
kiosk = Kiosk(inventory, handler)
interface = KioskInterface(kiosk)

print("\n=== PURCHASE ===")
print(interface.purchaseItem("P1", 2, UPI(), StandardPricing()))

print("\n=== FAILURE CASE ===")
print(interface.purchaseItem("P1", 5, UPI(), StandardPricing()))

print("\n=== RESTOCK ===")
print(interface.restockInventory("P1", 5))

print("\n=== REFUND ===")
print(interface.refundTransaction("P1"))