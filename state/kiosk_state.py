
from abc import ABC, abstractmethod

class KioskState(ABC):
    @abstractmethod
    def handle_purchase(self, qty): pass
    @abstractmethod
    def get_name(self): pass

class ActiveState(KioskState):
    def handle_purchase(self, qty): return True
    def get_name(self): return "ACTIVE"

class MaintenanceState(KioskState):
    def handle_purchase(self, qty): return False
    def get_name(self): return "MAINTENANCE"

class EmergencyState(KioskState):
    def handle_purchase(self, qty): return qty <= 2
    def get_name(self): return "EMERGENCY"

class PowerSavingState(KioskState):
    def handle_purchase(self, qty):
        print("[PowerSaving] Limited operation")
        return True

    def get_name(self):
        return "POWER_SAVING"