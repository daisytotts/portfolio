-- ============================================================
-- Project: Healthcare Readmission Risk Analysis
-- Author: Daisy Omondi
-- Purpose: SQL queries for 30-day hospital readmission analysis
-- Tools: SQL, Python, Healthcare Analytics
-- ============================================================

-- Data privacy note:
-- This project uses simulated/public healthcare-style admission data.
-- No real patient data, confidential hospital data, or personally identifiable
-- patient information is included.

-- Main table used in this project:
-- patient_admissions_clean

-- Expected columns:
-- patient_id
-- admission_id
-- admission_date
-- discharge_date
-- age_group
-- department
-- previous_admissions
-- length_of_stay
-- days_to_readmission
-- readmitted_within_30_days

-- ============================================================
-- 1. Executive Readmission KPI Summary
-- ============================================================

SELECT
COUNT(*) AS total_admissions,
COUNT(DISTINCT patient_id) AS unique_patients,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage,
ROUND(AVG(length_of_stay), 2) AS average_length_of_stay,
ROUND(AVG(previous_admissions), 2) AS average_previous_admissions
FROM patient_admissions_clean;

-- ============================================================
-- 2. Readmission Rate by Previous Admissions
-- ============================================================

SELECT
previous_admissions,
COUNT(*) AS total_admissions,
COUNT(DISTINCT patient_id) AS unique_patients,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage,
ROUND(AVG(length_of_stay), 2) AS average_length_of_stay
FROM patient_admissions_clean
GROUP BY previous_admissions
ORDER BY previous_admissions;

-- ============================================================
-- 3. Patients with Highest Readmission Risk
-- ============================================================

SELECT
patient_id,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage,
MAX(previous_admissions) AS highest_previous_admissions,
ROUND(AVG(length_of_stay), 2) AS average_length_of_stay
FROM patient_admissions_clean
GROUP BY patient_id
HAVING COUNT(*) >= 1
ORDER BY
readmission_rate_percentage DESC,
total_admissions DESC,
highest_previous_admissions DESC
LIMIT 10;

-- ============================================================
-- 4. Readmission Rate by Department
-- ============================================================

SELECT
department,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage,
ROUND(AVG(length_of_stay), 2) AS average_length_of_stay
FROM patient_admissions_clean
GROUP BY department
ORDER BY readmission_rate_percentage DESC;

-- ============================================================
-- 5. Readmission Rate by Age Group
-- ============================================================

SELECT
age_group,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage,
ROUND(AVG(previous_admissions), 2) AS average_previous_admissions,
ROUND(AVG(length_of_stay), 2) AS average_length_of_stay
FROM patient_admissions_clean
GROUP BY age_group
ORDER BY readmission_rate_percentage DESC;

-- ============================================================
-- 6. Monthly Readmission Trend
-- ============================================================

SELECT
strftime('%Y', admission_date) AS admission_year,
strftime('%m', admission_date) AS admission_month,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage
FROM patient_admissions_clean
GROUP BY
strftime('%Y', admission_date),
strftime('%m', admission_date)
ORDER BY
admission_year,
admission_month;

-- ============================================================
-- 7. Average Days to Readmission
-- ============================================================

SELECT
previous_admissions,
COUNT(*) AS readmitted_cases,
ROUND(AVG(days_to_readmission), 2) AS average_days_to_readmission,
MIN(days_to_readmission) AS shortest_days_to_readmission,
MAX(days_to_readmission) AS longest_days_to_readmission
FROM patient_admissions_clean
WHERE readmitted_within_30_days = 1
GROUP BY previous_admissions
ORDER BY previous_admissions;

-- ============================================================
-- 8. Short Discharge-to-Readmission Gaps
-- ============================================================

SELECT
patient_id,
admission_id,
admission_date,
discharge_date,
department,
age_group,
previous_admissions,
length_of_stay,
days_to_readmission,
readmitted_within_30_days
FROM patient_admissions_clean
WHERE
readmitted_within_30_days = 1
AND days_to_readmission <= 7
ORDER BY
days_to_readmission ASC,
previous_admissions DESC
LIMIT 20;

