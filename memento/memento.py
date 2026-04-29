# Pattern: Memento
# Role: Save and restore inventory state for transaction rollback

from __future__ import annotations
from typing import Any


# PATTERN: Memento (Memento)
class InventoryMemento:
    """Opaque snapshot of inventory state. Only the Caretaker stores these."""

    def __init__(self, state: dict[str, Any]) -> None:
        # Deep-copy to prevent mutation of saved state
        import copy

        self._state = copy.deepcopy(state)

    def get_state(self) -> dict[str, Any]:
        import copy

        return copy.deepcopy(self._state)


# PATTERN: Memento (Caretaker)
class TransactionCaretaker:
    """
    Maintains a stack of Mementos.
    Before each purchase attempt the Kiosk calls save(); on failure, undo().
    """

    def __init__(self) -> None:
        self._history: list[InventoryMemento] = []

    def save(self, state: dict[str, Any]) -> None:
        self._history.append(InventoryMemento(state))

    def undo(self) -> dict[str, Any] | None:
        if self._history:
            return self._history.pop().get_state()
        return None

    def has_snapshot(self) -> bool:
        return bool(self._history)
