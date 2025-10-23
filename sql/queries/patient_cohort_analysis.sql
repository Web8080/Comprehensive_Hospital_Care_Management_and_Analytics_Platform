-- ==================================================================
-- Patient Cohort Analysis Queries
-- MediCare Analytics Platform
--
-- Author: Victor Ibhafidon
-- Description: Advanced cohort analysis for patient populations.
--              Longitudinal tracking and pattern identification.
-- ==================================================================

-- Frequent Flyer Analysis
-- Identifies patients with multiple admissions
SELECT 
    p.mrn,
    p.first_name || ' ' || p.last_name as patient_name,
    COUNT(DISTINCT a.admission_id) as admission_count,
    MIN(a.admission_date) as first_admission,
    MAX(a.admission_date) as most_recent_admission,
    ROUND(AVG(a.length_of_stay), 1) as avg_los,
    SUM(a.total_charges) as lifetime_charges,
    LISTAGG(DISTINCT d.diagnosis_name, '; ') as diagnoses
FROM dim_patients p
JOIN fact_admissions a ON p.patient_id = a.patient_id
LEFT JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
WHERE a.admission_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY p.patient_id, p.mrn, p.first_name, p.last_name
HAVING COUNT(DISTINCT a.admission_id) >= 3
ORDER BY admission_count DESC;


-- Age-Based Outcome Analysis
-- Compares outcomes across age groups
SELECT 
    CASE 
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 30 THEN '18-29'
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 45 THEN '30-44'
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 65 THEN '45-64'
        ELSE '65+'
    END as age_group,
    COUNT(DISTINCT a.admission_id) as admissions,
    ROUND(AVG(a.length_of_stay), 1) as avg_los,
    ROUND(SUM(CASE WHEN a.is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate,
    ROUND(AVG(a.total_charges), 2) as avg_charges
FROM dim_patients p
JOIN fact_admissions a ON p.patient_id = a.patient_id
WHERE a.discharge_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY 
    CASE 
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 30 THEN '18-29'
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 45 THEN '30-44'
        WHEN DATEDIFF('year', p.date_of_birth, CURRENT_DATE) < 65 THEN '45-64'
        ELSE '65+'
    END
ORDER BY age_group;


-- Diagnosis Pathway Analysis
-- Tracks common diagnosis sequences
WITH patient_sequences AS (
    SELECT 
        a.patient_id,
        a.admission_id,
        a.admission_date,
        d.diagnosis_name,
        ROW_NUMBER() OVER (PARTITION BY a.patient_id ORDER BY a.admission_date) as admission_sequence
    FROM fact_admissions a
    JOIN dim_diagnoses d ON a.primary_diagnosis_id = d.diagnosis_id
    WHERE a.admission_date >= CURRENT_DATE - INTERVAL '24 months'
)
SELECT 
    s1.diagnosis_name as first_diagnosis,
    s2.diagnosis_name as second_diagnosis,
    COUNT(*) as sequence_count,
    ROUND(AVG(DATEDIFF('day', s1.admission_date, s2.admission_date)), 0) as avg_days_between
FROM patient_sequences s1
JOIN patient_sequences s2 
    ON s1.patient_id = s2.patient_id 
    AND s2.admission_sequence = s1.admission_sequence + 1
GROUP BY s1.diagnosis_name, s2.diagnosis_name
HAVING COUNT(*) >= 3
ORDER BY sequence_count DESC
LIMIT 20;

