from __future__ import annotations
from typing import Any
from models.product import Product


class Inventory:
    LOW_STOCK_THRESHOLD = 5

    def __init__(self) -> None:
        # items: pid -> {"product": Product, "total": int, "reserved": int, "hw_ok": bool}
        self.items: dict[str, dict[str, Any]] = {}

    def add_product(self, product: Product, qty: int) -> None:
        pid = product.product_id
        self.items[pid] = {
            "product": product,
            "total": int(qty),
            "reserved": 0,
            "hw_ok": True,
        }

    def get_product(self, pid: str) -> Product | None:
        return self.items.get(pid, {}).get("product")

    def available_stock(self, pid: str) -> int:
        item = self.items.get(pid)
        if not item:
            return 0
        if not item.get("hw_ok", True):
            return 0
        return max(0, item["total"] - item["reserved"])

    def check_stock(self, pid: str, qty: int) -> bool:
        return self.available_stock(pid) >= qty

    def reserve(self, pid: str, qty: int) -> bool:
        item = self.items.get(pid)
        if not item:
            return False
        avail = self.available_stock(pid)
        if avail >= qty:
            item["reserved"] += qty
            return True
        return False

    def release_reservation(self, pid: str, qty: int) -> None:
        item = self.items.get(pid)
        if not item:
            return
        item["reserved"] = max(0, item["reserved"] - qty)

    def commit_deduction(self, pid: str, qty: int) -> bool:
        item = self.items.get(pid)
        if not item:
            return False
        # Deduct from total and clear reserved
        deduct = min(qty, item["reserved"])
        item["total"] = max(0, item["total"] - deduct)
        item["reserved"] = max(0, item["reserved"] - deduct)
        return True

    def restock(self, pid: str, qty: int) -> bool:
        item = self.items.get(pid)
        if not item:
            return False
        item["total"] += int(qty)
        return True

    def return_stock(self, pid: str, qty: int) -> None:
        item = self.items.get(pid)
        if not item:
            return
        item["total"] += int(qty)

    def is_low_stock(self, pid: str) -> bool:
        return self.available_stock(pid) <= self.LOW_STOCK_THRESHOLD

    def set_hardware_ok(self, pid: str, ok: bool) -> None:
        item = self.items.get(pid)
        if not item:
            return
        item["hw_ok"] = bool(ok)

    def get_price(self, pid: str) -> float:
        item = self.items.get(pid)
        if not item:
            return 0.0
        return item["product"].base_price

    def get_state(self) -> dict[str, Any]:
        # snapshot of totals/reserved/hw_ok per pid
        return {
            pid: {
                "total": data["total"],
                "reserved": data["reserved"],
                "hw_ok": data["hw_ok"],
            }
            for pid, data in self.items.items()
        }

    def restore(self, state: dict[str, Any]) -> None:
        for pid, vals in state.items():
            if pid in self.items:
                self.items[pid]["total"] = int(
                    vals.get("total", self.items[pid]["total"])
                )
                self.items[pid]["reserved"] = int(
                    vals.get("reserved", self.items[pid]["reserved"])
                )
                self.items[pid]["hw_ok"] = bool(
                    vals.get("hw_ok", self.items[pid]["hw_ok"])
                )

    def list_all(self) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for pid, data in self.items.items():
            p = data["product"]
            rows.append(
                {
                    "product_id": pid,
                    "name": p.name,
                    "base_price": p.base_price,
                    "available": self.available_stock(pid),
                    "requires_hardware": list(p.requires_hardware),
                }
            )
        return rows
