# Pattern: Abstract Factory
# Role: Create compatible families of kiosk components

from __future__ import annotations
from abc import ABC, abstractmethod

from core.central_registry import CentralRegistry
from core.kiosk import Kiosk
from core.kiosk_interface import KioskInterface
from events.event_bus import EventBus
from failure.handler import build_default_chain
from inventory.inventory import Inventory
from models.product import Product


# PATTERN: Abstract Factory (Abstract)
class AbstractKioskFactory(ABC):
    """
    Declares the interface for creating all kiosk components.
    Each concrete factory creates components that work together.
    """

    @abstractmethod
    def create_inventory(self) -> Inventory: ...

    @abstractmethod
    def get_default_products(self) -> list[tuple[Product, int]]: ...

    @abstractmethod
    def get_default_pricing(self):
        """Returns the default PricingStrategy for this kiosk type."""
        ...

    @abstractmethod
    def get_default_payment(self):
        """Returns the default PaymentStrategy for this kiosk type."""
        ...

    @abstractmethod
    def get_kiosk_type(self) -> str: ...

    def create_kiosk(self, kiosk_id: str, event_bus: EventBus) -> KioskInterface:
        """Template: build a fully-wired Kiosk and wrap it in the Facade."""
        inventory = self.create_inventory()
        for product, qty in self.get_default_products():
            inventory.add_product(product, qty)

        kiosk = Kiosk(
            kiosk_id=kiosk_id,
            inventory=inventory,
            failure_handler=build_default_chain(),
            event_bus=event_bus,
            default_pricing=self.get_default_pricing(),
            default_payment=self.get_default_payment(),
        )
        CentralRegistry.get_instance().log(
            f"Factory created {self.get_kiosk_type()} kiosk: {kiosk_id}"
        )
        return KioskInterface(kiosk)


# ── Concrete factories ─────────────────────────────────────────


# PATTERN: Abstract Factory (Concrete — Pharmacy)
class PharmacyKioskFactory(AbstractKioskFactory):
    def create_inventory(self) -> Inventory:
        return Inventory()

    def get_default_products(self) -> list[tuple[Product, int]]:
        return [
            (
                Product(
                    "MED-001", "Paracetamol 500mg", 25.0, "medicine", is_essential=True
                ),
                100,
            ),
            (Product("MED-002", "Bandage", 15.0, "medicine", is_essential=True), 60),
            (Product("MED-003", "Antiseptic", 30.0, "medicine", is_essential=True), 40),
            (Product("MED-004", "Vitamin C Tablets", 20.0, "supplement"), 80),
        ]

    def get_default_pricing(self):
        from pricing.strategy import StandardPricing

        return StandardPricing()

    def get_default_payment(self):
        from payment.strategy import CardPayment

        return CardPayment()

    def get_kiosk_type(self) -> str:
        return "PharmacyKiosk"


# PATTERN: Abstract Factory (Concrete — Food)
class FoodKioskFactory(AbstractKioskFactory):
    def create_inventory(self) -> Inventory:
        return Inventory()

    def get_default_products(self) -> list[tuple[Product, int]]:
        return [
            (Product("FOOD-001", "Sandwich", 80.0, "food"), 30),
            (
                Product(
                    "FOOD-002", "Bottled Water", 20.0, "beverage", is_essential=True
                ),
                120,
            ),
            (Product("FOOD-003", "Burger", 95.0, "food"), 25),
            (Product("FOOD-004", "Salad Box", 65.0, "food"), 20),
        ]

    def get_default_pricing(self):
        from pricing.strategy import DiscountPricing

        return DiscountPricing(0.05)  # 5% everyday discount

    def get_default_payment(self):
        from payment.strategy import UPIPayment

        return UPIPayment()

    def get_kiosk_type(self) -> str:
        return "FoodKiosk"


# PATTERN: Abstract Factory (Concrete — Emergency Relief)
class EmergencyReliefKioskFactory(AbstractKioskFactory):
    def create_inventory(self) -> Inventory:
        return Inventory()

    def get_default_products(self) -> list[tuple[Product, int]]:
        return [
            (
                Product(
                    "EMRG-001",
                    "Emergency Water Pouch",
                    12.0,
                    "essential",
                    is_essential=True,
                ),
                200,
            ),
            (
                Product(
                    "EMRG-002", "First Aid Kit", 45.0, "essential", is_essential=True
                ),
                80,
            ),
            (
                Product(
                    "EMRG-003", "Thermal Blanket", 35.0, "essential", is_essential=True
                ),
                60,
            ),
            (
                Product(
                    "EMRG-004", "Paracetamol Strip", 10.0, "medicine", is_essential=True
                ),
                150,
            ),
        ]

    def get_default_pricing(self):
        from pricing.strategy import EmergencyPricing

        return EmergencyPricing()

    def get_default_payment(self):
        from payment.strategy import WalletPayment

        return WalletPayment()

    def get_kiosk_type(self) -> str:
        return "EmergencyReliefKiosk"
