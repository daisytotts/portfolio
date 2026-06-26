"""
ETL Pipeline - Nova Retail Group
Project: Business KPI Dashboard & Data Modeling
Author: Daisy Omondi

Purpose:
This script turns raw retail CSV files into a clean SQL reporting database.
It supports the Power BI dashboard with clean dimension tables and one sales fact table.

Workflow:

1. Extract raw CSV data
2. Clean and standardize the data with Python + Pandas
3. Build dimension tables and a fact table
4. Load the final tables into a SQLite database
5. Export cleaned CSV files for reporting checks

Note:
If raw CSV files are missing, the script creates small synthetic demo data.
This keeps the project runnable for portfolio reviewers.
"""

from **future** import annotations

import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

# ============================================================

# Project paths

# ============================================================

PROJECT_ROOT = Path(**file**).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
DATABASE_DIR = PROJECT_ROOT / "database"
DATABASE_PATH = DATABASE_DIR / "nova_retail.db"

EXPECTED_RAW_FILES = {
"customers": "customers.csv",
"products": "products.csv",
"regions": "regions.csv",
"orders": "orders.csv",
"sales": "sales_transactions.csv",
}

# ============================================================

# Logging

# ============================================================

logging.basicConfig(
level=logging.INFO,
format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(**name**)

# ============================================================

# Setup

# ============================================================

def create_project_folders() -> None:
"""Create the folders needed by the ETL pipeline."""
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

def raw_files_exist() -> bool:
"""Check if all expected raw CSV files already exist."""
return all((RAW_DATA_DIR / filename).exists() for filename in EXPECTED_RAW_FILES.values())

# ============================================================

# Demo data creation

# ============================================================

def create_sample_raw_data(seed: int = 42) -> None:
"""
Create synthetic retail data for portfolio demonstration.

```
This is useful when the repository is reviewed without external data files.
The data is fictional and should not be treated as real company data.
"""
logger.info("Raw CSV files not found. Creating synthetic demo data...")

rng = np.random.default_rng(seed)

customer_segments = ["Consumer", "Corporate", "Home Office", "Small Business"]
countries = ["Germany", "France", "Netherlands", "Italy", "Spain", "Poland"]
cities = ["Berlin", "Munich", "Paris", "Amsterdam", "Milan", "Madrid", "Warsaw", "Hamburg"]

customers = pd.DataFrame({
    "customer_id": [f"CUST-{i:05d}" for i in range(1, 501)],
    "customer_name": [f"Customer {i}" for i in range(1, 501)],
    "customer_segment": rng.choice(customer_segments, size=500, p=[0.38, 0.27, 0.20, 0.15]),
    "email": [f"customer{i}@example.com" for i in range(1, 501)],
    "city": rng.choice(cities, size=500),
    "country": rng.choice(countries, size=500),
})

categories = {
    "Electronics": ["Laptops", "Phones", "Accessories"],
    "Apparel": ["Shoes", "Jackets", "Shirts"],
    "Home & Living": ["Furniture", "Kitchen", "Decor"],
    "Beauty": ["Skincare", "Haircare", "Fragrance"],
    "Sports & Outdoors": ["Fitness", "Outdoor", "Cycling"],
    "Toys & Games": ["Board Games", "Educational", "Outdoor Toys"],
}

product_rows = []
product_id = 1

for category, sub_categories in categories.items():
    for sub_category in sub_categories:
        for number in range(1, 6):
            unit_cost = round(float(rng.uniform(8, 250)), 2)
            markup = float(rng.uniform(1.25, 2.10))
            unit_price = round(unit_cost * markup, 2)

            product_rows.append({
                "product_id": f"PROD-{product_id:04d}",
                "product_name": f"{sub_category} Item {number}",
                "category": category,
                "sub_category": sub_category,
                "unit_cost": unit_cost,
                "unit_price": unit_price,
            })

            product_id += 1

products = pd.DataFrame(product_rows)

regions = pd.DataFrame({
    "region_id": [f"REG-{i:02d}" for i in range(1, 13)],
    "region_name": [
        "North America", "North America", "Europe", "Europe",
        "Asia Pacific", "Asia Pacific", "Latin America", "Latin America",
        "Middle East & Africa", "Middle East & Africa", "Europe", "Asia Pacific"
    ],
    "country": [
        "United States", "Canada", "Germany", "France",
        "Japan", "Australia", "Brazil", "Mexico",
        "United Arab Emirates", "South Africa", "Netherlands", "Singapore"
    ],
    "state": [
        "California", "Ontario", "Bavaria", "Ile-de-France",
        "Tokyo", "New South Wales", "São Paulo", "Mexico City",
        "Dubai", "Gauteng", "North Holland", "Central"
    ],
    "city": [
        "Los Angeles", "Toronto", "Munich", "Paris",
        "Tokyo", "Sydney", "São Paulo", "Mexico City",
        "Dubai", "Johannesburg", "Amsterdam", "Singapore"
    ],
})

start_date = pd.Timestamp("2024-01-01")
order_dates = start_date + pd.to_timedelta(rng.integers(0, 365, size=2000), unit="D")
ship_dates = order_dates + pd.to_timedelta(rng.integers(1, 8, size=2000), unit="D")

orders = pd.DataFrame({
    "order_id": [f"ORD-{i:06d}" for i in range(1, 2001)],
    "order_date": order_dates,
    "ship_date": ship_dates,
    "order_status": rng.choice(["Completed", "Returned", "Cancelled"], size=2000, p=[0.90, 0.07, 0.03]),
    "payment_method": rng.choice(["Credit Card", "PayPal", "Bank Transfer", "Invoice"], size=2000),
})

sales_rows = []
sales_key = 1

for order_id in orders["order_id"]:
    number_of_lines = int(rng.integers(1, 4))

    for _ in range(number_of_lines):
        sales_rows.append({
            "sales_id": f"SALE-{sales_key:07d}",
            "order_id": order_id,
            "customer_id": rng.choice(customers["customer_id"]),
            "product_id": rng.choice(products["product_id"]),
            "region_id": rng.choice(regions["region_id"]),
            "quantity": int(rng.integers(1, 8)),
            "discount": round(float(rng.choice([0, 0.03, 0.05, 0.10, 0.15], p=[0.45, 0.15, 0.20, 0.15, 0.05])), 2),
        })

        sales_key += 1

sales = pd.DataFrame(sales_rows)

customers.to_csv(RAW_DATA_DIR / EXPECTED_RAW_FILES["customers"], index=False)
products.to_csv(RAW_DATA_DIR / EXPECTED_RAW_FILES["products"], index=False)
regions.to_csv(RAW_DATA_DIR / EXPECTED_RAW_FILES["regions"], index=False)
orders.to_csv(RAW_DATA_DIR / EXPECTED_RAW_FILES["orders"], index=False)
sales.to_csv(RAW_DATA_DIR / EXPECTED_RAW_FILES["sales"], index=False)

logger.info("Synthetic demo data created in data/raw.")
```

# ============================================================

# Extract

# ============================================================

def extract_raw_data() -> dict[str, pd.DataFrame]:
"""Load raw CSV files into pandas DataFrames."""
if not raw_files_exist():
create_sample_raw_data()

```
logger.info("Extracting raw CSV files...")

data = {
    name: pd.read_csv(RAW_DATA_DIR / filename)
    for name, filename in EXPECTED_RAW_FILES.items()
}

logger.info("Raw data extracted successfully.")
return data
```

# ============================================================

# Transform

# ============================================================

def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
"""Strip spaces and clean text columns."""
df = df.copy()

```
for column in df.select_dtypes(include="object").columns:
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
        .replace({"nan": np.nan, "None": np.nan, "": np.nan})
    )

