-- ============================================================
-- Project: Business KPI Dashboard & Data Modeling
-- Author: Daisy Omondi
-- Purpose: Business SQL queries for Nova Retail Group dashboard
-- Tools: SQL, Python, Power BI
-- ============================================================

-- These queries support management reporting for:
-- Revenue, Profit, Profit Margin, Orders, Customers,
-- Product Performance, Regional Performance and Customer Segments.

-- ============================================================
-- 1. Executive KPI Summary
-- ============================================================

SELECT
    ROUND(SUM(revenue), 2) AS total_revenue,
    ROUND(SUM(profit), 2) AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(revenue), 0)) * 100, 2) AS profit_margin_percentage,
    COUNT(DISTINCT order_key) AS number_of_orders,
    ROUND(SUM(revenue) / NULLIF(COUNT(DISTINCT order_key), 0), 2) AS average_order_value,
    COUNT(DISTINCT customer_key) AS customer_count
FROM fact_sales;


-- ============================================================
-- 2. Monthly Revenue Trend
-- ============================================================

SELECT
    d.year_number,
    d.month_number,
    d.month_name,
    ROUND(SUM(f.revenue), 2) AS monthly_revenue,
    ROUND(SUM(f.profit), 2) AS monthly_profit
FROM fact_sales f
JOIN dim_date d
    ON f.date_key = d.date_key
GROUP BY
    d.year_number,
    d.month_number,
    d.month_name
ORDER BY
    d.year_number,
    d.month_number;


-- ============================================================
-- 3. Revenue and Profit by Region
-- ============================================================

SELECT
    r.region_name,
    r.country,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage
FROM fact_sales f
JOIN dim_region r
    ON f.region_key = r.region_key
GROUP BY
    r.region_name,
    r.country
ORDER BY
    total_revenue DESC;


-- ============================================================
-- 4. Revenue by Product Category
-- ============================================================

SELECT
    p.category,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage
FROM fact_sales f
JOIN dim_product p
    ON f.product_key = p.product_key
GROUP BY
    p.category
ORDER BY
    total_revenue DESC;


-- ============================================================
-- 5. Top 10 Products by Revenue
-- ============================================================

SELECT
    p.product_name,
    p.category,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    SUM(f.quantity) AS total_quantity_sold
FROM fact_sales f
JOIN dim_product p
    ON f.product_key = p.product_key
GROUP BY
    p.product_name,
    p.category
ORDER BY
    total_revenue DESC
LIMIT 10;


-- ============================================================
-- 6. Products with High Revenue but Low Profit Margin
-- ============================================================

SELECT
    p.product_name,
    p.category,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage
FROM fact_sales f
JOIN dim_product p
    ON f.product_key = p.product_key
GROUP BY
    p.product_name,
    p.category
HAVING
    SUM(f.revenue) > 10000
    AND (SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100 < 10
ORDER BY
    total_revenue DESC;


-- ============================================================
-- 7. Customer Segment Performance
-- ============================================================

SELECT
    c.customer_segment,
    COUNT(DISTINCT c.customer_key) AS number_of_customers,
    COUNT(DISTINCT f.order_key) AS number_of_orders,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND(SUM(f.revenue) / NULLIF(COUNT(DISTINCT f.order_key), 0), 2) AS average_order_value
FROM fact_sales f
JOIN dim_customer c
    ON f.customer_key = c.customer_key
GROUP BY
    c.customer_segment
ORDER BY
    total_revenue DESC;


-- ============================================================
-- 8. Regional Sales Performance by Product Category
-- ============================================================

SELECT
    r.region_name,
    p.category,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage
FROM fact_sales f
JOIN dim_region r
    ON f.region_key = r.region_key
JOIN dim_product p
    ON f.product_key = p.product_key
GROUP BY
    r.region_name,
    p.category
ORDER BY
    r.region_name,
    total_revenue DESC;


-- ============================================================
-- 9. Orders by Payment Method
-- ============================================================

SELECT
    o.payment_method,
    COUNT(DISTINCT f.order_key) AS number_of_orders,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit
FROM fact_sales f
JOIN dim_order o
    ON f.order_key = o.order_key
GROUP BY
    o.payment_method
ORDER BY
    total_revenue DESC;


-- ============================================================
-- 10. Yearly Business Performance
-- ============================================================

SELECT
    d.year_number,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage,
    COUNT(DISTINCT f.order_key) AS number_of_orders,
    COUNT(DISTINCT f.customer_key) AS customer_count
FROM fact_sales f
JOIN dim_date d
    ON f.date_key = d.date_key
GROUP BY
    d.year_number
ORDER BY
    d.year_number;


-- ============================================================
-- 11. Underperforming Regions
-- ============================================================

SELECT
    r.region_name,
    r.country,
    ROUND(SUM(f.revenue), 2) AS total_revenue,
    ROUND(SUM(f.profit), 2) AS total_profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage
FROM fact_sales f
JOIN dim_region r
    ON f.region_key = r.region_key
GROUP BY
    r.region_name,
    r.country
HAVING
    SUM(f.revenue) < 20000
    OR (SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100 < 10
ORDER BY
    total_profit ASC;


-- ============================================================
-- 12. Dashboard Data Export Query
-- ============================================================

SELECT
    d.year_number,
    d.month_name,
    r.region_name,
    p.category,
    c.customer_segment,
    ROUND(SUM(f.revenue), 2) AS revenue,
    ROUND(SUM(f.cost), 2) AS cost,
    ROUND(SUM(f.profit), 2) AS profit,
    ROUND((SUM(f.profit) / NULLIF(SUM(f.revenue), 0)) * 100, 2) AS profit_margin_percentage,
    COUNT(DISTINCT f.order_key) AS number_of_orders,
    COUNT(DISTINCT f.customer_key) AS customer_count
FROM fact_sales f
JOIN dim_date d
    ON f.date_key = d.date_key
JOIN dim_region r
    ON f.region_key = r.region_key
JOIN dim_product p
    ON f.product_key = p.product_key
JOIN dim_customer c
    ON f.customer_key = c.customer_key
GROUP BY
    d.year_number,
    d.month_number,
    d.month_name,
    r.region_name,
    p.category,
    c.customer_segment
ORDER BY
    d.year_number,
    d.month_number,
    r.region_name,
    p.category,
    c.customer_segment;


-- ============================================================
-- End of script
-- ============================================================
