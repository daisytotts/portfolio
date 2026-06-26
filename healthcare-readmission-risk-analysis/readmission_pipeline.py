"""
Healthcare Readmission Risk Analysis Pipeline
Project: Healthcare Readmission Risk Analysis
Author: Daisy Omondi

Purpose:
This script builds a small end-to-end healthcare analytics workflow for 30-day
hospital readmission analysis.

It demonstrates:
1. Data ingestion from CSV
2. Data cleaning and validation
3. Creation of readmission-related features
4. SQL-ready cleaned dataset export
5. SQLite database loading
6. KPI summary and operational risk view

Data privacy note:
This project uses simulated healthcare-style admission data for portfolio demonstration.
No real patient data, confidential hospital data or personally identifiable patient
information is included.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd


# ============================================================
# Project paths
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
CLEANED_DATA_DIR = PROJECT_ROOT / "data" / "cleaned"
DATABASE_DIR = PROJECT_ROOT / "database"

RAW_FILE = RAW_DATA_DIR / "hospital_admissions.csv"
CLEANED_FILE = CLEANED_DATA_DIR / "patient_admissions_clean.csv"
DATABASE_PATH = DATABASE_DIR / "healthcare_readmission.db"


# ============================================================
# Logging
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger(__name__)


# ============================================================
# Setup
# ============================================================

def create_project_folders() -> None:
    """Create project folders if they do not already exist."""
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    CLEANED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# Extract: simulated demo data
# ============================================================

def create_simulated_admission_data(output_path: Path, seed: int = 42) -> pd.DataFrame:
    """
    Create simulated hospital admission data.

    The readmission probability intentionally increases as previous admissions increase.
    This supports the main project insight:
    patients with more previous admissions show higher 30-day readmission risk.
    """
    logger.info("Creating simulated healthcare-style admission data...")

    rng = np.random.default_rng(seed)

    previous_admission_groups = [0, 1, 2, 3, 4, 5]
    group_sizes = [1200, 1000, 850, 700, 500, 350]

    readmission_probabilities = {
        0: 0.078,
        1: 0.146,
        2: 0.283,
        3: 0.437,
        4: 0.612,
        5: 0.725,
    }

    departments = [
        "Internal Medicine",
        "Cardiology",
        "Neurology",
        "Surgery",
        "Emergency Observation",
        "Geriatrics",
    ]

    age_groups = ["18-39", "40-59", "60-74", "75+"]

    rows: list[dict[str, object]] = []
    admission_counter = 1
    patient_counter = 10000
    start_date = pd.Timestamp("2024-01-01")

    for previous_admissions, group_size in zip(previous_admission_groups, group_sizes):
        for _ in range(group_size):
            patient_counter += 1

            patient_id = f"P{patient_counter}"
            admission_id = f"A{admission_counter:06d}"

            admission_date = start_date + pd.to_timedelta(
                int(rng.integers(0, 365)),
                unit="D",
            )

            length_of_stay = int(rng.integers(1, 15))
            discharge_date = admission_date + pd.to_timedelta(length_of_stay, unit="D")

            readmitted_within_30_days = int(
                rng.random() < readmission_probabilities[previous_admissions]
            )

            if readmitted_within_30_days == 1:
                days_to_readmission = int(rng.integers(2, 31))
            else:
                days_to_readmission = np.nan

            rows.append(
                {
                    "patient_id": patient_id,
                    "admission_id": admission_id,
                    "admission_date": admission_date,
                    "discharge_date": discharge_date,
                    "age_group": rng.choice(age_groups, p=[0.18, 0.28, 0.30, 0.24]),
                    "department": rng.choice(departments),
                    "previous_admissions": previous_admissions,
                    "length_of_stay": length_of_stay,
                    "days_to_readmission": days_to_readmission,
                    "readmitted_within_30_days": readmitted_within_30_days,
                }
            )

            admission_counter += 1

    admissions = pd.DataFrame(rows)

    # Add a few realistic data quality issues for the cleaning step.
    duplicate_rows = admissions.sample(20, random_state=seed)
    admissions = pd.concat([admissions, duplicate_rows], ignore_index=True)

    missing_department_index = admissions.sample(30, random_state=seed + 1).index
    admissions.loc[missing_department_index, "department"] = None

    admissions.to_csv(output_path, index=False)

    logger.info("Simulated raw data saved to %s.", output_path)
    return admissions


def extract_data() -> pd.DataFrame:
    """Load raw admission data or create simulated data if no raw file exists."""
    if not RAW_FILE.exists():
        create_simulated_admission_data(RAW_FILE)

    logger.info("Loading raw admission data from %s.", RAW_FILE)
    return pd.read_csv(RAW_FILE)


# ============================================================
# Transform: cleaning and feature preparation
# ============================================================

def clean_admission_data(raw_admissions: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and prepare hospital admission records.

    Cleaning steps:
    - Remove duplicate admission records
    - Standardize date columns
    - Fill missing department values
    - Convert numeric fields
    - Check length of stay
    - Create operational risk pattern fields
    """
    logger.info("Cleaning admission data...")

    admissions = raw_admissions.copy()

    admissions = admissions.drop_duplicates(subset=["admission_id"])

    admissions["admission_date"] = pd.to_datetime(
        admissions["admission_date"],
        errors="coerce",
    )

    admissions["discharge_date"] = pd.to_datetime(
        admissions["discharge_date"],
        errors="coerce",
    )

    admissions["department"] = admissions["department"].fillna("Unknown")

    numeric_columns = [
        "previous_admissions",
        "length_of_stay",
        "days_to_readmission",
        "readmitted_within_30_days",
    ]

    for column in numeric_columns:
        admissions[column] = pd.to_numeric(admissions[column], errors="coerce")

    admissions = admissions.dropna(
        subset=[
            "patient_id",
            "admission_id",
            "admission_date",
            "discharge_date",
        ]
    )

    admissions["calculated_length_of_stay"] = (
        admissions["discharge_date"] - admissions["admission_date"]
    ).dt.days

    admissions["length_of_stay"] = admissions["length_of_stay"].fillna(
        admissions["calculated_length_of_stay"]
    )

    admissions["length_of_stay"] = admissions["length_of_stay"].astype(int)
    admissions["previous_admissions"] = admissions["previous_admissions"].fillna(0).astype(int)
    admissions["readmitted_within_30_days"] = (
        admissions["readmitted_within_30_days"].fillna(0).astype(int)
    )

    admissions = admissions[admissions["length_of_stay"] > 0]

    admissions["risk_pattern"] = np.select(
        [
            admissions["previous_admissions"] >= 4,
            admissions["previous_admissions"].between(2, 3),
        ],
        [
            "High readmission pattern",
            "Moderate readmission pattern",
        ],
        default="Lower readmission pattern",
    )

    admissions["suggested_operational_action"] = np.select(
        [
            admissions["previous_admissions"] >= 4,
            admissions["previous_admissions"].between(2, 3),
        ],
        [
            "Review discharge planning and follow-up coordination",
            "Consider stronger follow-up after discharge",
        ],
        default="Standard discharge process",
    )

    admissions = admissions.sort_values(
        ["patient_id", "admission_date"],
        ascending=[True, True],
    ).reset_index(drop=True)

    logger.info("Cleaned admission data contains %s rows.", len(admissions))

    return admissions


