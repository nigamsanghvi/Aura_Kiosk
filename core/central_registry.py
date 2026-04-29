# Pattern: Singleton
# Role: System-wide configuration, status, and event logging

from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Any, Optional


# PATTERN: Singleton
class CentralRegistry:
    """
    Single global store for kiosk configuration, runtime status, and event log.
    Thread-safe at the class level; a single instance is guaranteed.
    """

    _instance: CentralRegistry | None = None

    def __new__(cls) -> CentralRegistry:
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._config: dict[str, Any] = {}
            inst._status: dict[str, Any] = {}
            inst._event_log: list[str] = []
            cls._instance = inst
        return cls._instance

    @classmethod
    def get_instance(cls) -> CentralRegistry:
        return cls()

    # ── Config ────────────────────────────────────────────────
    def set_config(self, key: str, value: Any) -> None:
        self._config[key] = value

    def get_config(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    # ── Runtime status ────────────────────────────────────────
    def set_status(self, key: str, value: Any) -> None:
        self._status[key] = value

    def get_status(self, key: str, default: Any = None) -> Any:
        return self._status.get(key, default)

    # ── Event log ─────────────────────────────────────────────
    def log(self, message: str) -> None:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        entry = f"[{ts}] {message}"
        self._event_log.append(entry)
        print(f"[REGISTRY] {entry}")

    def get_event_log(self) -> list[str]:
        return list(self._event_log)

    # ── Persistence ───────────────────────────────────────────
    def load_config(self, filepath: str) -> None:
        try:
            with open(filepath) as f:
                data = json.load(f)
            self._config.update(data)
        except FileNotFoundError:
            pass

    def save_config(self, filepath: str) -> None:
        with open(filepath, "w") as f:
            json.dump(self._config, f, indent=2)
