from decimal import Decimal
import unittest

from retail_analytics.validation import ValidationError, parse_order, validate_headers


VALID_ROW = {
    "order_id": "42",
    "order_timestamp": "2026-01-10T12:30:00",
    "customer_id": "C001",
    "customer_name": "Avery Chen",
    "customer_email": "avery@example.com",
    "product_id": "P001",
    "product_name": "Trail Backpack",
    "category": "Outdoor",
    "unit_price": "89.99",
    "quantity": "2",
    "status": "completed",
}


class ValidationTests(unittest.TestCase):
    def test_valid_row_is_converted_to_order(self) -> None:
        order = parse_order(VALID_ROW)
        self.assertEqual(order.order_id, 42)
        self.assertEqual(order.unit_price, Decimal("89.99"))
        self.assertEqual(order.gross_revenue, Decimal("179.98"))

    def test_multiple_rule_failures_are_reported(self) -> None:
        row = {**VALID_ROW, "quantity": "0", "status": "unknown"}
        with self.assertRaises(ValidationError) as context:
            parse_order(row)
        self.assertIn("quantity must be a positive integer", str(context.exception))
        self.assertIn("status must be one of", str(context.exception))

    def test_missing_header_is_rejected(self) -> None:
        headers = list(VALID_ROW)
        headers.remove("product_id")
        with self.assertRaisesRegex(ValidationError, "product_id"):
            validate_headers(headers)


if __name__ == "__main__":
    unittest.main()

