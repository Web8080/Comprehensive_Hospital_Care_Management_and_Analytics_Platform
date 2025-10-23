"""
Reusable SQL Queries for MediCare Analytics Platform

Author: Victor Ibhafidon
Description: Centralized repository of analytical SQL queries optimized for dashboard performance.
             Contains 30+ parameterized queries for KPIs, patient searches, medication tracking,
             and quality metrics. Queries target the GOLD layer star schema.
Pipeline Role: Analytics layer that transforms GOLD layer data into business insights.
              Supports all 5 dashboard views with efficient, reusable SQL patterns.
"""

# Executive Dashboard Queries

QUERY_CURRENT_OCCUPANCY = """
SELECT 
    COUNT(DISTINCT a.patient_id) as current_patients,
    (SELECT SUM(bed_capacity) FROM dim_wards) as total_beds,
    ROUND(COUNT(DISTINCT a.patient_id) * 100.0 / (SELECT SUM(bed_capacity) FROM dim_wards), 1) as occupancy_rate
FROM fact_admissions a
WHERE a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE
"""

QUERY_AVG_LENGTH_OF_STAY = """
SELECT 
    ROUND(AVG(length_of_stay), 1) as avg_los
FROM fact_admissions
WHERE discharge_date >= CURRENT_DATE - INTERVAL '30 days'
"""

QUERY_READMISSION_RATE = """
SELECT 
    ROUND(SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate
FROM fact_admissions
WHERE discharge_date >= CURRENT_DATE - INTERVAL '30 days'
"""

QUERY_TODAY_ADMISSIONS = """
SELECT 
    COUNT(*) as today_admissions
FROM fact_admissions
WHERE admission_date = CURRENT_DATE
"""

QUERY_ADMISSION_TRENDS = """
SELECT 
    DATE_TRUNC('month', admission_date) as month,
    COUNT(*) as admission_count
FROM fact_admissions
GROUP BY DATE_TRUNC('month', admission_date)
ORDER BY month
"""

QUERY_REVENUE_BY_DEPARTMENT = """
SELECT 
    w.department,
    SUM(a.total_charges) as total_revenue,
    COUNT(*) as admission_count
FROM fact_admissions a
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY w.department
ORDER BY total_revenue DESC
"""

QUERY_TOP_DIAGNOSES = """
SELECT 
    d.diagnosis_name,
    d.category,
    COUNT(*) as count
FROM fact_admissions a
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.admission_date >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY d.diagnosis_name, d.category
ORDER BY count DESC
LIMIT 10
"""

# Ward Operations Queries

QUERY_BED_STATUS = """
SELECT 
    w.ward_name,
    w.bed_capacity,
    COUNT(a.admission_id) as occupied_beds,
    w.bed_capacity - COUNT(a.admission_id) as available_beds,
    ROUND(COUNT(a.admission_id) * 100.0 / w.bed_capacity, 1) as occupancy_pct
FROM dim_wards w
LEFT JOIN fact_admissions a ON w.ward_id = a.ward_id 
    AND (a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE)
GROUP BY w.ward_id, w.ward_name, w.bed_capacity
ORDER BY w.ward_name
"""

QUERY_DISCHARGE_FORECAST = """
SELECT 
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    w.ward_name,
    a.admission_date,
    a.discharge_date,
    a.length_of_stay,
    d.diagnosis_name
FROM fact_admissions a
JOIN dim_patients p ON a.patient_id = p.patient_id
JOIN dim_wards w ON a.ward_id = w.ward_id
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.discharge_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '2 days'
ORDER BY a.discharge_date, w.ward_name
"""

# Patient Care Plan Queries

