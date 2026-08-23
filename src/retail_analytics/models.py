"""Validated domain models used by the pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class Order:
    order_id: int
    order_timestamp: datetime
    customer_id: str
    customer_name: str
    customer_email: str
    product_id: str
    product_name: str
    category: str
    unit_price: Decimal
    quantity: int
    status: str

    @property
    def gross_revenue(self) -> Decimal:
        return self.unit_price * self.quantity

