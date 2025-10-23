-- ==================================================================
-- Matillion ETL Transformation Scripts
-- MediCare Analytics Platform
-- ==================================================================
--
-- These SQL scripts are designed to be used in Matillion ETL jobs
-- Copy and paste these into your Matillion transformation components
--
-- Pipeline: BRONZE → SILVER → GOLD
--
-- ==================================================================

-- ==================================================================
-- BRONZE TO SILVER TRANSFORMATIONS
-- Purpose: Clean, validate, and standardize raw data
-- ==================================================================

-- --------------------------------------------------------------
-- SILVER: Cleaned Admissions
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.CLEANED_ADMISSIONS AS
SELECT
    CAST(admission_id AS INTEGER) AS admission_id,
    CAST(patient_id AS INTEGER) AS patient_id,
    CAST(ward_id AS INTEGER) AS ward_id,
    CAST(bed_id AS INTEGER) AS bed_id,
    
    -- Date conversions
    CAST(admission_date AS DATE) AS admission_date,
    CAST(admission_datetime AS TIMESTAMP) AS admission_datetime,
    CAST(discharge_date AS DATE) AS discharge_date,
    CAST(discharge_datetime AS TIMESTAMP) AS discharge_datetime,
    
    -- String fields
    UPPER(TRIM(admission_type)) AS admission_type,
    chief_complaint,
    
    -- IDs
    CAST(primary_diagnosis_id AS INTEGER) AS primary_diagnosis_id,
    secondary_diagnosis_ids,
    CAST(attending_doctor_id AS INTEGER) AS attending_doctor_id,
    
    -- Calculated fields
    CAST(length_of_stay AS INTEGER) AS length_of_stay,
    CAST(is_readmission AS BOOLEAN) AS is_readmission,
    readmission_days_since_discharge,
    discharge_disposition,
    CAST(total_charges AS DECIMAL(12, 2)) AS total_charges,
    
    -- Audit fields
    CURRENT_TIMESTAMP() AS processed_timestamp
FROM BRONZE.FACT_ADMISSIONS
WHERE admission_date IS NOT NULL
  AND admission_datetime IS NOT NULL
  AND discharge_datetime >= admission_datetime  -- Business rule validation
  AND length_of_stay >= 0;

-- --------------------------------------------------------------
-- SILVER: Cleaned Medications
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.CLEANED_MEDICATION_ADMINISTRATION AS
SELECT
    CAST(mar_id AS INTEGER) AS mar_id,
    CAST(patient_id AS INTEGER) AS patient_id,
    CAST(admission_id AS INTEGER) AS admission_id,
    CAST(medication_id AS INTEGER) AS medication_id,
    CAST(prescribed_by_staff_id AS INTEGER) AS prescribed_by_staff_id,
    CAST(administered_by_staff_id AS INTEGER) AS administered_by_staff_id,
    
    -- Timestamps
    CAST(scheduled_datetime AS TIMESTAMP) AS scheduled_datetime,
    CAST(administered_datetime AS TIMESTAMP) AS administered_datetime,
    
    -- Medication details
    TRIM(dosage) AS dosage,
    UPPER(TRIM(route)) AS route,
    UPPER(TRIM(status)) AS status,
    reason_if_not_given,
    
    -- Calculate if medication was given on time (within 1 hour window)
    CASE 
        WHEN status = 'Given' 
            AND ABS(DATEDIFF('minute', scheduled_datetime, administered_datetime)) <= 60 
        THEN TRUE
        ELSE FALSE
    END AS given_on_time,
    
    -- Audit
    CURRENT_TIMESTAMP() AS processed_timestamp
FROM BRONZE.FACT_MEDICATION_ADMINISTRATION
WHERE scheduled_datetime IS NOT NULL
  AND status IN ('Given', 'Missed', 'Refused', 'Held');