QUERY_SEARCH_PATIENTS = """
SELECT 
    p.patient_id,
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    p.date_of_birth,
    p.gender,
    p.blood_type,
    a.admission_id,
    a.admission_date,
    a.discharge_date,
    w.ward_name,
    b.bed_number,
    d.diagnosis_name,
    s.first_name || ' ' || s.last_name as attending_doctor
FROM dim_patients p
JOIN fact_admissions a ON p.patient_id = a.patient_id
JOIN dim_wards w ON a.ward_id = w.ward_id
LEFT JOIN dim_beds b ON a.bed_id = b.bed_id
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
JOIN dim_staff s ON a.attending_doctor_id = s.staff_id
WHERE (
    p.mrn LIKE ? 
    OR LOWER(p.first_name || ' ' || p.last_name) LIKE LOWER(?)
    OR LOWER(w.ward_name) LIKE LOWER(?)
  )
ORDER BY a.admission_date DESC
LIMIT 20
"""

QUERY_PATIENT_DETAILS = """
SELECT 
    p.*,
    a.admission_id,
    a.admission_date,
    a.discharge_date,
    a.admission_type,
    a.chief_complaint,
    a.length_of_stay,
    w.ward_name,
    w.department,
    b.bed_number,
    d.diagnosis_name,
    d.severity_level,
    s.first_name || ' ' || s.last_name as attending_doctor
FROM dim_patients p
JOIN fact_admissions a ON p.patient_id = a.patient_id
JOIN dim_wards w ON a.ward_id = w.ward_id
LEFT JOIN dim_beds b ON a.bed_id = b.bed_id
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
JOIN dim_staff s ON a.attending_doctor_id = s.staff_id
WHERE p.patient_id = ?
ORDER BY a.admission_date DESC
LIMIT 1
"""

QUERY_PATIENT_MEDICATIONS = """
SELECT 
    m.drug_name,
    m.dosage_form,
    mar.dosage,
    mar.route,
    mar.scheduled_datetime,
    mar.administered_datetime,
    mar.status,
    mar.reason_if_not_given,
    s.first_name || ' ' || s.last_name as administered_by
FROM fact_medication_administration mar
JOIN dim_medications m ON mar.medication_id = m.medication_id
LEFT JOIN dim_staff s ON mar.administered_by_staff_id = s.staff_id
WHERE mar.admission_id = ?
  AND mar.scheduled_datetime >= CURRENT_DATE - INTERVAL '3 days'
ORDER BY mar.scheduled_datetime DESC
"""

QUERY_PATIENT_VITALS = """
SELECT 
    recorded_datetime,
    blood_pressure_systolic,
    blood_pressure_diastolic,
    heart_rate,
    temperature,
    respiratory_rate,
    oxygen_saturation,
    pain_level,
    consciousness_level
FROM fact_vital_signs
WHERE admission_id = ?
  AND recorded_datetime >= CURRENT_DATE - INTERVAL '3 days'
ORDER BY recorded_datetime DESC
"""

QUERY_PATIENT_DAILY_ACTIVITIES = """
SELECT 
    activity_date,
    mobility_score,
    mobility_notes,
    self_care_score,
    breakfast_percent_consumed,
    lunch_percent_consumed,
    dinner_percent_consumed,
    bathroom_independence,
    mental_status,
    mood,
    pain_level,
    sleep_quality,
    comments,
    s.first_name || ' ' || s.last_name as recorded_by
FROM fact_daily_activities fa
LEFT JOIN dim_staff s ON fa.recorded_by_staff_id = s.staff_id
WHERE fa.admission_id = ?
ORDER BY fa.activity_date DESC
LIMIT 7
"""

QUERY_PATIENT_LABS = """
SELECT 
    lab_id,
    test_type,
    test_name,
    test_value,
    unit_of_measure,
    reference_range,
    abnormal_flag,
    collected_datetime,
    resulted_datetime
FROM fact_lab_results
WHERE admission_id = ?
ORDER BY collected_datetime DESC
LIMIT 20
"""