return df
```

def clean_customers(customers: pd.DataFrame) -> pd.DataFrame:
"""Clean customer data."""
customers = clean_text_columns(customers)
customers = customers.drop_duplicates(subset=["customer_id"])
customers["customer_segment"] = customers["customer_segment"].fillna("Unknown")
customers["country"] = customers["country"].fillna("Unknown")

```
return customers
```

def clean_products(products: pd.DataFrame) -> pd.DataFrame:
"""Clean product data."""
products = clean_text_columns(products)
products = products.drop_duplicates(subset=["product_id"])

```
products["unit_cost"] = pd.to_numeric(products["unit_cost"], errors="coerce").fillna(0)
products["unit_price"] = pd.to_numeric(products["unit_price"], errors="coerce").fillna(0)

products["category"] = products["category"].fillna("Unknown")
products["sub_category"] = products["sub_category"].fillna("Unknown")

return products
```

def clean_regions(regions: pd.DataFrame) -> pd.DataFrame:
"""Clean region data."""
regions = clean_text_columns(regions)
regions = regions.drop_duplicates(subset=["region_id"])
regions["region_name"] = regions["region_name"].fillna("Unknown")

```
return regions
```

def clean_orders(orders: pd.DataFrame) -> pd.DataFrame:
"""Clean order data."""
orders = clean_text_columns(orders)
orders = orders.drop_duplicates(subset=["order_id"])

```
orders["order_date"] = pd.to_datetime(orders["order_date"], errors="coerce")
orders["ship_date"] = pd.to_datetime(orders["ship_date"], errors="coerce")

