# Pattern: Observer
# Role: Decoupled event-driven communication between subsystems

from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Callable


# ── Observer interface ────────────────────────────────────────
class IEventSubscriber(ABC):
    """Abstract observer that receives kiosk system events."""

    @abstractmethod
    def on_event(self, event_type: str, payload: dict[str, Any]) -> None: ...


# ── Event types ───────────────────────────────────────────────
class EventType:
    PURCHASE_SUCCESS = "PurchaseSuccess"
    PURCHASE_FAILED = "PurchaseFailed"
    REFUND_SUCCESS = "RefundSuccess"
    RESTOCK_DONE = "RestockDone"
    LOW_STOCK = "LowStockEvent"
    HARDWARE_FAILURE = "HardwareFailureEvent"
    HARDWARE_RECALIBRATED = "HardwareRecalibrated"
    EMERGENCY_ACTIVATED = "EmergencyModeActivated"
    EMERGENCY_DEACTIVATED = "EmergencyModeDeactivated"
    STATE_CHANGED = "KioskStateChanged"
    PRICING_CHANGED = "PricingStrategyChanged"
    TRANSACTION_ROLLBACK = "TransactionRollback"


# ── Event Bus (Subject) ───────────────────────────────────────
class EventBus:
    """
    PATTERN: Observer (Subject / Publisher)
    Central publish-subscribe bus. Subsystems publish events here;
    subscribers receive them without direct coupling to the publisher.
    """

    def __init__(self) -> None:
        self._subscribers: dict[str, list[IEventSubscriber]] = {}
        self._log: list[dict[str, Any]] = []

    def subscribe(self, event_type: str, subscriber: IEventSubscriber) -> None:
        self._subscribers.setdefault(event_type, []).append(subscriber)

    def unsubscribe(self, event_type: str, subscriber: IEventSubscriber) -> None:
        subs = self._subscribers.get(event_type, [])
        if subscriber in subs:
            subs.remove(subscriber)

    def publish(self, event_type: str, payload: dict[str, Any] | None = None) -> None:
        payload = payload or {}
        payload["event_type"] = event_type
        payload["timestamp"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        entry = dict(payload)
        self._log.append(entry)

        for subscriber in self._subscribers.get(event_type, []):
            subscriber.on_event(event_type, payload)

    def get_log(self) -> list[dict[str, Any]]:
        return list(self._log)


# ── Built-in subscribers ──────────────────────────────────────
class MaintenanceServiceSubscriber(IEventSubscriber):
    """
    PATTERN: Observer (Concrete Observer)
    Simulates an automated maintenance service that reacts to hardware failures.
    """

    def on_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type == EventType.HARDWARE_FAILURE:
            print(
                f"[MaintenanceService] Hardware failure detected: {payload.get('detail', '')} — scheduling technician."
            )
        elif event_type == EventType.HARDWARE_RECALIBRATED:
            print(
                f"[MaintenanceService] Hardware recalibrated successfully: {payload.get('detail', '')}"
            )


class SupplyChainSubscriber(IEventSubscriber):
    """
    PATTERN: Observer (Concrete Observer)
    Simulates an automated supply chain system that reacts to low stock.
    """

    def on_event(self, event_type: str, payload: dict[str, Any]) -> None:
        if event_type == EventType.LOW_STOCK:
            pid = payload.get("product_id", "?")
            qty = payload.get("current_qty", 0)
            print(
                f"[SupplyChain] Low stock alert for {pid} (qty={qty}). Initiating reorder."
            )


class CityMonitoringSubscriber(IEventSubscriber):
    """
    PATTERN: Observer (Concrete Observer)
    Simulates the city monitoring center receiving critical alerts.
    """

    def on_event(self, event_type: str, payload: dict[str, Any]) -> None:
        high_priority = {
            EventType.EMERGENCY_ACTIVATED,
            EventType.HARDWARE_FAILURE,
            EventType.TRANSACTION_ROLLBACK,
        }
        if event_type in high_priority:
            print(
                f"[CityMonitor] ⚠ HIGH PRIORITY — {event_type}: {payload.get('detail', '')}"
            )
        else:
            print(f"[CityMonitor] {event_type}: {payload.get('detail', '')}")