QUERY_PATIENT_PROCEDURES = """
SELECT 
    p.procedure_name,
    p.procedure_type,
    fp.scheduled_datetime,
    fp.actual_datetime,
    fp.duration_minutes,
    fp.outcome,
    fp.notes,
    s.first_name || ' ' || s.last_name as performed_by
FROM fact_procedures fp
JOIN dim_procedures p ON fp.procedure_id = p.procedure_id
LEFT JOIN dim_staff s ON fp.performed_by_staff_id = s.staff_id
WHERE fp.admission_id = ?
ORDER BY fp.actual_datetime DESC
"""

QUERY_PATIENT_CARE_GOALS = """
SELECT 
    goal_id,
    goal_type,
    goal_description,
    target_date,
    status,
    progress_pct,
    created_datetime,
    last_updated_datetime
FROM fact_care_plan_goals
WHERE admission_id = ?
  AND status IN ('In Progress', 'Not Started')
ORDER BY created_datetime DESC
"""

QUERY_PATIENT_HISTORY = """
SELECT 
    a.admission_date,
    a.discharge_date,
    a.length_of_stay,
    a.admission_type,
    w.ward_name,
    d.diagnosis_name,
    a.discharge_disposition
FROM fact_admissions a
JOIN dim_wards w ON a.ward_id = w.ward_id
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.patient_id = ?
  AND a.discharge_date < CURRENT_DATE
ORDER BY a.admission_date DESC
LIMIT 10
"""

# Medication Analytics Queries

QUERY_MEDICATION_ADHERENCE = """
SELECT 
    w.ward_name,
    COUNT(*) as total_doses,
    SUM(CASE WHEN mar.status = 'Given' THEN 1 ELSE 0 END) as doses_given,
    ROUND(SUM(CASE WHEN mar.status = 'Given' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as adherence_rate
FROM fact_medication_administration mar
JOIN fact_admissions a ON mar.admission_id = a.admission_id
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE mar.scheduled_datetime >= (SELECT MAX(scheduled_datetime) FROM fact_medication_administration) - INTERVAL '30 days'
GROUP BY w.ward_name
ORDER BY adherence_rate
"""

QUERY_MEDICATION_ERRORS = """
SELECT 
    w.ward_name,
    mar.status,
    COUNT(*) as count
FROM fact_medication_administration mar
JOIN fact_admissions a ON mar.admission_id = a.admission_id
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE mar.scheduled_datetime >= (SELECT MAX(scheduled_datetime) FROM fact_medication_administration) - INTERVAL '60 days'
  AND mar.status IN ('Missed', 'Refused', 'Held')
GROUP BY w.ward_name, mar.status
ORDER BY w.ward_name, count DESC
"""

QUERY_TOP_MEDICATIONS = """
SELECT 
    m.drug_name,
    m.drug_class,
    COUNT(*) as administration_count,
    SUM(m.cost_per_unit) as total_cost
FROM fact_medication_administration mar
JOIN dim_medications m ON mar.medication_id = m.medication_id
WHERE mar.scheduled_datetime >= (SELECT MAX(scheduled_datetime) FROM fact_medication_administration) - INTERVAL '90 days'
GROUP BY m.medication_id, m.drug_name, m.drug_class
ORDER BY administration_count DESC
LIMIT 15
"""

# Quality & Outcomes Queries

QUERY_READMISSION_BY_DIAGNOSIS = """
SELECT 
    d.diagnosis_name,
    d.category,
    COUNT(*) as total_admissions,
    SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) as readmissions,
    ROUND(SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate
FROM fact_admissions a
JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '180 days'
GROUP BY d.diagnosis_name, d.category
HAVING COUNT(*) >= 10
ORDER BY readmission_rate DESC
LIMIT 10
"""

QUERY_AVERAGE_LOS_BY_WARD = """
SELECT 
    w.ward_name,
    w.ward_type,
    COUNT(*) as admission_count,
    ROUND(AVG(a.length_of_stay), 1) as avg_los,
    MIN(a.length_of_stay) as min_los,
    MAX(a.length_of_stay) as max_los
FROM fact_admissions a
JOIN dim_wards w ON a.ward_id = w.ward_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY w.ward_name, w.ward_type
ORDER BY avg_los DESC
"""

