import csv
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from retail_analytics.config import PipelineConfig
from retail_analytics.pipeline import run_pipeline


HEADERS = [
    "order_id", "order_timestamp", "customer_id", "customer_name",
    "customer_email", "product_id", "product_name", "category",
    "unit_price", "quantity", "status",
]


class PipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "orders.csv"
        self.database = self.root / "warehouse.db"
        self.rejected = self.root / "rejected.csv"
        self.project_root = Path(__file__).resolve().parents[1]
        self.config = PipelineConfig(self.source, self.database, self.rejected)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def write_rows(self, rows: list[list[str]]) -> None:
        with self.source.open("w", newline="", encoding="utf-8") as target:
            writer = csv.writer(target)
            writer.writerow(HEADERS)
            writer.writerows(rows)

    def test_pipeline_loads_valid_and_quarantines_invalid_rows(self) -> None:
        self.write_rows([
            [
                "1", "2026-01-01T12:00:00", "C1", "Avery", "a@example.com",
                "P1", "Backpack", "Outdoor", "50.00", "2", "completed",
            ],
            [
                "2", "2026-01-01T12:05:00", "C2", "Morgan", "m@example.com",
                "P2", "Bottle", "Outdoor", "20.00", "0", "completed",
            ],
        ])

        result = run_pipeline(self.config, self.project_root)

        self.assertEqual(result.status, "completed")
        self.assertEqual((result.rows_read, result.rows_loaded, result.rows_rejected), (2, 1, 1))
        self.assertTrue(self.rejected.exists())
        with sqlite3.connect(self.database) as connection:
            count = connection.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0]
            revenue = connection.execute(
                "SELECT revenue FROM vw_daily_sales"
            ).fetchone()[0]
        self.assertEqual(count, 1)
        self.assertEqual(revenue, 100)

    def test_same_source_checksum_is_skipped(self) -> None:
        self.write_rows([[
            "1", "2026-01-01T12:00:00", "C1", "Avery", "a@example.com",
            "P1", "Backpack", "Outdoor", "50.00", "2", "completed",
        ]])

        first = run_pipeline(self.config, self.project_root)
        second = run_pipeline(self.config, self.project_root)

        self.assertEqual(first.status, "completed")
        self.assertEqual(second.status, "skipped")
        with sqlite3.connect(self.database) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM fact_orders").fetchone()[0],
                1,
            )


if __name__ == "__main__":
    unittest.main()