orders["order_status"] = orders["order_status"].fillna("Unknown")
orders["payment_method"] = orders["payment_method"].fillna("Unknown")

return orders.dropna(subset=["order_date"])
```

def clean_sales(sales: pd.DataFrame) -> pd.DataFrame:
"""Clean sales transaction data."""
sales = clean_text_columns(sales)
sales = sales.drop_duplicates(subset=["sales_id"])

```
sales["quantity"] = pd.to_numeric(sales["quantity"], errors="coerce").fillna(0).astype(int)
sales["discount"] = pd.to_numeric(sales["discount"], errors="coerce").fillna(0)

sales = sales[sales["quantity"] > 0]

return sales
```

def add_surrogate_key(df: pd.DataFrame, key_name: str) -> pd.DataFrame:
"""Add a simple integer surrogate key."""
df = df.copy().reset_index(drop=True)
df.insert(0, key_name, df.index + 1)
return df

def build_date_dimension(orders: pd.DataFrame) -> pd.DataFrame:
"""Create a date dimension from order dates."""
min_date = orders["order_date"].min()
max_date = orders["order_date"].max()

```
date_range = pd.date_range(start=min_date, end=max_date, freq="D")

dim_date = pd.DataFrame({"full_date": date_range})
dim_date["date_key"] = dim_date["full_date"].dt.strftime("%Y%m%d").astype(int)
dim_date["day_number"] = dim_date["full_date"].dt.day
dim_date["day_name"] = dim_date["full_date"].dt.day_name()
dim_date["week_number"] = dim_date["full_date"].dt.isocalendar().week.astype(int)
dim_date["month_number"] = dim_date["full_date"].dt.month
dim_date["month_name"] = dim_date["full_date"].dt.month_name()
dim_date["quarter_number"] = dim_date["full_date"].dt.quarter
dim_date["year_number"] = dim_date["full_date"].dt.year

return dim_date
```

def transform_data(raw_data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
"""Clean raw data and create reporting tables."""
logger.info("Transforming raw data...")

```
customers = clean_customers(raw_data["customers"])
products = clean_products(raw_data["products"])
regions = clean_regions(raw_data["regions"])
orders = clean_orders(raw_data["orders"])
sales = clean_sales(raw_data["sales"])

dim_customer = add_surrogate_key(customers, "customer_key")
dim_product = add_surrogate_key(products, "product_key")
dim_region = add_surrogate_key(regions, "region_key")
dim_order = add_surrogate_key(orders, "order_key")
dim_date = build_date_dimension(dim_order)

