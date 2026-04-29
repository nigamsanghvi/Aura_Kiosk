# ============================================================
# Module: state/kiosk_state.py
# Pattern: State
# Role: Kiosk operational modes — each state controls purchase behaviour
# ============================================================

from __future__ import annotations
from abc import ABC, abstractmethod


# PATTERN: State (Abstract State)
class KioskState(ABC):
    """Abstract base for all kiosk operational states."""

    @abstractmethod
    def handle_purchase(self, qty: int) -> tuple[bool, str]:
        """Return (allowed, reason)."""
        ...

    @abstractmethod
    def get_name(self) -> str: ...

    @abstractmethod
    def describe(self) -> str: ...

    def __repr__(self) -> str:
        return self.get_name()


# PATTERN: State (Concrete State — Active)
class ActiveState(KioskState):
    """Normal operating mode. All purchases allowed."""

    def handle_purchase(self, qty: int) -> tuple[bool, str]:
        return True, "OK"

    def get_name(self) -> str:
        return "ACTIVE"

    def describe(self) -> str:
        return "Kiosk is fully operational. All purchases allowed."


# PATTERN: State (Concrete State — PowerSaving)
class PowerSavingState(KioskState):
    """
    Reduced-operation mode. Purchases still allowed but limited to small
    quantities to conserve resources.
    """

    MAX_QTY = 5

    def handle_purchase(self, qty: int) -> tuple[bool, str]:
        if qty > self.MAX_QTY:
            return (
                False,
                f"Power-saving mode limits purchases to {self.MAX_QTY} units per transaction.",
            )
        return True, "OK"

    def get_name(self) -> str:
        return "POWER_SAVING"

    def describe(self) -> str:
        return f"Power-saving mode active. Purchases limited to {self.MAX_QTY} units."


# PATTERN: State (Concrete State — Maintenance)
class MaintenanceState(KioskState):
    """Maintenance mode. All purchases blocked until technician clears."""

    def handle_purchase(self, qty: int) -> tuple[bool, str]:
        return False, "Kiosk is under maintenance. Purchases not available."

    def get_name(self) -> str:
        return "MAINTENANCE"

    def describe(self) -> str:
        return "Kiosk is undergoing scheduled maintenance. No purchases available."


# PATTERN: State (Concrete State — Emergency)
class EmergencyState(KioskState):
    """
    Emergency lockdown mode.
    Essential items only; quantity capped to conserve supply.
    """

    MAX_QTY = 2

    def handle_purchase(self, qty: int) -> tuple[bool, str]:
        if qty > self.MAX_QTY:
            return (
                False,
                f"Emergency lockdown: essential-item purchases capped at {self.MAX_QTY} units.",
            )
        return True, "OK"

    def get_name(self) -> str:
        return "EMERGENCY"

    def describe(self) -> str:
        return f"Emergency lockdown active. Max {self.MAX_QTY} units per purchase. Essential items only."
