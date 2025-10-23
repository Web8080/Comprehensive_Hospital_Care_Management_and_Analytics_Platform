-- Gold Layer Schema: Analytics-ready Star Schema
-- MediCare Analytics Platform

-- ============================================
-- DIMENSION TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS dim_patients (
    patient_id INTEGER PRIMARY KEY,
    mrn VARCHAR(20) UNIQUE NOT NULL,  -- Medical Record Number
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    blood_type VARCHAR(5),
    address VARCHAR(255),
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    phone VARCHAR(20),
    email VARCHAR(100),
    insurance_provider VARCHAR(100),
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    effective_date DATE,  -- SCD Type 2
    end_date DATE,        -- SCD Type 2
    is_current BOOLEAN,   -- SCD Type 2
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_wards (
    ward_id INTEGER PRIMARY KEY,
    ward_name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    bed_capacity INTEGER,
    ward_type VARCHAR(50),  -- ICU, General, Specialty, etc.
    floor_number INTEGER,
    nurse_station_contact VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_staff (
    staff_id INTEGER PRIMARY KEY,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(100),  -- Doctor, Nurse, Therapist, etc.
    department VARCHAR(100),
    shift_pattern VARCHAR(50),  -- Day, Night, Rotating
    qualifications VARCHAR(255),
    hire_date DATE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_medications (
    medication_id INTEGER PRIMARY KEY,
    drug_name VARCHAR(200) NOT NULL,
    generic_name VARCHAR(200),
    drug_class VARCHAR(100),  -- Antibiotic, Analgesic, etc.
    dosage_form VARCHAR(50),  -- Tablet, Injection, IV, etc.
    manufacturer VARCHAR(100),
    cost_per_unit DECIMAL(10, 2),
    contraindications TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_procedures (
    procedure_id INTEGER PRIMARY KEY,
    procedure_name VARCHAR(200) NOT NULL,
    procedure_type VARCHAR(100),  -- Diagnostic, Therapeutic, Surgical
    department VARCHAR(100),
    avg_duration_minutes INTEGER,
    base_cost DECIMAL(10, 2),
    requires_anesthesia BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_diagnoses (
    diagnosis_id INTEGER PRIMARY KEY,
    icd10_code VARCHAR(10) UNIQUE NOT NULL,
    diagnosis_name VARCHAR(255) NOT NULL,
    category VARCHAR(100),  -- Cardiovascular, Respiratory, etc.
    severity_level VARCHAR(50),  -- Mild, Moderate, Severe, Critical
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_beds (
    bed_id INTEGER PRIMARY KEY,
    ward_id INTEGER,
    bed_number VARCHAR(10),
    bed_type VARCHAR(50),  -- ICU, Isolation, Standard
    has_ventilator BOOLEAN,
    has_monitor BOOLEAN,
    is_available BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (ward_id) REFERENCES dim_wards(ward_id)
);

CREATE TABLE IF NOT EXISTS dim_date (
    date_id INTEGER PRIMARY KEY,
    date DATE UNIQUE NOT NULL,
    day INTEGER,
    day_of_week VARCHAR(20),
    week INTEGER,
    month INTEGER,
    month_name VARCHAR(20),
    quarter INTEGER,
    year INTEGER,
    is_weekend BOOLEAN,
    is_holiday BOOLEAN,
    fiscal_year INTEGER
);

-- ============================================
-- FACT TABLES
-- ============================================

CREATE TABLE IF NOT EXISTS fact_admissions (
    admission_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    ward_id INTEGER,
    bed_id INTEGER,
    admission_date DATE,
    admission_datetime TIMESTAMP,
    discharge_date DATE,
    discharge_datetime TIMESTAMP,
    admission_type VARCHAR(50),  -- Emergency, Scheduled, Transfer
    chief_complaint TEXT,
    primary_diagnosis_id INTEGER,
    secondary_diagnosis_ids VARCHAR(255),  -- Comma-separated
    attending_doctor_id INTEGER,
    length_of_stay INTEGER,  -- Calculated field
    is_readmission BOOLEAN,  -- Within 30 days
    readmission_days_since_discharge INTEGER,
    discharge_disposition VARCHAR(100),  -- Home, Rehab, Expired, etc.
    total_charges DECIMAL(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (ward_id) REFERENCES dim_wards(ward_id),
    FOREIGN KEY (bed_id) REFERENCES dim_beds(bed_id),
    FOREIGN KEY (primary_diagnosis_id) REFERENCES dim_diagnoses(diagnosis_id),
    FOREIGN KEY (attending_doctor_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_medication_administration (
    mar_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    medication_id INTEGER,
    prescribed_by_staff_id INTEGER,
    administered_by_staff_id INTEGER,
    scheduled_datetime TIMESTAMP,
    administered_datetime TIMESTAMP,
    dosage VARCHAR(50),
    route VARCHAR(50),  -- PO (oral), IV, IM (intramuscular), SC (subcutaneous)
    status VARCHAR(50),  -- Given, Missed, Refused, Held
    reason_if_not_given TEXT,
    vital_signs_before VARCHAR(255),  -- JSON or comma-separated
    vital_signs_after VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (medication_id) REFERENCES dim_medications(medication_id),
    FOREIGN KEY (prescribed_by_staff_id) REFERENCES dim_staff(staff_id),
    FOREIGN KEY (administered_by_staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_vital_signs (
    vital_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    recorded_datetime TIMESTAMP,
    recorded_by_staff_id INTEGER,
    blood_pressure_systolic INTEGER,
    blood_pressure_diastolic INTEGER,
    heart_rate INTEGER,
    temperature DECIMAL(4, 1),  -- Celsius
    respiratory_rate INTEGER,
    oxygen_saturation INTEGER,
    pain_level INTEGER,  -- 0-10 scale
    consciousness_level VARCHAR(50),  -- Alert, Confused, Lethargic, Unresponsive
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (recorded_by_staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_procedures (
    procedure_event_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    procedure_id INTEGER,
    performed_by_staff_id INTEGER,
    scheduled_datetime TIMESTAMP,
    actual_datetime TIMESTAMP,
    duration_minutes INTEGER,
    outcome VARCHAR(100),  -- Successful, Complicated, Aborted
    complications TEXT,
    notes TEXT,
    procedure_charges DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (procedure_id) REFERENCES dim_procedures(procedure_id),
    FOREIGN KEY (performed_by_staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_lab_results (
    lab_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    test_type VARCHAR(100),  -- CBC, BMP, Lipid Panel, etc.
    test_name VARCHAR(200),
    ordered_by_staff_id INTEGER,
    collected_datetime TIMESTAMP,
    resulted_datetime TIMESTAMP,
    test_value VARCHAR(100),
    unit_of_measure VARCHAR(50),
    reference_range VARCHAR(100),
    abnormal_flag VARCHAR(20),  -- Normal, High, Low, Critical
    lab_department VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (ordered_by_staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_daily_activities (
    activity_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    activity_date DATE,
    recorded_by_staff_id INTEGER,
    recorded_datetime TIMESTAMP,
    -- Mobility (1-5 scale)
    mobility_score INTEGER,  -- 1=Bedbound, 2=Chair only, 3=Walk with assistance, 4=Walk with device, 5=Independent
    mobility_notes VARCHAR(255),
    -- Self-care (1-5 scale)
    self_care_score INTEGER,  -- 1=Total assistance, 2=Extensive help, 3=Moderate help, 4=Minimal help, 5=Independent
    -- Meals
    breakfast_percent_consumed INTEGER,  -- 0-100
    lunch_percent_consumed INTEGER,
    dinner_percent_consumed INTEGER,
    feeding_assistance_needed BOOLEAN,
    -- Bathroom
    bathroom_independence BOOLEAN,
    continent_bladder BOOLEAN,
    continent_bowel BOOLEAN,
    output_notes VARCHAR(255),
    -- Mental status
    mental_status VARCHAR(50),  -- Alert, Confused, Lethargic, Agitated
    mood VARCHAR(50),  -- Cooperative, Anxious, Depressed, Irritable
    -- Pain management
    pain_level INTEGER,  -- 0-10 scale
    pain_location VARCHAR(100),
    pain_management_effectiveness INTEGER,  -- 1-5 scale
    -- Sleep
    sleep_quality INTEGER,  -- 1-5 scale
    sleep_hours DECIMAL(4, 1),
    -- Comments
    comments TEXT,  -- Free-text nursing observations
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (recorded_by_staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_nursing_notes (
    note_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    staff_id INTEGER,
    note_datetime TIMESTAMP,
    note_type VARCHAR(50),  -- Assessment, Progress, Shift Handoff, Incident
    note_text TEXT,
    severity_flag VARCHAR(20),  -- Routine, Urgent, Critical
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (staff_id) REFERENCES dim_staff(staff_id)
);

CREATE TABLE IF NOT EXISTS fact_care_plan_goals (
    goal_id INTEGER PRIMARY KEY,
    patient_id INTEGER,
    admission_id INTEGER,
    goal_type VARCHAR(100),  -- Mobility, Pain Management, Wound Healing, etc.
    goal_description TEXT,
    target_date DATE,
    status VARCHAR(50),  -- Not Started, In Progress, Achieved, Discontinued
    progress_pct INTEGER,  -- 0-100
    created_by_staff_id INTEGER,
    created_datetime TIMESTAMP,
    last_updated_datetime TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES dim_patients(patient_id),
    FOREIGN KEY (admission_id) REFERENCES fact_admissions(admission_id),
    FOREIGN KEY (created_by_staff_id) REFERENCES dim_staff(staff_id)
);

-- ============================================
-- AGGREGATE TABLES (For Performance)
-- ============================================

CREATE TABLE IF NOT EXISTS agg_daily_ward_metrics (
    date DATE,
    ward_id INTEGER,
    total_patients INTEGER,
    total_admissions INTEGER,
    total_discharges INTEGER,
    bed_occupancy_rate DECIMAL(5, 2),
    avg_length_of_stay DECIMAL(5, 2),
    total_medication_doses INTEGER,
    medication_error_count INTEGER,
    avg_patient_satisfaction DECIMAL(3, 2),
    PRIMARY KEY (date, ward_id),
    FOREIGN KEY (ward_id) REFERENCES dim_wards(ward_id)
);

CREATE TABLE IF NOT EXISTS agg_monthly_kpis (
    year_month VARCHAR(7),  -- YYYY-MM
    total_admissions INTEGER,
    total_discharges INTEGER,
    avg_length_of_stay DECIMAL(5, 2),
    readmission_rate DECIMAL(5, 2),
    mortality_rate DECIMAL(5, 2),
    avg_bed_occupancy_rate DECIMAL(5, 2),
    total_revenue DECIMAL(15, 2),
    total_operating_costs DECIMAL(15, 2),
    PRIMARY KEY (year_month)
);

-- ============================================
-- INDEXES FOR PERFORMANCE
-- ============================================

CREATE INDEX idx_admissions_patient ON fact_admissions(patient_id);
CREATE INDEX idx_admissions_dates ON fact_admissions(admission_date, discharge_date);
CREATE INDEX idx_admissions_ward ON fact_admissions(ward_id);
CREATE INDEX idx_medication_patient ON fact_medication_administration(patient_id);
CREATE INDEX idx_medication_datetime ON fact_medication_administration(scheduled_datetime);
CREATE INDEX idx_vitals_patient ON fact_vital_signs(patient_id);
CREATE INDEX idx_vitals_datetime ON fact_vital_signs(recorded_datetime);
CREATE INDEX idx_activities_patient ON fact_daily_activities(patient_id);
CREATE INDEX idx_activities_date ON fact_daily_activities(activity_date);
CREATE INDEX idx_patients_mrn ON dim_patients(mrn);