-- --------------------------------------------------------------
-- SILVER: Cleaned Vital Signs
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.CLEANED_VITAL_SIGNS AS
SELECT
    CAST(vital_id AS INTEGER) AS vital_id,
    CAST(patient_id AS INTEGER) AS patient_id,
    CAST(admission_id AS INTEGER) AS admission_id,
    CAST(recorded_datetime AS TIMESTAMP) AS recorded_datetime,
    CAST(recorded_by_staff_id AS INTEGER) AS recorded_by_staff_id,
    
    -- Vital signs with range validation
    CASE 
        WHEN blood_pressure_systolic BETWEEN 70 AND 250 
        THEN CAST(blood_pressure_systolic AS INTEGER)
        ELSE NULL
    END AS blood_pressure_systolic,
    
    CASE 
        WHEN blood_pressure_diastolic BETWEEN 40 AND 150 
        THEN CAST(blood_pressure_diastolic AS INTEGER)
        ELSE NULL
    END AS blood_pressure_diastolic,
    
    CASE 
        WHEN heart_rate BETWEEN 30 AND 200 
        THEN CAST(heart_rate AS INTEGER)
        ELSE NULL
    END AS heart_rate,
    
    CASE 
        WHEN temperature BETWEEN 32.0 AND 43.0 
        THEN CAST(temperature AS DECIMAL(4, 1))
        ELSE NULL
    END AS temperature,
    
    CASE 
        WHEN respiratory_rate BETWEEN 8 AND 40 
        THEN CAST(respiratory_rate AS INTEGER)
        ELSE NULL
    END AS respiratory_rate,
    
    CASE 
        WHEN oxygen_saturation BETWEEN 70 AND 100 
        THEN CAST(oxygen_saturation AS INTEGER)
        ELSE NULL
    END AS oxygen_saturation,
    
    CAST(pain_level AS INTEGER) AS pain_level,
    consciousness_level,
    
    -- Audit
    CURRENT_TIMESTAMP() AS processed_timestamp
FROM BRONZE.FACT_VITAL_SIGNS
WHERE recorded_datetime IS NOT NULL;

-- --------------------------------------------------------------
-- SILVER: Cleaned Daily Activities
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE SILVER.CLEANED_DAILY_ACTIVITIES AS
SELECT
    CAST(activity_id AS INTEGER) AS activity_id,
    CAST(patient_id AS INTEGER) AS patient_id,
    CAST(admission_id AS INTEGER) AS admission_id,
    CAST(activity_date AS DATE) AS activity_date,
    CAST(recorded_by_staff_id AS INTEGER) AS recorded_by_staff_id,
    CAST(recorded_datetime AS TIMESTAMP) AS recorded_datetime,
    
    -- Mobility & self-care
    CAST(mobility_score AS INTEGER) AS mobility_score,
    mobility_notes,
    CAST(self_care_score AS INTEGER) AS self_care_score,
    
    -- Meals
    CAST(breakfast_percent_consumed AS INTEGER) AS breakfast_percent_consumed,
    CAST(lunch_percent_consumed AS INTEGER) AS lunch_percent_consumed,
    CAST(dinner_percent_consumed AS INTEGER) AS dinner_percent_consumed,
    CAST(feeding_assistance_needed AS BOOLEAN) AS feeding_assistance_needed,
    
    -- Bathroom
    CAST(bathroom_independence AS BOOLEAN) AS bathroom_independence,
    CAST(continent_bladder AS BOOLEAN) AS continent_bladder,
    CAST(continent_bowel AS BOOLEAN) AS continent_bowel,
    output_notes,
    
    -- Mental status
    mental_status,
    mood,
    
    -- Pain & sleep
    CAST(pain_level AS INTEGER) AS pain_level,
    pain_location,
    CAST(pain_management_effectiveness AS INTEGER) AS pain_management_effectiveness,
    CAST(sleep_quality AS INTEGER) AS sleep_quality,
    CAST(sleep_hours AS DECIMAL(4, 1)) AS sleep_hours,
    
    -- COMMENTS (Important field)
    comments,
    
    -- Audit
    CURRENT_TIMESTAMP() AS processed_timestamp
FROM BRONZE.FACT_DAILY_ACTIVITIES
WHERE activity_date IS NOT NULL;

-- ==================================================================
-- SILVER TO GOLD TRANSFORMATIONS
-- Purpose: Build analytics-ready star schema with derived metrics
-- ==================================================================

-- --------------------------------------------------------------
-- GOLD: Fact Admissions (with calculated metrics)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.FACT_ADMISSIONS AS
SELECT
    a.admission_id,
    a.patient_id,
    a.ward_id,
    a.bed_id,
    a.admission_date,
    a.admission_datetime,
    a.discharge_date,
    a.discharge_datetime,
    a.admission_type,
    a.chief_complaint,
    a.primary_diagnosis_id,
    a.secondary_diagnosis_ids,
    a.attending_doctor_id,
    a.length_of_stay,
    a.discharge_disposition,
    a.total_charges,
    
    -- Calculated: Is this a readmission?
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM SILVER.CLEANED_ADMISSIONS prev
            WHERE prev.patient_id = a.patient_id
              AND prev.discharge_date < a.admission_date
              AND DATEDIFF('day', prev.discharge_date, a.admission_date) <= 30
        ) THEN TRUE
        ELSE FALSE
    END AS is_readmission,
    
    -- Calculated: Days since last discharge (for readmissions)
    (
        SELECT MIN(DATEDIFF('day', prev.discharge_date, a.admission_date))
        FROM SILVER.CLEANED_ADMISSIONS prev
        WHERE prev.patient_id = a.patient_id
          AND prev.discharge_date < a.admission_date
    ) AS readmission_days_since_discharge,
    
    -- Date dimension FK
    d.date_id AS admission_date_id,
    
    CURRENT_TIMESTAMP() AS created_at