# ============================================================
# Quality checks
# ============================================================

def run_quality_checks(admissions: pd.DataFrame) -> None:
    """Run basic data quality checks before exporting and loading."""
    logger.info("Running data quality checks...")

    if admissions.empty:
        raise ValueError("Cleaned admissions data is empty.")

    if admissions["admission_id"].duplicated().any():
        raise ValueError("Duplicate admission_id values remain after cleaning.")

    if admissions["admission_date"].isna().any():
        raise ValueError("Admission date contains missing values.")

    if admissions["discharge_date"].isna().any():
        raise ValueError("Discharge date contains missing values.")

    if (admissions["length_of_stay"] <= 0).any():
        raise ValueError("Length of stay contains zero or negative values.")

    invalid_flags = set(admissions["readmitted_within_30_days"].unique()) - {0, 1}
    if invalid_flags:
        raise ValueError("Readmission flag must only contain 0 or 1.")

    logger.info("Data quality checks passed.")


# ============================================================
# Analysis summaries
# ============================================================

def create_kpi_summary(admissions: pd.DataFrame) -> pd.DataFrame:
    """Create an executive KPI summary."""
    total_admissions = len(admissions)
    unique_patients = admissions["patient_id"].nunique()
    readmissions_30d = admissions["readmitted_within_30_days"].sum()
    readmission_rate = readmissions_30d / total_admissions * 100
    average_length_of_stay = admissions["length_of_stay"].mean()
    average_previous_admissions = admissions["previous_admissions"].mean()

    return pd.DataFrame(
        {
            "kpi": [
                "Total Admissions",
                "Unique Patients",
                "30-Day Readmissions",
                "Readmission Rate (%)",
                "Average Length of Stay",
                "Average Previous Admissions",
            ],
            "value": [
                total_admissions,
                unique_patients,
                readmissions_30d,
                round(readmission_rate, 2),
                round(average_length_of_stay, 2),
                round(average_previous_admissions, 2),
            ],
        }
    )