fact_sales = (
    sales
    .merge(dim_order[["order_key", "order_id", "order_date"]], on="order_id", how="inner")
    .merge(dim_customer[["customer_key", "customer_id"]], on="customer_id", how="inner")
    .merge(dim_product[["product_key", "product_id", "unit_cost", "unit_price"]], on="product_id", how="inner")
    .merge(dim_region[["region_key", "region_id"]], on="region_id", how="inner")
)

fact_sales["date_key"] = fact_sales["order_date"].dt.strftime("%Y%m%d").astype(int)
fact_sales["revenue"] = fact_sales["quantity"] * fact_sales["unit_price"] * (1 - fact_sales["discount"])
fact_sales["cost"] = fact_sales["quantity"] * fact_sales["unit_cost"]
fact_sales["profit"] = fact_sales["revenue"] - fact_sales["cost"]
fact_sales["profit_margin"] = np.where(
    fact_sales["revenue"] > 0,
    (fact_sales["profit"] / fact_sales["revenue"]) * 100,
    0,
)

fact_sales = fact_sales.reset_index(drop=True)
fact_sales.insert(0, "sales_key", fact_sales.index + 1)

fact_sales = fact_sales[
    [
        "sales_key",
        "order_key",
        "customer_key",
        "product_key",
        "region_key",
        "date_key",
        "quantity",
        "unit_price",
        "discount",
        "revenue",
        "cost",
        "profit",
        "profit_margin",
    ]
]

final_tables = {
    "dim_customer": dim_customer,
    "dim_product": dim_product,
    "dim_region": dim_region,
    "dim_date": dim_date,
    "dim_order": dim_order,
    "fact_sales": fact_sales,
}

logger.info("Data transformed successfully.")
return final_tables
```

# ============================================================

# Load

# ============================================================

def create_database_schema(connection: sqlite3.Connection) -> None:
"""Create the SQL database schema."""
logger.info("Creating SQL database schema...")

```
connection.executescript(
    """
    PRAGMA foreign_keys = ON;

    DROP TABLE IF EXISTS fact_sales;
    DROP TABLE IF EXISTS dim_order;
    DROP TABLE IF EXISTS dim_date;
    DROP TABLE IF EXISTS dim_region;
    DROP TABLE IF EXISTS dim_product;
    DROP TABLE IF EXISTS dim_customer;

    CREATE TABLE dim_customer (
        customer_key INTEGER PRIMARY KEY,
        customer_id TEXT NOT NULL,
        customer_name TEXT,
        customer_segment TEXT,
        email TEXT,
        city TEXT,
        country TEXT
    );

    CREATE TABLE dim_product (
        product_key INTEGER PRIMARY KEY,
        product_id TEXT NOT NULL,
        product_name TEXT,
        category TEXT,
        sub_category TEXT,
        unit_cost REAL,
        unit_price REAL
    );

    CREATE TABLE dim_region (
        region_key INTEGER PRIMARY KEY,
        region_id TEXT NOT NULL,
        region_name TEXT,
        country TEXT,
        state TEXT,
        city TEXT
    );

    CREATE TABLE dim_date (
        date_key INTEGER PRIMARY KEY,
        full_date TEXT NOT NULL,
        day_number INTEGER,
        day_name TEXT,
        week_number INTEGER,
        month_number INTEGER,
        month_name TEXT,
        quarter_number INTEGER,
        year_number INTEGER
    );

    CREATE TABLE dim_order (
        order_key INTEGER PRIMARY KEY,
        order_id TEXT NOT NULL,
        order_date TEXT,
        ship_date TEXT,
        order_status TEXT,
        payment_method TEXT
    );

    CREATE TABLE fact_sales (
        sales_key INTEGER PRIMARY KEY,
        order_key INTEGER,
        customer_key INTEGER,
        product_key INTEGER,
        region_key INTEGER,
        date_key INTEGER,
        quantity INTEGER,
        unit_price REAL,
        discount REAL,
        revenue REAL,
        cost REAL,
        profit REAL,
        profit_margin REAL,

        FOREIGN KEY (order_key) REFERENCES dim_order(order_key),
        FOREIGN KEY (customer_key) REFERENCES dim_customer(customer_key),
        FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
        FOREIGN KEY (region_key) REFERENCES dim_region(region_key),
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key)
    );

    CREATE INDEX idx_fact_sales_order_key ON fact_sales(order_key);
    CREATE INDEX idx_fact_sales_customer_key ON fact_sales(customer_key);
    CREATE INDEX idx_fact_sales_product_key ON fact_sales(product_key);
    CREATE INDEX idx_fact_sales_region_key ON fact_sales(region_key);
    CREATE INDEX idx_fact_sales_date_key ON fact_sales(date_key);
    """
)

