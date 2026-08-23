PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_customers (
    customer_key INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL UNIQUE,
    customer_name TEXT NOT NULL,
    customer_email TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_key INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id TEXT NOT NULL UNIQUE,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    current_unit_price NUMERIC NOT NULL CHECK (current_unit_price >= 0),
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id INTEGER PRIMARY KEY,
    order_timestamp TEXT NOT NULL,
    order_date TEXT NOT NULL,
    customer_key INTEGER NOT NULL,
    product_key INTEGER NOT NULL,
    unit_price NUMERIC NOT NULL CHECK (unit_price >= 0),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    gross_revenue NUMERIC NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled', 'refunded')),
    source_file TEXT NOT NULL,
    loaded_at TEXT NOT NULL,
    FOREIGN KEY (customer_key) REFERENCES dim_customers(customer_key),
    FOREIGN KEY (product_key) REFERENCES dim_products(product_key)
);

CREATE INDEX IF NOT EXISTS idx_fact_orders_date ON fact_orders(order_date);
CREATE INDEX IF NOT EXISTS idx_fact_orders_customer ON fact_orders(customer_key);
CREATE INDEX IF NOT EXISTS idx_fact_orders_product ON fact_orders(product_key);

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id TEXT PRIMARY KEY,
    source_file TEXT NOT NULL,
    source_checksum TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    status TEXT NOT NULL,
    rows_read INTEGER NOT NULL DEFAULT 0,
    rows_loaded INTEGER NOT NULL DEFAULT 0,
    rows_rejected INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);

