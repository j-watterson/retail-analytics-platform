"""Input schema and business-rule validation."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from email.utils import parseaddr

from .models import Order

REQUIRED_FIELDS = {
    "order_id",
    "order_timestamp",
    "customer_id",
    "customer_name",
    "customer_email",
    "product_id",
    "product_name",
    "category",
    "unit_price",
    "quantity",
    "status",
}
VALID_STATUSES = {"completed", "cancelled", "refunded"}


class ValidationError(ValueError):
    """A source row failed one or more data quality rules."""


def validate_headers(headers: list[str] | None) -> None:
    missing = REQUIRED_FIELDS - set(headers or [])
    if missing:
        raise ValidationError(f"Missing required columns: {', '.join(sorted(missing))}")


def parse_order(row: dict[str, str]) -> Order:
    errors: list[str] = []

    def required(name: str) -> str:
        value = (row.get(name) or "").strip()
        if not value:
            errors.append(f"{name} is required")
        return value

    order_id_raw = required("order_id")
    timestamp_raw = required("order_timestamp")
    customer_id = required("customer_id")
    customer_name = required("customer_name")
    customer_email = required("customer_email").lower()
    product_id = required("product_id")
    product_name = required("product_name")
    category = required("category")
    unit_price_raw = required("unit_price")
    quantity_raw = required("quantity")
    status = required("status").lower()

    try:
        order_id = int(order_id_raw)
        if order_id <= 0:
            raise ValueError
    except ValueError:
        errors.append("order_id must be a positive integer")
        order_id = 0

    try:
        order_timestamp = datetime.fromisoformat(timestamp_raw)
    except ValueError:
        errors.append("order_timestamp must be ISO-8601")
        order_timestamp = datetime.min

    try:
        unit_price = Decimal(unit_price_raw)
        if unit_price < 0:
            raise InvalidOperation
    except InvalidOperation:
        errors.append("unit_price must be a non-negative decimal")
        unit_price = Decimal(0)

    try:
        quantity = int(quantity_raw)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        errors.append("quantity must be a positive integer")
        quantity = 0

    parsed_name, parsed_email = parseaddr(customer_email)
    if parsed_name or parsed_email != customer_email or "@" not in customer_email:
        errors.append("customer_email must be a valid email address")
    if status not in VALID_STATUSES:
        errors.append(f"status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    if errors:
        raise ValidationError("; ".join(errors))

    return Order(
        order_id=order_id,
        order_timestamp=order_timestamp,
        customer_id=customer_id,
        customer_name=customer_name,
        customer_email=customer_email,
        product_id=product_id,
        product_name=product_name,
        category=category,
        unit_price=unit_price,
        quantity=quantity,
        status=status,
    )