connection.commit()
```

def prepare_for_sql(df: pd.DataFrame) -> pd.DataFrame:
"""Convert datetime columns so they save cleanly into SQLite."""
df = df.copy()

```
for column in df.columns:
    if pd.api.types.is_datetime64_any_dtype(df[column]):
        df[column] = df[column].dt.strftime("%Y-%m-%d")

return df
```

def load_to_sqlite(tables: dict[str, pd.DataFrame]) -> None:
"""Load transformed tables into a SQLite database."""
logger.info("Loading transformed data into SQLite database...")

```
with sqlite3.connect(DATABASE_PATH) as connection:
    create_database_schema(connection)

    load_order = [
        "dim_customer",
        "dim_product",
        "dim_region",
        "dim_date",
        "dim_order",
        "fact_sales",
    ]

    for table_name in load_order:
        table = prepare_for_sql(tables[table_name])
        table.to_sql(table_name, connection, if_exists="append", index=False)
        logger.info("Loaded %s rows into %s.", len(table), table_name)

logger.info("SQL database created at %s.", DATABASE_PATH)
```

def export_cleaned_csv(tables: dict[str, pd.DataFrame]) -> None:
"""Export cleaned reporting tables as CSV files."""
logger.info("Exporting cleaned CSV files...")

```
for table_name, table in tables.items():
    output_path = CLEANED_DATA_DIR / f"{table_name}.csv"
    prepare_for_sql(table).to_csv(output_path, index=False)

logger.info("Cleaned CSV files exported to data/cleaned.")
```

# ============================================================

# Quality checks

# ============================================================

def run_quality_checks(tables: dict[str, pd.DataFrame]) -> None:
"""Run basic checks before loading the data."""
logger.info("Running data quality checks...")

```
fact_sales = tables["fact_sales"]

if fact_sales.empty:
    raise ValueError("fact_sales is empty. Check the raw input data.")

if fact_sales["revenue"].isna().any():
    raise ValueError("Revenue contains missing values.")

if fact_sales["profit"].isna().any():
    raise ValueError("Profit contains missing values.")

if (fact_sales["quantity"] <= 0).any():
    raise ValueError("Quantity contains zero or negative values.")

logger.info("Data quality checks passed.")
```

def print_summary(tables: dict[str, pd.DataFrame]) -> None:
"""Print a small project summary."""
fact_sales = tables["fact_sales"]

```
total_revenue = fact_sales["revenue"].sum()
total_profit = fact_sales["profit"].sum()
number_of_orders = fact_sales["order_key"].nunique()
customer_count = fact_sales["customer_key"].nunique()

print("\nETL Pipeline Summary")
print("====================")
print(f"Total revenue:      ${total_revenue:,.2f}")
print(f"Total profit:       ${total_profit:,.2f}")
print(f"Number of orders:   {number_of_orders:,}")
print(f"Customer count:     {customer_count:,}")
print(f"Database created:   {DATABASE_PATH}")
print(f"Cleaned CSV folder: {CLEANED_DATA_DIR}")
```

# ============================================================

# Main pipeline

# ============================================================

def run_pipeline() -> None:
"""Run the full ETL pipeline."""
create_project_folders()

```
raw_data = extract_raw_data()
transformed_tables = transform_data(raw_data)

run_quality_checks(transformed_tables)
export_cleaned_csv(transformed_tables)
load_to_sqlite(transformed_tables)

print_summary(transformed_tables)
```

if **name** == "**main**":
run_pipeline()
