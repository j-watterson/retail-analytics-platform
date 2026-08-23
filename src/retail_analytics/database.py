"""SQLite warehouse operations."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .models import Order


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Warehouse:
    def __init__(self, database_path: Path, sql_dir: Path):
        self.database_path = database_path
        self.sql_dir = sql_dir
        self.connection: sqlite3.Connection | None = None

    def __enter__(self) -> "Warehouse":
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        if self.connection:
            self.connection.close()

    @property
    def db(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("Warehouse connection is not open")
        return self.connection

    def initialize(self) -> None:
        for filename in ("schema.sql", "analytics_views.sql"):
            self.db.executescript((self.sql_dir / filename).read_text(encoding="utf-8"))
        self.db.commit()

    def checksum_loaded(self, checksum: str) -> bool:
        row = self.db.execute(
            "SELECT 1 FROM etl_runs WHERE source_checksum = ? AND status = 'completed'",
            (checksum,),
        ).fetchone()
        return row is not None

    def start_run(self, run_id: str, source_file: str, checksum: str) -> None:
        self.db.execute(
            """
            INSERT INTO etl_runs(run_id, source_file, source_checksum, started_at, status)
            VALUES (?, ?, ?, ?, 'running')
            """,
            (run_id, source_file, checksum, utc_now()),
        )
        self.db.commit()

    def finish_run(
        self, run_id: str, status: str, rows_read: int, rows_loaded: int,
        rows_rejected: int, error_message: str | None = None,
    ) -> None:
        self.db.execute(
            """
            UPDATE etl_runs
            SET completed_at = ?, status = ?, rows_read = ?, rows_loaded = ?,
                rows_rejected = ?, error_message = ?
            WHERE run_id = ?
            """,
            (
                utc_now(), status, rows_read, rows_loaded, rows_rejected,
                error_message, run_id,
            ),
        )
        self.db.commit()

    def upsert_order(self, order: Order, source_file: str) -> None:
        now = utc_now()
        self.db.execute(
            """
            INSERT INTO dim_customers(customer_id, customer_name, customer_email, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
                customer_name = excluded.customer_name,
                customer_email = excluded.customer_email,
                updated_at = excluded.updated_at
            """,
            (order.customer_id, order.customer_name, order.customer_email, now),
        )
        self.db.execute(
            """
            INSERT INTO dim_products(
                product_id, product_name, category, current_unit_price, updated_at
            )
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(product_id) DO UPDATE SET
                product_name = excluded.product_name,
                category = excluded.category,
                current_unit_price = excluded.current_unit_price,
                updated_at = excluded.updated_at
            """,
            (
                order.product_id, order.product_name, order.category,
                float(order.unit_price), now,
            ),
        )
        customer_key = self.db.execute(
            "SELECT customer_key FROM dim_customers WHERE customer_id = ?",
            (order.customer_id,),
        ).fetchone()["customer_key"]
        product_key = self.db.execute(
            "SELECT product_key FROM dim_products WHERE product_id = ?",
            (order.product_id,),
        ).fetchone()["product_key"]
        self.db.execute(
            """
            INSERT INTO fact_orders(
                order_id, order_timestamp, order_date, customer_key, product_key,
                unit_price, quantity, gross_revenue, status, source_file, loaded_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(order_id) DO UPDATE SET
                order_timestamp = excluded.order_timestamp,
                order_date = excluded.order_date,
                customer_key = excluded.customer_key,
                product_key = excluded.product_key,
                unit_price = excluded.unit_price,
                quantity = excluded.quantity,
                gross_revenue = excluded.gross_revenue,
                status = excluded.status,
                source_file = excluded.source_file,
                loaded_at = excluded.loaded_at
            """,
            (
                order.order_id,
                order.order_timestamp.isoformat(),
                order.order_timestamp.date().isoformat(),
                customer_key,
                product_key,
                float(order.unit_price),
                order.quantity,
                float(order.gross_revenue),
                order.status,
                source_file,
                now,
            ),
        )