-- ============================================================
-- 9. High-Priority Follow-Up List
-- ============================================================

SELECT
patient_id,
admission_id,
discharge_date,
department,
age_group,
previous_admissions,
length_of_stay,
days_to_readmission,
CASE
WHEN previous_admissions >= 4 AND readmitted_within_30_days = 1 THEN 'Very High Priority'
WHEN previous_admissions >= 3 THEN 'High Priority'
WHEN previous_admissions = 2 THEN 'Medium Priority'
ELSE 'Standard Follow-Up'
END AS follow_up_priority
FROM patient_admissions_clean
WHERE previous_admissions >= 2
ORDER BY
CASE
WHEN previous_admissions >= 4 AND readmitted_within_30_days = 1 THEN 1
WHEN previous_admissions >= 3 THEN 2
WHEN previous_admissions = 2 THEN 3
ELSE 4
END,
discharge_date DESC;

-- ============================================================
-- 10. Length of Stay Group and Readmission Rate
-- ============================================================

SELECT
CASE
WHEN length_of_stay BETWEEN 1 AND 3 THEN '1-3 days'
WHEN length_of_stay BETWEEN 4 AND 7 THEN '4-7 days'
WHEN length_of_stay BETWEEN 8 AND 14 THEN '8-14 days'
ELSE '15+ days'
END AS length_of_stay_group,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage
FROM patient_admissions_clean
GROUP BY
CASE
WHEN length_of_stay BETWEEN 1 AND 3 THEN '1-3 days'
WHEN length_of_stay BETWEEN 4 AND 7 THEN '4-7 days'
WHEN length_of_stay BETWEEN 8 AND 14 THEN '8-14 days'
ELSE '15+ days'
END
ORDER BY readmission_rate_percentage DESC;

-- ============================================================
-- 11. Department and Previous Admissions Risk View
-- ============================================================

SELECT
department,
previous_admissions,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage
FROM patient_admissions_clean
GROUP BY
department,
previous_admissions
ORDER BY
department,
previous_admissions;

-- ============================================================
-- 12. Operational Decision-Support Export
-- ============================================================

SELECT
patient_id,
admission_id,
admission_date,
discharge_date,
department,
age_group,
previous_admissions,
length_of_stay,
days_to_readmission,
readmitted_within_30_days,
CASE
WHEN previous_admissions >= 4 THEN 'High readmission pattern'
WHEN previous_admissions BETWEEN 2 AND 3 THEN 'Moderate readmission pattern'
ELSE 'Lower readmission pattern'
END AS risk_pattern,
CASE
WHEN previous_admissions >= 4 THEN 'Review discharge planning and follow-up coordination'
WHEN previous_admissions BETWEEN 2 AND 3 THEN 'Consider stronger follow-up after discharge'
ELSE 'Standard discharge process'
END AS suggested_operational_action
FROM patient_admissions_clean
ORDER BY
previous_admissions DESC,
readmitted_within_30_days DESC,
discharge_date DESC;

-- ============================================================
-- 13. Create a Reusable View for Dashboard Reporting
-- ============================================================

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
CASE
WHEN previous_admissions >= 4 THEN 'High Risk Pattern'
WHEN previous_admissions BETWEEN 2 AND 3 THEN 'Medium Risk Pattern'
ELSE 'Lower Risk Pattern'
END AS risk_pattern
FROM patient_admissions_clean;

-- ============================================================
-- 14. Dashboard View Check
-- ============================================================

SELECT
risk_pattern,
COUNT(*) AS total_admissions,
SUM(readmitted_within_30_days) AS readmissions_30d,
ROUND(
100.0 * SUM(readmitted_within_30_days) / COUNT(*),
2
) AS readmission_rate_percentage
FROM vw_readmission_dashboard
GROUP BY risk_pattern
ORDER BY readmission_rate_percentage DESC;

-- ============================================================
-- End of script
-- ============================================================
