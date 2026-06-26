-- ============================================================
-- Project: Business KPI Dashboard & Data Modeling
-- Author: Daisy Omondi
-- Purpose: Create a star schema for Nova Retail Group reporting
-- Tools: SQL, Python, Power BI
-- ============================================================

-- This database structure supports a clean reporting layer for:
-- Revenue, Profit, Profit Margin, Orders, Customers, Products,
-- Regions, Dates and Customer Segments.

-- Drop tables first if the script is re-run
DROP TABLE IF EXISTS fact_sales;
DROP TABLE IF EXISTS dim_order;
DROP TABLE IF EXISTS dim_date;
DROP TABLE IF EXISTS dim_region;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_customer;

-- ============================================================
-- Dimension Table: Customers
-- ============================================================

CREATE TABLE dim_customer (
    customer_key INT PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(150),
    customer_segment VARCHAR(100),
    email VARCHAR(150),
    city VARCHAR(100),
    country VARCHAR(100)
);

-- ============================================================
-- Dimension Table: Products
-- ============================================================

CREATE TABLE dim_product (
    product_key INT PRIMARY KEY,
    product_id VARCHAR(50) NOT NULL,
    product_name VARCHAR(150),
    category VARCHAR(100),
    sub_category VARCHAR(100),
    unit_cost DECIMAL(10, 2),
    unit_price DECIMAL(10, 2)
);

-- ============================================================
-- Dimension Table: Regions
-- ============================================================

CREATE TABLE dim_region (
    region_key INT PRIMARY KEY,
    region_id VARCHAR(50) NOT NULL,
    region_name VARCHAR(100),
    country VARCHAR(100),
    state VARCHAR(100),
    city VARCHAR(100)
);

-- ============================================================
-- Dimension Table: Dates
-- ============================================================

CREATE TABLE dim_date (
    date_key INT PRIMARY KEY,
    full_date DATE NOT NULL,
    day_number INT,
    day_name VARCHAR(20),
    week_number INT,
    month_number INT,
    month_name VARCHAR(20),
    quarter_number INT,
    year_number INT
);

-- ============================================================
-- Dimension Table: Orders
-- ============================================================

CREATE TABLE dim_order (
    order_key INT PRIMARY KEY,
    order_id VARCHAR(50) NOT NULL,
    order_date DATE,
    ship_date DATE,
    order_status VARCHAR(50),
    payment_method VARCHAR(50)
);

-- ============================================================
-- Fact Table: Sales
-- ============================================================

CREATE TABLE fact_sales (
    sales_key INT PRIMARY KEY,
    order_key INT,
    customer_key INT,
    product_key INT,
    region_key INT,
    date_key INT,

    quantity INT,
    unit_price DECIMAL(10, 2),
    discount DECIMAL(10, 2),
    revenue DECIMAL(12, 2),
    cost DECIMAL(12, 2),
    profit DECIMAL(12, 2),
    profit_margin DECIMAL(5, 2),

    CONSTRAINT fk_sales_order
        FOREIGN KEY (order_key) REFERENCES dim_order(order_key),

    CONSTRAINT fk_sales_customer
        FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),

    CONSTRAINT fk_sales_product
        FOREIGN KEY (product_key) REFERENCES dim_product(product_key),

    CONSTRAINT fk_sales_region
        FOREIGN KEY (region_key) REFERENCES dim_region(region_key),

    CONSTRAINT fk_sales_date
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
);

-- ============================================================
-- Indexes for faster reporting queries
-- ============================================================

CREATE INDEX idx_fact_sales_order_key
ON fact_sales(order_key);

CREATE INDEX idx_fact_sales_customer_key
ON fact_sales(customer_key);

CREATE INDEX idx_fact_sales_product_key
ON fact_sales(product_key);

CREATE INDEX idx_fact_sales_region_key
ON fact_sales(region_key);

CREATE INDEX idx_fact_sales_date_key
ON fact_sales(date_key);

-- ============================================================
-- End of script
-- ============================================================
