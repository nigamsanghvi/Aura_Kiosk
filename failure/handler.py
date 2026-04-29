# Pattern: Chain of Responsibility
# Role: Sequence of failure recovery handlers

from __future__ import annotations
from abc import ABC, abstractmethod


# PATTERN: Chain of Responsibility (Abstract Handler)
class FailureHandler(ABC):
    def __init__(self, successor: FailureHandler | None = None) -> None:
        self._next = successor

    def set_next(self, handler: FailureHandler) -> FailureHandler:
        self._next = handler
        return handler

    @abstractmethod
    def handle(self, issue: str) -> str: ...

    def _pass_to_next(self, issue: str) -> str:
        if self._next:
            return self._next.handle(issue)
        return f"UNHANDLED: {issue}"


# PATTERN: Chain of Responsibility (Concrete — Retry)
class RetryHandler(FailureHandler):
    """
    First in chain. Attempts automatic retry for transient failures.
    """

    TRANSIENT_KEYWORDS = {"timeout", "temporary", "transient", "busy"}

    def handle(self, issue: str) -> str:
        if any(kw in issue.lower() for kw in self.TRANSIENT_KEYWORDS):
            print(f"  [RetryHandler] Transient issue detected. Retrying... ({issue})")
            # Simulate retry success for transient errors
            return "RETRY_SUCCESS"
        return self._pass_to_next(issue)


# PATTERN: Chain of Responsibility (Concrete — Recalibrate)
class RecalibrateHandler(FailureHandler):
    """
    Second in chain. Attempts hardware recalibration for mechanical errors.
    """

    HARDWARE_KEYWORDS = {
        "motor",
        "sensor",
        "dispenser",
        "jam",
        "hardware",
        "mechanical",
    }

    def handle(self, issue: str) -> str:
        if any(kw in issue.lower() for kw in self.HARDWARE_KEYWORDS):
            print(
                f"  [RecalibrateHandler] Hardware issue detected. Recalibrating... ({issue})"
            )
            return "RECALIBRATED"
        return self._pass_to_next(issue)


# PATTERN: Chain of Responsibility (Concrete — Alert)
class AlertHandler(FailureHandler):
    """
    Final handler. Escalates to technician when no earlier handler resolves.
    """

    def handle(self, issue: str) -> str:
        print(f"  [AlertHandler] Escalating to technician! Unresolved issue: {issue}")
        return "ALERT_SENT"


# ── Factory helper ─────────────────────────────────────────────
def build_default_chain() -> FailureHandler:
    """Constructs the default handler chain: Retry → Recalibrate → Alert."""
    alert = AlertHandler()
    recal = RecalibrateHandler(alert)
    retry = RetryHandler(recal)
    return retry
