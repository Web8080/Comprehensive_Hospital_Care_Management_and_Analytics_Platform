-- ==================================================================
-- KPI Metrics and Analytical Queries
-- MediCare Analytics Platform
-- 
-- Author: Victor Ibhafidon
-- Description: Ad-hoc analytical queries for direct database execution.
--              These queries can be run in Snowflake UI or DuckDB CLI
--              for custom analysis beyond dashboard views.
-- ==================================================================

-- ==================================================================
-- OPERATIONAL KPIs
-- ==================================================================

-- Current Hospital Status
-- Shows real-time bed occupancy and patient census
SELECT 
    CURRENT_DATE as report_date,
    COUNT(DISTINCT a.patient_id) as current_patients,
    (SELECT SUM(bed_capacity) FROM dim_wards) as total_beds,
    ROUND(COUNT(DISTINCT a.patient_id) * 100.0 / 
          (SELECT SUM(bed_capacity) FROM dim_wards), 1) as occupancy_pct,
    COUNT(DISTINCT CASE WHEN a.admission_date = CURRENT_DATE THEN a.admission_id END) as today_admits,
    COUNT(DISTINCT CASE WHEN a.discharge_date = CURRENT_DATE THEN a.admission_id END) as today_discharges
FROM fact_admissions a
WHERE a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE;


-- Average Length of Stay by Month
-- Tracks ALOS trends over time
SELECT 
    TO_CHAR(discharge_date, 'YYYY-MM') as year_month,
    COUNT(*) as discharge_count,
    ROUND(AVG(length_of_stay), 1) as avg_los,
    ROUND(STDDEV(length_of_stay), 1) as std_los,
    MIN(length_of_stay) as min_los,
    MAX(length_of_stay) as max_los
FROM fact_admissions
WHERE discharge_date IS NOT NULL
  AND discharge_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY TO_CHAR(discharge_date, 'YYYY-MM')
ORDER BY year_month;


