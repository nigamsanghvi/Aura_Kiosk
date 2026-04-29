# Role: Core product data model

from __future__ import annotations


class Product:
    """Represents a single retail product available in a kiosk."""

    def __init__(
        self,
        product_id: str,
        name: str,
        base_price: float,
        category: str = "general",
        is_essential: bool = False,
        requires_hardware: list[str] | None = None,
    ) -> None:
        self._id = product_id
        self._name = name
        self._base_price = base_price
        self._category = category
        self._is_essential = is_essential
        self._requires_hardware: list[str] = requires_hardware or []

    @property
    def product_id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def base_price(self) -> float:
        return self._base_price

    @property
    def category(self) -> str:
        return self._category

    @property
    def is_essential(self) -> bool:
        return self._is_essential

    @property
    def requires_hardware(self) -> list[str]:
        return list(self._requires_hardware)

    def to_dict(self) -> dict:
        return {
            "product_id": self._id,
            "name": self._name,
            "base_price": self._base_price,
            "category": self._category,
            "is_essential": self._is_essential,
            "requires_hardware": self._requires_hardware,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        return cls(
            product_id=data["product_id"],
            name=data["name"],
            base_price=data["base_price"],
            category=data.get("category", "general"),
            is_essential=data.get("is_essential", False),
            requires_hardware=data.get("requires_hardware", []),
        )

    def __repr__(self) -> str:
        return f"Product({self._id!r}, {self._name!r}, ${self._base_price:.2f})"
