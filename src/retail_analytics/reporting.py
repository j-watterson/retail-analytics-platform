"""Console reporting from analytics views."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def build_summary(database_path: Path) -> str:
    with sqlite3.connect(database_path) as connection:
        connection.row_factory = sqlite3.Row
        metrics = connection.execute(
            """
            SELECT
                COUNT(*) AS orders,
                COALESCE(SUM(quantity), 0) AS units,
                COALESCE(ROUND(SUM(gross_revenue), 2), 0) AS revenue
            FROM fact_orders
            WHERE status = 'completed'
            """
        ).fetchone()
        categories = connection.execute(
            """
            SELECT category, completed_orders, units_sold, revenue
            FROM vw_category_performance
            ORDER BY revenue DESC
            """
        ).fetchall()

    lines = [
        "Northwind Outfitters — Sales Summary",
        "=" * 37,
        f"Completed orders: {metrics['orders']}",
        f"Units sold:       {metrics['units']}",
        f"Revenue:         ${metrics['revenue']:,.2f}",
        "",
        "Category performance",
        "-" * 37,
    ]
    lines.extend(
        f"{row['category']:<16} {row['units_sold']:>3} units  ${row['revenue']:>9,.2f}"
        for row in categories
    )
    return "\n".join(lines)