def create_readmission_summary(admissions: pd.DataFrame) -> pd.DataFrame:
    """Summarize readmission rate by number of previous admissions."""
    summary = (
        admissions.groupby("previous_admissions")
        .agg(
            total_admissions=("admission_id", "count"),
            unique_patients=("patient_id", "nunique"),
            readmissions_30d=("readmitted_within_30_days", "sum"),
            average_length_of_stay=("length_of_stay", "mean"),
        )
        .reset_index()
    )

    summary["readmission_rate_percentage"] = (
        summary["readmissions_30d"] / summary["total_admissions"] * 100
    ).round(2)

    return summary


def create_department_summary(admissions: pd.DataFrame) -> pd.DataFrame:
    """Summarize readmission rate by department."""
    summary = (
        admissions.groupby("department")
        .agg(
            total_admissions=("admission_id", "count"),
            readmissions_30d=("readmitted_within_30_days", "sum"),
            average_length_of_stay=("length_of_stay", "mean"),
        )
        .reset_index()
    )

    summary["readmission_rate_percentage"] = (
        summary["readmissions_30d"] / summary["total_admissions"] * 100
    ).round(2)

    return summary.sort_values("readmission_rate_percentage", ascending=False)


# ============================================================
# Load: export CSV and SQLite
# ============================================================

def prepare_for_sql(admissions: pd.DataFrame) -> pd.DataFrame:
    """Convert datetime columns into SQL-friendly text dates."""
    sql_ready = admissions.copy()

    for column in sql_ready.columns:
        if pd.api.types.is_datetime64_any_dtype(sql_ready[column]):
            sql_ready[column] = sql_ready[column].dt.strftime("%Y-%m-%d")

    return sql_ready


def export_cleaned_outputs(admissions: pd.DataFrame) -> None:
    """Export cleaned data and analysis summaries as CSV files."""
    logger.info("Exporting cleaned data and summary tables...")

    sql_ready_admissions = prepare_for_sql(admissions)
    sql_ready_admissions.to_csv(CLEANED_FILE, index=False)

    kpi_summary = create_kpi_summary(admissions)
    readmission_summary = create_readmission_summary(admissions)
    department_summary = create_department_summary(admissions)

    kpi_summary.to_csv(CLEANED_DATA_DIR / "kpi_summary.csv", index=False)
    readmission_summary.to_csv(CLEANED_DATA_DIR / "readmission_summary.csv", index=False)
    department_summary.to_csv(CLEANED_DATA_DIR / "department_summary.csv", index=False)

    logger.info("Cleaned files exported to %s.", CLEANED_DATA_DIR)


def load_to_sqlite(admissions: pd.DataFrame) -> None:
    """Load cleaned admission data into a SQLite database."""
    logger.info("Loading cleaned data into SQLite database...")

    sql_ready_admissions = prepare_for_sql(admissions)

    with sqlite3.connect(DATABASE_PATH) as connection:
        sql_ready_admissions.to_sql(
            "patient_admissions_clean",
            connection,
            if_exists="replace",
            index=False,
        )

        connection.executescript(
            """
            DROP VIEW IF EXISTS vw_readmission_dashboard;

            CREATE VIEW vw_readmission_dashboard AS
            SELECT
                patient_id,
                admission_id,
                admission_date,
                discharge_date,
                strftime('%Y', admission_date) AS admission_year,
                strftime('%m', admission_date) AS admission_month,
                department,
                age_group,
                previous_admissions,
                length_of_stay,
                days_to_readmission,
                readmitted_within_30_days,
                risk_pattern,
                suggested_operational_action
            FROM patient_admissions_clean;
            """
        )

    logger.info("SQLite database saved to %s.", DATABASE_PATH)


# ============================================================
# Display summary
# ============================================================

def print_pipeline_summary(admissions: pd.DataFrame) -> None:
    """Print a clear summary of the pipeline output."""
    kpi_summary = create_kpi_summary(admissions)
    readmission_summary = create_readmission_summary(admissions)

    print("\nHealthcare Readmission Pipeline Summary")
    print("=======================================")

    for _, row in kpi_summary.iterrows():
        print(f"{row['kpi']:<32} {row['value']}")

    print("\nReadmission Rate by Previous Admissions")
    print("---------------------------------------")
    print(readmission_summary.to_string(index=False))

    print("\nOutputs created")
    print("---------------")
    print(f"Cleaned admissions CSV: {CLEANED_FILE}")
    print(f"SQLite database:        {DATABASE_PATH}")
    print(f"Summary folder:         {CLEANED_DATA_DIR}")


# ============================================================
# Main pipeline
# ============================================================

def run_pipeline() -> None:
    """Run the full healthcare readmission analytics pipeline."""
    create_project_folders()

    raw_admissions = extract_data()
    cleaned_admissions = clean_admission_data(raw_admissions)

    run_quality_checks(cleaned_admissions)
    export_cleaned_outputs(cleaned_admissions)
    load_to_sqlite(cleaned_admissions)

    print_pipeline_summary(cleaned_admissions)


if __name__ == "__main__":
    run_pipeline()
