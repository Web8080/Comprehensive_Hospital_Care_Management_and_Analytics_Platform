"""
Data Generation Script for MediCare Analytics Platform

Author: Victor Ibhafidon
Description: Generates synthetic healthcare data spanning 5 years for 500 patients across 12 hospital wards.
             Creates realistic patient admissions, medication records, vital signs, daily activities, 
             procedures, lab results, and care plan goals. Outputs 15 CSV files representing the Bronze layer.
Pipeline Role: BRONZE LAYER - Initial data ingestion. Produces raw CSV files that feed into ETL transformations.
              Output files are loaded into data warehouse staging area for cleaning and validation.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
from faker import Faker
from datetime import datetime, timedelta
import random
from config import (
    NUM_PATIENTS, NUM_STAFF, NUM_YEARS, START_DATE,
    WARDS, STAFF_ROLES, MEDICATION_CLASSES, COMMON_DIAGNOSES,
    VITAL_SIGNS_RANGES, RAW_DATA_DIR
)

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

print("MediCare Analytics - Data Generation Script")
print("=" * 60)

# ============================================
# Generate Dimension Data
# ============================================

def generate_patients(n=NUM_PATIENTS):
    """Generate patient master data"""
    print(f"Generating {n} patients...")
    
    blood_types = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
    genders = ['Male', 'Female', 'Other']
    insurance_providers = ['Blue Cross', 'Aetna', 'UnitedHealthcare', 'Cigna', 'Medicare', 'Medicaid']
    
    patients = []
    for i in range(1, n + 1):
        gender = random.choice(genders)
        first_name = fake.first_name_male() if gender == 'Male' else fake.first_name_female()
        
        patient = {
            'patient_id': i,
            'mrn': f'MRN{str(i).zfill(8)}',
            'first_name': first_name,
            'last_name': fake.last_name(),
            'date_of_birth': fake.date_of_birth(minimum_age=18, maximum_age=95),
            'gender': gender,
            'blood_type': random.choice(blood_types),
            'address': fake.street_address(),
            'city': fake.city(),
            'state': fake.state_abbr(),
            'zip_code': fake.zipcode(),
            'phone': fake.phone_number(),
            'email': fake.email(),
            'insurance_provider': random.choice(insurance_providers),
            'emergency_contact_name': fake.name(),
            'emergency_contact_phone': fake.phone_number(),
            'effective_date': START_DATE,
            'end_date': None,
            'is_current': True
        }
        patients.append(patient)
    
    df = pd.DataFrame(patients)
    print(f"[DONE] Generated {len(df)} patients")
    return df

def generate_staff(n=NUM_STAFF):
    """Generate hospital staff"""
    print(f"Generating {n} staff members...")
    
    shift_patterns = ['Day', 'Night', 'Rotating', 'On-Call']
    
    staff = []
    for i in range(1, n + 1):
        role = random.choice(STAFF_ROLES)
        department = random.choice([w['department'] for w in WARDS])
        
        staff_member = {
            'staff_id': i,
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'role': role,
            'department': department,
            'shift_pattern': random.choice(shift_patterns),
            'qualifications': f"Licensed {role}",
            'hire_date': fake.date_between(start_date='-15y', end_date='-1y'),
            'is_active': True
        }
        staff.append(staff_member)
    
    df = pd.DataFrame(staff)
    print(f"[DONE] Generated {len(df)} staff members")
    return df

def generate_wards():
    """Generate ward/department data"""
    print(f"Generating {len(WARDS)} wards...")
    df = pd.DataFrame(WARDS)
    df['nurse_station_contact'] = [fake.phone_number() for _ in range(len(df))]
    print(f"[DONE] Generated {len(df)} wards")
    return df

def generate_medications(n=200):
    """Generate medication formulary"""
    print(f"Generating {n} medications...")
    
    dosage_forms = ['Tablet', 'Capsule', 'Injection', 'IV Solution', 'Topical Cream', 'Inhaler']
    manufacturers = ['Pfizer', 'Novartis', 'Roche', 'Merck', 'GSK', 'AstraZeneca']
    
    medications = []
    for i in range(1, n + 1):
        drug_class = random.choice(MEDICATION_CLASSES)
        medications.append({
            'medication_id': i,
            'drug_name': fake.word().capitalize() + 'zole',
            'generic_name': fake.word().capitalize() + 'mine',
            'drug_class': drug_class,
            'dosage_form': random.choice(dosage_forms),
            'manufacturer': random.choice(manufacturers),
            'cost_per_unit': round(random.uniform(0.5, 500), 2),
            'contraindications': 'Allergy to ' + drug_class
        })
    
    df = pd.DataFrame(medications)
    print(f"[DONE] Generated {len(df)} medications")
    return df

def generate_procedures(n=100):
    """Generate medical procedures"""
    print(f"Generating {n} procedures...")
    
    procedure_types = ['Diagnostic', 'Therapeutic', 'Surgical', 'Rehabilitative']
    
    procedures = []
    for i in range(1, n + 1):
        procedure_type = random.choice(procedure_types)
        procedures.append({
            'procedure_id': i,
            'procedure_name': fake.catch_phrase().replace(',', ''),
            'procedure_type': procedure_type,
            'department': random.choice([w['department'] for w in WARDS]),
            'avg_duration_minutes': random.randint(15, 480),
            'base_cost': round(random.uniform(100, 50000), 2),
            'requires_anesthesia': procedure_type == 'Surgical'
        })
    
    df = pd.DataFrame(procedures)
    print(f"[DONE] Generated {len(df)} procedures")
    return df

def generate_diagnoses():
    """Generate diagnosis codes"""
    print(f"Generating diagnoses...")
    df = pd.DataFrame(COMMON_DIAGNOSES)
    df['diagnosis_id'] = range(1, len(df) + 1)
    print(f"[DONE] Generated {len(df)} diagnoses")
    return df

def generate_beds():
    """Generate bed inventory"""
    print(f"Generating beds...")
    
    beds = []
    bed_id = 1
    for ward in WARDS:
        for bed_num in range(1, ward['bed_capacity'] + 1):
            bed_type = 'ICU' if 'ICU' in ward['ward_name'] else 'Standard'
            beds.append({
                'bed_id': bed_id,
                'ward_id': ward['ward_id'],
                'bed_number': f"{ward['ward_name'][:3].upper()}-{bed_num:03d}",
                'bed_type': bed_type,
                'has_ventilator': bed_type == 'ICU',
                'has_monitor': True,
                'is_available': random.choice([True, False])
            })
            bed_id += 1
    
    df = pd.DataFrame(beds)
    print(f"[DONE] Generated {len(df)} beds")
    return df

def generate_date_dimension(start_date, num_years=NUM_YEARS):
    """Generate date dimension"""
    print(f"Generating date dimension ({num_years} years)...")
    
    start = pd.to_datetime(start_date)
    end = start + pd.DateOffset(years=num_years)
    dates = pd.date_range(start, end, freq='D')
    
    date_dim = pd.DataFrame({
        'date_id': range(1, len(dates) + 1),
        'date': dates,
        'day': dates.day,
        'day_of_week': dates.day_name(),
        'week': dates.isocalendar().week,
        'month': dates.month,
        'month_name': dates.month_name(),
        'quarter': dates.quarter,
        'year': dates.year,
        'is_weekend': dates.dayofweek >= 5,
        'is_holiday': False,  # Simplified
        'fiscal_year': dates.year
    })
    
    print(f"[DONE] Generated {len(date_dim)} date records")
    return date_dim

# ============================================
# Generate Fact Data
# ============================================

def generate_admissions(patients_df, wards_df, diagnoses_df, staff_df, beds_df, start_date, num_years=NUM_YEARS):
    """Generate admission records"""
    print(f"Generating admissions ({num_years} years)...")
    
    start = pd.to_datetime(start_date)
    end = start + pd.DateOffset(years=num_years)
    
    admission_types = ['Emergency', 'Scheduled', 'Transfer']
    dispositions = ['Home', 'Rehab Facility', 'Nursing Home', 'Expired', 'Transfer', 'Left AMA']
    
    # Generate 2-5 admissions per patient over 5 years
    admissions = []
    admission_id = 1
    
    for _, patient in patients_df.iterrows():
        num_admissions = random.randint(2, 5)
        
        for adm_num in range(num_admissions):
            # Random admission date
            days_offset = random.randint(0, (end - start).days)
            admission_datetime = start + timedelta(days=days_offset, hours=random.randint(0, 23), minutes=random.randint(0, 59))
            
            # Length of stay varies by severity
            diagnosis = diagnoses_df.sample(1).iloc[0]
            if diagnosis['severity_level'] == 'Critical':
                los = random.randint(5, 21)
            elif diagnosis['severity_level'] == 'Serious':
                los = random.randint(3, 14)
            else:
                los = random.randint(1, 7)
            
            discharge_datetime = admission_datetime + timedelta(days=los)
            
            # Check for readmission
            is_readmission = False
            if adm_num > 0:
                prev_discharge = admissions[admission_id - 2]['discharge_datetime']
                days_since = (admission_datetime - prev_discharge).days
                if days_since <= 30:
                    is_readmission = True
            
            ward = wards_df.sample(1).iloc[0]
            bed = beds_df[beds_df['ward_id'] == ward['ward_id']].sample(1).iloc[0]
            doctor = staff_df[staff_df['role'].isin(['Attending Physician', 'Resident'])].sample(1).iloc[0]
            
            admission = {
                'admission_id': admission_id,
                'patient_id': patient['patient_id'],
                'ward_id': ward['ward_id'],
                'bed_id': bed['bed_id'],
                'admission_date': admission_datetime.date(),
                'admission_datetime': admission_datetime,
                'discharge_date': discharge_datetime.date(),
                'discharge_datetime': discharge_datetime,
                'admission_type': random.choice(admission_types),
                'chief_complaint': diagnosis['diagnosis_name'],
                'primary_diagnosis_id': diagnosis['diagnosis_id'],
                'secondary_diagnosis_ids': ','.join(map(str, diagnoses_df.sample(random.randint(0, 2))['diagnosis_id'].tolist())),
                'attending_doctor_id': doctor['staff_id'],
                'length_of_stay': los,
                'is_readmission': is_readmission,
                'readmission_days_since_discharge': None,
                'discharge_disposition': random.choice(dispositions),
                'total_charges': round(random.uniform(5000, 150000), 2)
            }
            admissions.append(admission)
            admission_id += 1
    
    df = pd.DataFrame(admissions)
    print(f"[DONE] Generated {len(df)} admissions")
    return df

def generate_medication_administration(admissions_df, medications_df, staff_df):
    """Generate medication administration records (MAR)"""
    print(f"Generating medication administration records...")
    
    routes = ['PO', 'IV', 'IM', 'SC', 'Topical', 'Inhaled']
    statuses = ['Given', 'Given', 'Given', 'Given', 'Given', 'Missed', 'Refused', 'Held']  # Weighted toward "Given"
    
    mar_records = []
    mar_id = 1
    
    # Sample 30% of admissions for performance
    sampled_admissions = admissions_df.sample(frac=0.3)
    
    for _, admission in sampled_admissions.iterrows():
        # Each patient gets 3-8 scheduled medications
        num_meds = random.randint(3, 8)
        meds = medications_df.sample(num_meds)
        
        for _, med in meds.iterrows():
            # Generate doses for each day of admission
            for day in range(admission['length_of_stay']):
                # Medication schedule (1-4 times per day)
                doses_per_day = random.randint(1, 4)
                
                for dose in range(doses_per_day):
                    scheduled_dt = admission['admission_datetime'] + timedelta(days=day, hours=8*dose)
                    status = random.choice(statuses)
                    
                    if status == 'Given':
                        administered_dt = scheduled_dt + timedelta(minutes=random.randint(-30, 60))
                    else:
                        administered_dt = None
                    
                    prescriber = staff_df[staff_df['role'].isin(['Attending Physician', 'Resident'])].sample(1).iloc[0]
                    nurse = staff_df[staff_df['role'] == 'Registered Nurse'].sample(1).iloc[0]
                    
                    mar_records.append({
                        'mar_id': mar_id,
                        'patient_id': admission['patient_id'],
                        'admission_id': admission['admission_id'],
                        'medication_id': med['medication_id'],
                        'prescribed_by_staff_id': prescriber['staff_id'],
                        'administered_by_staff_id': nurse['staff_id'] if status == 'Given' else None,
                        'scheduled_datetime': scheduled_dt,
                        'administered_datetime': administered_dt,
                        'dosage': f"{random.choice([10, 25, 50, 100, 250, 500])} {random.choice(['mg', 'mcg', 'units'])}",
                        'route': random.choice(routes),
                        'status': status,
                        'reason_if_not_given': 'Patient asleep' if status == 'Missed' else ('Patient refused' if status == 'Refused' else ('Low BP' if status == 'Held' else None)),
                        'vital_signs_before': None,
                        'vital_signs_after': None
                    })
                    mar_id += 1
    
    df = pd.DataFrame(mar_records)
    print(f"[DONE] Generated {len(df)} medication administration records")
    return df

def generate_vital_signs(admissions_df, staff_df):
    """Generate vital signs measurements"""
    print(f"Generating vital signs...")
    
    vitals = []
    vital_id = 1
    
    # Sample 30% of admissions
    sampled_admissions = admissions_df.sample(frac=0.3)
    
    for _, admission in sampled_admissions.iterrows():
        # Vital signs checked 2-4 times per day
        checks_per_day = random.randint(2, 4)
        
        for day in range(admission['length_of_stay']):
            for check in range(checks_per_day):
                recorded_dt = admission['admission_datetime'] + timedelta(days=day, hours=6*check)
                nurse = staff_df[staff_df['role'] == 'Registered Nurse'].sample(1).iloc[0]
                
                vitals.append({
                    'vital_id': vital_id,
                    'patient_id': admission['patient_id'],
                    'admission_id': admission['admission_id'],
                    'recorded_datetime': recorded_dt,
                    'recorded_by_staff_id': nurse['staff_id'],
                    'blood_pressure_systolic': random.randint(90, 180),
                    'blood_pressure_diastolic': random.randint(60, 120),
                    'heart_rate': random.randint(55, 120),
                    'temperature': round(random.uniform(36.0, 39.0), 1),
                    'respiratory_rate': random.randint(12, 24),
                    'oxygen_saturation': random.randint(88, 100),
                    'pain_level': random.randint(0, 8),
                    'consciousness_level': random.choice(['Alert', 'Alert', 'Alert', 'Confused', 'Lethargic'])
                })
                vital_id += 1
    
    df = pd.DataFrame(vitals)
    print(f"[DONE] Generated {len(df)} vital signs records")
    return df

def generate_daily_activities(admissions_df, staff_df):
    """Generate daily activity logs (ADL)"""
    print(f"Generating daily activity logs...")
    
    mental_statuses = ['Alert', 'Alert', 'Confused', 'Lethargic', 'Agitated']
    moods = ['Cooperative', 'Cooperative', 'Anxious', 'Depressed', 'Irritable']
    
    activities = []
    activity_id = 1
    
    # Sample 40% of admissions
    sampled_admissions = admissions_df.sample(frac=0.4)
    
    for _, admission in sampled_admissions.iterrows():
        for day in range(admission['length_of_stay']):
            activity_date = (admission['admission_datetime'] + timedelta(days=day)).date()
            nurse = staff_df[staff_df['role'] == 'Registered Nurse'].sample(1).iloc[0]
            
            # Comments array for variation
            possible_comments = [
                "Patient ambulated to hallway with walker, good progress today.",
                "Patient complained of pain in right hip during PT session.",
                "Family visited today, patient mood improved significantly.",
                "Patient required extensive assistance with morning hygiene.",
                "Good appetite today, finished most meals independently.",
                "Patient expressed desire to go home, education provided.",
                "Wound dressing changed, healing well per nursing assessment.",
                "Patient participated in physical therapy exercises reluctantly.",
                "Overnight sleep interrupted 3x for medications/vitals.",
                "Patient displayed confusion this morning, resolved by afternoon.",
                "No bowel movement for 2 days, physician notified.",
                "Patient tolerated ambulation better today vs yesterday.",
            ]
            
            activities.append({
                'activity_id': activity_id,
                'patient_id': admission['patient_id'],
                'admission_id': admission['admission_id'],
                'activity_date': activity_date,
                'recorded_by_staff_id': nurse['staff_id'],
                'recorded_datetime': admission['admission_datetime'] + timedelta(days=day, hours=20),
                'mobility_score': random.randint(1, 5),
                'mobility_notes': random.choice(['Walked to chair (assisted)', 'Bedbound', 'Walked hallway with walker', 'Independent ambulation']),
                'self_care_score': random.randint(1, 5),
                'breakfast_percent_consumed': random.randint(25, 100),
                'lunch_percent_consumed': random.randint(25, 100),
                'dinner_percent_consumed': random.randint(25, 100),
                'feeding_assistance_needed': random.choice([True, False]),
                'bathroom_independence': random.choice([True, True, False]),
                'continent_bladder': random.choice([True, True, True, False]),
                'continent_bowel': random.choice([True, True, True, False]),
                'output_notes': random.choice(['Urination normal', 'No BM today', 'Catheter in place', 'Normal output']),
                'mental_status': random.choice(mental_statuses),
                'mood': random.choice(moods),
                'pain_level': random.randint(0, 7),
                'pain_location': random.choice(['None', 'Abdomen', 'Hip', 'Chest', 'Back', 'Head']),
                'pain_management_effectiveness': random.randint(1, 5),
                'sleep_quality': random.randint(2, 5),
                'sleep_hours': round(random.uniform(4.0, 9.0), 1),
                'comments': random.choice(possible_comments) if random.random() > 0.3 else None  # 70% have comments
            })
            activity_id += 1
    
    df = pd.DataFrame(activities)
    print(f"[DONE] Generated {len(df)} daily activity records")
    return df

def generate_procedure_events(admissions_df, procedures_df, staff_df):
    """Generate procedure events"""
    print(f"Generating procedure events...")
    
    outcomes = ['Successful', 'Successful', 'Successful', 'Complicated', 'Aborted']
    
    procedure_events = []
    event_id = 1
    
    # 40% of admissions have procedures
    admissions_with_procedures = admissions_df.sample(frac=0.4)
    
    for _, admission in admissions_with_procedures.iterrows():
        num_procedures = random.randint(1, 3)
        
        for proc_num in range(num_procedures):
            procedure = procedures_df.sample(1).iloc[0]
            doctor = staff_df[staff_df['role'].isin(['Attending Physician', 'Resident'])].sample(1).iloc[0]
            
            scheduled_dt = admission['admission_datetime'] + timedelta(days=random.randint(0, admission['length_of_stay']-1), hours=random.randint(8, 17))
            actual_dt = scheduled_dt + timedelta(minutes=random.randint(-30, 120))
            
            procedure_events.append({
                'procedure_event_id': event_id,
                'patient_id': admission['patient_id'],
                'admission_id': admission['admission_id'],
                'procedure_id': procedure['procedure_id'],
                'performed_by_staff_id': doctor['staff_id'],
                'scheduled_datetime': scheduled_dt,
                'actual_datetime': actual_dt,
                'duration_minutes': procedure['avg_duration_minutes'] + random.randint(-30, 60),
                'outcome': random.choice(outcomes),
                'complications': 'Minor bleeding' if random.random() > 0.9 else None,
                'notes': 'Procedure completed as planned',
                'procedure_charges': procedure['base_cost']
            })
            event_id += 1
    
    df = pd.DataFrame(procedure_events)
    print(f"[DONE] Generated {len(df)} procedure events")
    return df

def generate_lab_results(admissions_df, staff_df):
    """Generate lab test results"""
    print(f"Generating lab results...")
    
    test_types = [
        ('CBC', 'Hemoglobin', '12-16 g/dL', 'g/dL'),
        ('CBC', 'WBC Count', '4-11 K/uL', 'K/uL'),
        ('BMP', 'Sodium', '135-145 mEq/L', 'mEq/L'),
        ('BMP', 'Potassium', '3.5-5.0 mEq/L', 'mEq/L'),
        ('BMP', 'Glucose', '70-100 mg/dL', 'mg/dL'),
        ('Lipid Panel', 'Total Cholesterol', '<200 mg/dL', 'mg/dL'),
        ('Lipid Panel', 'HDL', '>40 mg/dL', 'mg/dL'),
        ('Liver Function', 'ALT', '7-56 U/L', 'U/L'),
    ]
    
    abnormal_flags = ['Normal', 'Normal', 'Normal', 'High', 'Low', 'Critical']
    
    labs = []
    lab_id = 1
    
    # 50% of admissions have labs
    admissions_with_labs = admissions_df.sample(frac=0.5)
    
    for _, admission in admissions_with_labs.iterrows():
        num_lab_panels = random.randint(1, 4)
        
        for _ in range(num_lab_panels):
            test = random.choice(test_types)
            doctor = staff_df[staff_df['role'].isin(['Attending Physician', 'Resident'])].sample(1).iloc[0]
            
            collected_dt = admission['admission_datetime'] + timedelta(days=random.randint(0, admission['length_of_stay']-1), hours=random.randint(6, 10))
            resulted_dt = collected_dt + timedelta(hours=random.randint(2, 24))
            
            labs.append({
                'lab_id': lab_id,
                'patient_id': admission['patient_id'],
                'admission_id': admission['admission_id'],
                'test_type': test[0],
                'test_name': test[1],
                'ordered_by_staff_id': doctor['staff_id'],
                'collected_datetime': collected_dt,
                'resulted_datetime': resulted_dt,
                'test_value': str(round(random.uniform(50, 200), 1)),
                'unit_of_measure': test[3],
                'reference_range': test[2],
                'abnormal_flag': random.choice(abnormal_flags),
                'lab_department': 'Clinical Lab'
            })
            lab_id += 1
    
    df = pd.DataFrame(labs)
    print(f"[DONE] Generated {len(df)} lab results")
    return df

def generate_care_plan_goals(admissions_df, staff_df):
    """Generate care plan goals"""
    print(f"Generating care plan goals...")
    
    goal_templates = [
        ('Mobility', 'Walk 50 feet independently by discharge'),
        ('Mobility', 'Transfer from bed to chair with minimal assistance'),
        ('Pain Management', 'Maintain pain level below 4/10'),
        ('Wound Healing', 'Wound fully healed within 2 weeks'),
        ('Self-Care', 'Complete morning hygiene independently'),
        ('Nutrition', 'Consume 75% of meals without assistance'),
        ('Education', 'Patient verbalizes understanding of discharge medications'),
    ]
    
    statuses = ['Not Started', 'In Progress', 'In Progress', 'In Progress', 'Achieved', 'Discontinued']
    
    goals = []
    goal_id = 1
    
    # 60% of admissions have care plan goals
    admissions_with_goals = admissions_df.sample(frac=0.6)
    
    for _, admission in admissions_with_goals.iterrows():
        num_goals = random.randint(2, 4)
        
        for _ in range(num_goals):
            goal_template = random.choice(goal_templates)
            nurse = staff_df[staff_df['role'] == 'Registered Nurse'].sample(1).iloc[0]
            
            status = random.choice(statuses)
            if status == 'Achieved':
                progress = 100
            elif status == 'In Progress':
                progress = random.randint(30, 90)
            else:
                progress = 0
            
            goals.append({
                'goal_id': goal_id,
                'patient_id': admission['patient_id'],
                'admission_id': admission['admission_id'],
                'goal_type': goal_template[0],
                'goal_description': goal_template[1],
                'target_date': admission['discharge_date'],
                'status': status,
                'progress_pct': progress,
                'created_by_staff_id': nurse['staff_id'],
                'created_datetime': admission['admission_datetime'] + timedelta(hours=random.randint(2, 24)),
                'last_updated_datetime': admission['admission_datetime'] + timedelta(days=random.randint(1, admission['length_of_stay']))
            })
            goal_id += 1
    
    df = pd.DataFrame(goals)
    print(f"[DONE] Generated {len(df)} care plan goals")
    return df

# ============================================
# Main Execution
# ============================================

def main():
    print("\nStarting data generation process...")
    print(f"Output directory: {RAW_DATA_DIR}\n")
    
    # Generate dimensions
    patients_df = generate_patients()
    staff_df = generate_staff()
    wards_df = generate_wards()
    medications_df = generate_medications()
    procedures_df = generate_procedures()
    diagnoses_df = generate_diagnoses()
    beds_df = generate_beds()
    date_df = generate_date_dimension(START_DATE)
    
    # Generate facts
    admissions_df = generate_admissions(patients_df, wards_df, diagnoses_df, staff_df, beds_df, START_DATE)
    mar_df = generate_medication_administration(admissions_df, medications_df, staff_df)
    vitals_df = generate_vital_signs(admissions_df, staff_df)
    activities_df = generate_daily_activities(admissions_df, staff_df)
    procedures_events_df = generate_procedure_events(admissions_df, procedures_df, staff_df)
    labs_df = generate_lab_results(admissions_df, staff_df)
    goals_df = generate_care_plan_goals(admissions_df, staff_df)
    
    # Save to CSV
    print("\nSaving data to CSV files...")
    
    datasets = {
        'dim_patients.csv': patients_df,
        'dim_staff.csv': staff_df,
        'dim_wards.csv': wards_df,
        'dim_medications.csv': medications_df,
        'dim_procedures.csv': procedures_df,
        'dim_diagnoses.csv': diagnoses_df,
        'dim_beds.csv': beds_df,
        'dim_date.csv': date_df,
        'fact_admissions.csv': admissions_df,
        'fact_medication_administration.csv': mar_df,
        'fact_vital_signs.csv': vitals_df,
        'fact_daily_activities.csv': activities_df,
        'fact_procedures.csv': procedures_events_df,
        'fact_lab_results.csv': labs_df,
        'fact_care_plan_goals.csv': goals_df,
    }
    
    for filename, df in datasets.items():
        filepath = RAW_DATA_DIR / filename
        df.to_csv(filepath, index=False)
        print(f"  [SAVED] {filename} ({len(df):,} records)")
    
    # Summary statistics
    print("\n" + "=" * 60)
    print("DATA GENERATION SUMMARY")
    print("=" * 60)
    print(f"Total Patients: {len(patients_df):,}")
    print(f"Total Staff: {len(staff_df):,}")
    print(f"Total Admissions: {len(admissions_df):,}")
    print(f"Total Medication Doses: {len(mar_df):,}")
    print(f"Total Vital Signs: {len(vitals_df):,}")
    print(f"Total Daily Activities: {len(activities_df):,}")
    print(f"Total Procedures: {len(procedures_events_df):,}")
    print(f"Total Lab Results: {len(labs_df):,}")
    print(f"Total Care Goals: {len(goals_df):,}")
    print(f"\nDate Range: {START_DATE} to {(pd.to_datetime(START_DATE) + pd.DateOffset(years=NUM_YEARS)).date()}")
    print(f"Average Admissions per Patient: {len(admissions_df) / len(patients_df):.1f}")
    print(f"Average Length of Stay: {admissions_df['length_of_stay'].mean():.1f} days")
    print(f"Readmission Rate: {(admissions_df['is_readmission'].sum() / len(admissions_df) * 100):.1f}%")
    print("\n[COMPLETE] Data generation complete!")
    print(f"All files saved to: {RAW_DATA_DIR}")
    print("\nNext step: Load data into Snowflake and run Matillion ETL jobs")

if __name__ == '__main__':
    main()