FROM SILVER.CLEANED_ADMISSIONS a
LEFT JOIN GOLD.DIM_DATE d ON a.admission_date = d.date;

-- --------------------------------------------------------------
-- GOLD: Fact Medication Administration (with adherence metrics)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.FACT_MEDICATION_ADMINISTRATION AS
SELECT
    mar_id,
    patient_id,
    admission_id,
    medication_id,
    prescribed_by_staff_id,
    administered_by_staff_id,
    scheduled_datetime,
    administered_datetime,
    dosage,
    route,
    status,
    reason_if_not_given,
    given_on_time,
    
    -- Calculate delay in minutes (for "Given" status)
    CASE 
        WHEN status = 'Given' AND administered_datetime IS NOT NULL
        THEN DATEDIFF('minute', scheduled_datetime, administered_datetime)
        ELSE NULL
    END AS administration_delay_minutes,
    
    -- Categorize administration timeliness
    CASE 
        WHEN status != 'Given' THEN 'Not Administered'
        WHEN ABS(DATEDIFF('minute', scheduled_datetime, administered_datetime)) <= 30 
            THEN 'On Time'
        WHEN DATEDIFF('minute', scheduled_datetime, administered_datetime) > 30 
            THEN 'Late'
        WHEN DATEDIFF('minute', scheduled_datetime, administered_datetime) < -30 
            THEN 'Early'
        ELSE 'Unknown'
    END AS timeliness_category,
    
    CURRENT_TIMESTAMP() AS created_at
FROM SILVER.CLEANED_MEDICATION_ADMINISTRATION;

-- --------------------------------------------------------------
-- GOLD: Fact Vital Signs (with abnormal flags)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.FACT_VITAL_SIGNS AS
SELECT
    vital_id,
    patient_id,
    admission_id,
    recorded_datetime,
    recorded_by_staff_id,
    blood_pressure_systolic,
    blood_pressure_diastolic,
    heart_rate,
    temperature,
    respiratory_rate,
    oxygen_saturation,
    pain_level,
    consciousness_level,
    
    -- Abnormal vital sign flags
    CASE 
        WHEN blood_pressure_systolic > 180 OR blood_pressure_diastolic > 120 THEN TRUE
        ELSE FALSE
    END AS hypertensive_crisis,
    
    CASE 
        WHEN heart_rate > 100 THEN TRUE ELSE FALSE
    END AS tachycardia,
    
    CASE 
        WHEN heart_rate < 60 THEN TRUE ELSE FALSE
    END AS bradycardia,
    
    CASE 
        WHEN temperature > 38.0 THEN TRUE ELSE FALSE
    END AS fever,
    
    CASE 
        WHEN oxygen_saturation < 90 THEN TRUE ELSE FALSE
    END AS hypoxia,
    
    CASE 
        WHEN respiratory_rate > 20 THEN TRUE ELSE FALSE
    END AS tachypnea,
    
    CURRENT_TIMESTAMP() AS created_at
FROM SILVER.CLEANED_VITAL_SIGNS;

-- --------------------------------------------------------------
-- GOLD: Fact Daily Activities (as-is, already clean)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.FACT_DAILY_ACTIVITIES AS
SELECT
    *,
    CURRENT_TIMESTAMP() AS created_at
FROM SILVER.CLEANED_DAILY_ACTIVITIES;

-- ==================================================================
-- AGGREGATE TABLES (For Dashboard Performance)
-- ==================================================================