-- Ward Performance Scorecard
-- Comprehensive metrics by ward
SELECT 
    w.ward_name,
    w.ward_type,
    w.bed_capacity,
    COUNT(DISTINCT a.patient_id) as current_patients,
    ROUND(COUNT(DISTINCT a.patient_id) * 100.0 / w.bed_capacity, 1) as occupancy_pct,
    COUNT(DISTINCT CASE WHEN a.admission_date >= CURRENT_DATE - 30 THEN a.admission_id END) as admissions_30d,
    ROUND(AVG(CASE WHEN a.discharge_date >= CURRENT_DATE - 30 THEN a.length_of_stay END), 1) as avg_los_30d,
    ROUND(SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate
FROM dim_wards w
LEFT JOIN fact_admissions a ON w.ward_id = a.ward_id
    AND (a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE - 30)
GROUP BY w.ward_id, w.ward_name, w.ward_type, w.bed_capacity
ORDER BY occupancy_pct DESC;


-- ==================================================================
-- QUALITY METRICS
-- ==================================================================

-- 30-Day Readmission Analysis
-- Identifies patients readmitted within 30 days
SELECT 
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    d.diagnosis_name as initial_diagnosis,
    a1.admission_date as initial_admission,
    a1.discharge_date as initial_discharge,
    a2.admission_date as readmission_date,
    DATEDIFF('day', a1.discharge_date, a2.admission_date) as days_between,
    a1.length_of_stay as initial_los,
    a2.length_of_stay as readmission_los
FROM fact_admissions a1
JOIN fact_admissions a2 
    ON a1.patient_id = a2.patient_id
    AND a2.admission_date > a1.discharge_date
    AND DATEDIFF('day', a1.discharge_date, a2.admission_date) <= 30
JOIN dim_patients p ON a1.patient_id = p.patient_id
JOIN dim_diagnoses d ON a1.primary_diagnosis_id = d.diagnosis_id
WHERE a1.discharge_date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY a2.admission_date DESC;


-- High-Risk Diagnoses for Readmission
-- Shows which diagnoses have highest readmission rates
SELECT 
    d.diagnosis_name,
    d.category,
    COUNT(DISTINCT a.admission_id) as total_admissions,
    SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) as readmissions,
    ROUND(SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate,
    ROUND(AVG(a.length_of_stay), 1) as avg_los
FROM fact_admissions a
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY d.diagnosis_id, d.diagnosis_name, d.category
HAVING COUNT(*) >= 10  -- Only diagnoses with 10+ cases
ORDER BY readmission_rate DESC
LIMIT 20;


-- Patient Safety: Medication Adherence by Ward
-- Tracks medication administration compliance
SELECT 
    w.ward_name,
    COUNT(*) as total_scheduled_doses,
    SUM(CASE WHEN mar.status = 'Given' THEN 1 ELSE 0 END) as doses_given,
    SUM(CASE WHEN mar.status = 'Missed' THEN 1 ELSE 0 END) as doses_missed,
    SUM(CASE WHEN mar.status = 'Refused' THEN 1 ELSE 0 END) as doses_refused,
    SUM(CASE WHEN mar.status = 'Held' THEN 1 ELSE 0 END) as doses_held,
    ROUND(SUM(CASE WHEN mar.status = 'Given' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as adherence_rate
FROM fact_medication_administration mar
JOIN fact_admissions a ON mar.admission_id = a.admission_id
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE mar.scheduled_datetime >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY w.ward_id, w.ward_name
ORDER BY adherence_rate;


-- ==================================================================
-- FINANCIAL ANALYTICS
-- ==================================================================

-- Revenue Analysis by Department
-- Shows financial performance by department
SELECT 
    w.department,
    COUNT(DISTINCT a.admission_id) as admission_count,
    SUM(a.total_charges) as total_revenue,
    ROUND(AVG(a.total_charges), 2) as avg_revenue_per_admission,
    ROUND(SUM(a.total_charges) / SUM(a.length_of_stay), 2) as revenue_per_patient_day
FROM fact_admissions a
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY w.department
ORDER BY total_revenue DESC;


-- Top Revenue-Generating Procedures
-- Identifies most profitable procedures
SELECT 
    pr.procedure_name,
    pr.procedure_type,
    COUNT(*) as procedure_count,
    SUM(fp.procedure_charges) as total_charges,
    ROUND(AVG(fp.procedure_charges), 2) as avg_charge_per_procedure,
    ROUND(AVG(fp.duration_minutes), 0) as avg_duration_minutes
FROM fact_procedures fp
JOIN dim_procedures pr ON fp.procedure_id = pr.procedure_id
WHERE fp.actual_datetime >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY pr.procedure_id, pr.procedure_name, pr.procedure_type
ORDER BY total_charges DESC
LIMIT 20;


-- Medication Cost Analysis
-- Tracks pharmacy spend by drug class
SELECT 
    m.drug_class,
    COUNT(*) as administration_count,
    COUNT(DISTINCT mar.patient_id) as unique_patients,
    SUM(m.cost_per_unit) as total_cost,
    ROUND(AVG(m.cost_per_unit), 2) as avg_cost_per_dose,
    ROUND(SUM(m.cost_per_unit) / COUNT(DISTINCT mar.patient_id), 2) as cost_per_patient
FROM fact_medication_administration mar
JOIN dim_medications m ON mar.medication_id = m.medication_id
WHERE mar.scheduled_datetime >= CURRENT_DATE - INTERVAL '30 days'
  AND mar.status = 'Given'
GROUP BY m.drug_class
ORDER BY total_cost DESC;


-- ==================================================================
-- PATIENT FLOW ANALYTICS
-- ==================================================================

-- Admission Source Analysis
-- Shows where patients are coming from
SELECT 
    admission_type,
    COUNT(*) as admission_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(length_of_stay), 1) as avg_los,
    SUM(total_charges) as total_revenue
FROM fact_admissions
WHERE admission_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY admission_type
ORDER BY admission_count DESC;


-- Discharge Disposition Trends
-- Tracks where patients go after discharge
SELECT 
    discharge_disposition,
    COUNT(*) as discharge_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(length_of_stay), 1) as avg_los,
    SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) as readmissions_30d,
    ROUND(SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate
FROM fact_admissions
WHERE discharge_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY discharge_disposition
ORDER BY discharge_count DESC;


-- Daily Admission Pattern Analysis
-- Identifies peak admission times
SELECT 
    TO_CHAR(admission_datetime, 'Day') as day_of_week,
    EXTRACT(HOUR FROM admission_datetime) as hour_of_day,
    COUNT(*) as admission_count,
    ROUND(AVG(length_of_stay), 1) as avg_los
FROM fact_admissions
WHERE admission_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY TO_CHAR(admission_datetime, 'Day'), EXTRACT(HOUR FROM admission_datetime)
ORDER BY 
    CASE TO_CHAR(admission_datetime, 'Day')
        WHEN 'Sunday   ' THEN 1
        WHEN 'Monday   ' THEN 2
        WHEN 'Tuesday  ' THEN 3
        WHEN 'Wednesday' THEN 4
        WHEN 'Thursday ' THEN 5
        WHEN 'Friday   ' THEN 6
        WHEN 'Saturday ' THEN 7
    END,
    hour_of_day;


-- ==================================================================
-- CLINICAL ANALYTICS
-- ==================================================================

-- Care Goal Achievement Rate
-- Tracks patient progress toward care goals
SELECT 
    goal_type,
    COUNT(*) as total_goals,
    SUM(CASE WHEN status = 'Achieved' THEN 1 ELSE 0 END) as achieved,
    SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
    SUM(CASE WHEN status = 'Not Started' THEN 1 ELSE 0 END) as not_started,
    SUM(CASE WHEN status = 'Discontinued' THEN 1 ELSE 0 END) as discontinued,
    ROUND(SUM(CASE WHEN status = 'Achieved' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as achievement_rate,
    ROUND(AVG(progress_pct), 1) as avg_progress_pct
FROM fact_care_plan_goals
WHERE created_datetime >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY goal_type
ORDER BY achievement_rate DESC;


-- Vital Signs Abnormality Tracking
-- Identifies patients with abnormal vital signs
SELECT 
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    w.ward_name,
    COUNT(*) as total_readings,
    SUM(CASE WHEN vs.blood_pressure_systolic > 180 OR vs.blood_pressure_diastolic > 120 THEN 1 ELSE 0 END) as hypertensive_crisis_count,
    SUM(CASE WHEN vs.heart_rate > 100 THEN 1 ELSE 0 END) as tachycardia_count,
    SUM(CASE WHEN vs.temperature > 38.0 THEN 1 ELSE 0 END) as fever_count,
    SUM(CASE WHEN vs.oxygen_saturation < 90 THEN 1 ELSE 0 END) as hypoxia_count
FROM fact_vital_signs vs
JOIN fact_admissions a ON vs.admission_id = a.admission_id
JOIN dim_patients p ON vs.patient_id = p.patient_id
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE vs.recorded_datetime >= CURRENT_DATE - INTERVAL '7 days'
  AND (a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE)
GROUP BY p.patient_id, p.mrn, p.first_name, p.last_name, w.ward_name
HAVING SUM(CASE WHEN vs.blood_pressure_systolic > 180 OR vs.blood_pressure_diastolic > 120 THEN 1 ELSE 0 END) > 0
    OR SUM(CASE WHEN vs.oxygen_saturation < 90 THEN 1 ELSE 0 END) > 0
ORDER BY hypertensive_crisis_count DESC, hypoxia_count DESC;


-- Patient Mobility Progress Tracking
-- Monitors improvement in patient mobility
SELECT 
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    MIN(da.activity_date) as first_assessment,
    MAX(da.activity_date) as latest_assessment,
    DATEDIFF('day', MIN(da.activity_date), MAX(da.activity_date)) as days_tracked,
    MIN(da.mobility_score) as initial_mobility,
    MAX(da.mobility_score) as latest_mobility,
    MAX(da.mobility_score) - MIN(da.mobility_score) as improvement,
    ROUND(AVG(da.pain_level), 1) as avg_pain_level
FROM fact_daily_activities da
JOIN dim_patients p ON da.patient_id = p.patient_id
JOIN fact_admissions a ON da.admission_id = a.admission_id
WHERE a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE
GROUP BY p.patient_id, p.mrn, p.first_name, p.last_name
HAVING COUNT(*) >= 3  -- At least 3 assessments
ORDER BY improvement DESC;


-- ==================================================================
-- STAFF PRODUCTIVITY
-- ==================================================================

-- Nurse Workload Analysis
-- Shows documentation and medication administration by nurse
SELECT 
    s.first_name || ' ' || s.last_name as nurse_name,
    s.role,
    w.ward_name,
    COUNT(DISTINCT da.activity_id) as daily_activities_logged,
    COUNT(DISTINCT mar.mar_id) as medications_administered,
    COUNT(DISTINCT vs.vital_id) as vitals_recorded,
    COUNT(DISTINCT da.activity_date) as days_worked
FROM dim_staff s
LEFT JOIN fact_daily_activities da ON s.staff_id = da.recorded_by_staff_id
    AND da.recorded_datetime >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN fact_medication_administration mar ON s.staff_id = mar.administered_by_staff_id
    AND mar.administered_datetime >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN fact_vital_signs vs ON s.staff_id = vs.recorded_by_staff_id
    AND vs.recorded_datetime >= CURRENT_DATE - INTERVAL '30 days'
LEFT JOIN dim_wards w ON s.department = w.department
WHERE s.role IN ('Registered Nurse', 'Licensed Practical Nurse')
  AND s.is_active = TRUE
GROUP BY s.staff_id, s.first_name, s.last_name, s.role, w.ward_name
ORDER BY medications_administered DESC;


-- ==================================================================
-- END OF QUERIES
-- ==================================================================

