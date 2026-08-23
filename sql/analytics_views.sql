CREATE VIEW IF NOT EXISTS vw_daily_sales AS
SELECT
    order_date,
    COUNT(*) AS completed_orders,
    SUM(quantity) AS units_sold,
    ROUND(SUM(gross_revenue), 2) AS revenue
FROM fact_orders
WHERE status = 'completed'
GROUP BY order_date;

CREATE VIEW IF NOT EXISTS vw_category_performance AS
SELECT
    p.category,
    COUNT(*) AS completed_orders,
    SUM(f.quantity) AS units_sold,
    ROUND(SUM(f.gross_revenue), 2) AS revenue
FROM fact_orders AS f
JOIN dim_products AS p ON p.product_key = f.product_key
WHERE f.status = 'completed'
GROUP BY p.category;

CREATE VIEW IF NOT EXISTS vw_customer_lifetime_value AS
SELECT
    c.customer_id,
    c.customer_name,
    COUNT(*) AS completed_orders,
    ROUND(SUM(f.gross_revenue), 2) AS lifetime_value
FROM fact_orders AS f
JOIN dim_customers AS c ON c.customer_key = f.customer_key
WHERE f.status = 'completed'
GROUP BY c.customer_id, c.customer_name;