-- --------------------------------------------------------------
-- Daily Ward Metrics (for Executive Dashboard)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.AGG_DAILY_WARD_METRICS AS
SELECT
    a.admission_date AS date,
    a.ward_id,
    COUNT(DISTINCT a.patient_id) AS total_patients,
    COUNT(CASE WHEN a.admission_date = CURRENT_DATE THEN 1 END) AS total_admissions,
    COUNT(CASE WHEN a.discharge_date = CURRENT_DATE THEN 1 END) AS total_discharges,
    ROUND(COUNT(DISTINCT a.patient_id) * 100.0 / w.bed_capacity, 2) AS bed_occupancy_rate,
    ROUND(AVG(a.length_of_stay), 1) AS avg_length_of_stay,
    
    -- Medication metrics
    (
        SELECT COUNT(*)
        FROM GOLD.FACT_MEDICATION_ADMINISTRATION m
        WHERE m.admission_id = a.admission_id
          AND DATE(m.scheduled_datetime) = a.admission_date
    ) AS total_medication_doses,
    
    (
        SELECT COUNT(*)
        FROM GOLD.FACT_MEDICATION_ADMINISTRATION m
        WHERE m.admission_id = a.admission_id
          AND DATE(m.scheduled_datetime) = a.admission_date
          AND m.status != 'Given'
    ) AS medication_error_count,
    
    CURRENT_TIMESTAMP() AS created_at
FROM GOLD.FACT_ADMISSIONS a
JOIN GOLD.DIM_WARDS w ON a.ward_id = w.ward_id
GROUP BY a.admission_date, a.ward_id, w.bed_capacity;

-- --------------------------------------------------------------
-- Monthly KPIs (for trending analysis)
-- --------------------------------------------------------------
CREATE OR REPLACE TABLE GOLD.AGG_MONTHLY_KPIS AS
SELECT
    TO_CHAR(admission_date, 'YYYY-MM') AS year_month,
    COUNT(*) AS total_admissions,
    COUNT(CASE WHEN discharge_date IS NOT NULL THEN 1 END) AS total_discharges,
    ROUND(AVG(length_of_stay), 1) AS avg_length_of_stay,
    ROUND(SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS readmission_rate,
    SUM(total_charges) AS total_revenue,
    CURRENT_TIMESTAMP() AS created_at
FROM GOLD.FACT_ADMISSIONS
GROUP BY TO_CHAR(admission_date, 'YYYY-MM');

-- ==================================================================
-- DATA QUALITY CHECKS
-- ==================================================================

-- Run these after each ETL job to validate data quality

-- Check for duplicate admission IDs
SELECT 
    'Duplicate Admission IDs' AS check_name,
    COUNT(*) - COUNT(DISTINCT admission_id) AS error_count
FROM GOLD.FACT_ADMISSIONS
HAVING COUNT(*) - COUNT(DISTINCT admission_id) > 0;

-- Check for invalid date ranges
SELECT 
    'Invalid Date Ranges' AS check_name,
    COUNT(*) AS error_count
FROM GOLD.FACT_ADMISSIONS
WHERE discharge_datetime < admission_datetime;

-- Check for orphaned records (missing patient FK)
SELECT 
    'Orphaned Admissions' AS check_name,
    COUNT(*) AS error_count
FROM GOLD.FACT_ADMISSIONS a
LEFT JOIN GOLD.DIM_PATIENTS p ON a.patient_id = p.patient_id
WHERE p.patient_id IS NULL;

-- Check medication adherence rate
SELECT 
    'Overall Medication Adherence' AS metric_name,
    ROUND(SUM(CASE WHEN status = 'Given' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS value
FROM GOLD.FACT_MEDICATION_ADMINISTRATION;

-- ==================================================================
-- MATILLION JOB STRUCTURE RECOMMENDATION
-- ==================================================================

/*
Recommended Matillion Job Structure:

JOB 1: Bronze_to_Silver_Dimensions
  └─ Load and clean all dimension tables
  └─ Run time: 2-5 minutes

JOB 2: Bronze_to_Silver_Facts
  └─ Load and clean all fact tables
  └─ Run time: 5-15 minutes (depending on volume)

JOB 3: Silver_to_Gold_StarSchema
  └─ Build final analytics tables with derived metrics
  └─ Run time: 10-20 minutes

JOB 4: Gold_Aggregates
  └─ Build aggregate tables for dashboard performance
  └─ Run time: 3-5 minutes

JOB 5: Data_Quality_Checks
  └─ Run validation queries
  └─ Send alerts if errors found
  └─ Run time: 1-2 minutes

ORCHESTRATION: Master_Pipeline
  └─ Run jobs 1-5 in sequence
  └─ Schedule: Daily at 2 AM
  └─ Total runtime: ~30-45 minutes
*/

-- ==================================================================
-- END OF TRANSFORMATION SCRIPTS
-- ==================================================================

