"""
Configuration file for MediCare Analytics Platform

Author: Victor Ibhafidon
Description: Central configuration for the healthcare analytics platform.
             Defines hospital structure, patient parameters, and data generation settings.
             Used by data generation scripts and dashboard application.
Pipeline Role: Provides consistent configuration across all pipeline components.
"""
import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ANALYTICS_DATA_DIR = DATA_DIR / "analytics"

# Database configuration
DATABASE_PATH = DATA_DIR / "medicare_analytics.duckdb"
DATABASE_TYPE = "duckdb"  # Options: duckdb, postgresql, snowflake

# Application settings
APP_TITLE = "MediCare Analytics Platform"
HOSPITAL_NAME = "St. Mary's Medical Center"

# Data generation settings
NUM_PATIENTS = 500
NUM_STAFF = 150
NUM_WARDS = 12
NUM_YEARS = 5
START_DATE = "2020-01-01"

# Ward configurations
WARDS = [
    {"ward_id": 1, "ward_name": "ICU", "department": "Critical Care", "bed_capacity": 20, "ward_type": "Intensive Care", "floor_number": 3},
    {"ward_id": 2, "ward_name": "ICU-2", "department": "Critical Care", "bed_capacity": 20, "ward_type": "Intensive Care", "floor_number": 3},
    {"ward_id": 3, "ward_name": "Emergency", "department": "Emergency Medicine", "bed_capacity": 30, "ward_type": "Emergency", "floor_number": 1},
    {"ward_id": 4, "ward_name": "Cardiology", "department": "Cardiac Care", "bed_capacity": 25, "ward_type": "Specialty", "floor_number": 4},
    {"ward_id": 5, "ward_name": "Maternity", "department": "Obstetrics", "bed_capacity": 20, "ward_type": "Specialty", "floor_number": 2},
    {"ward_id": 6, "ward_name": "Pediatrics", "department": "Pediatrics", "bed_capacity": 30, "ward_type": "Specialty", "floor_number": 2},
    {"ward_id": 7, "ward_name": "Surgery", "department": "Surgical Services", "bed_capacity": 25, "ward_type": "Surgical", "floor_number": 5},
    {"ward_id": 8, "ward_name": "Orthopedics", "department": "Orthopedics", "bed_capacity": 20, "ward_type": "Specialty", "floor_number": 5},
    {"ward_id": 9, "ward_name": "Oncology", "department": "Cancer Care", "bed_capacity": 15, "ward_type": "Specialty", "floor_number": 6},
    {"ward_id": 10, "ward_name": "General Medicine A", "department": "Internal Medicine", "bed_capacity": 40, "ward_type": "General", "floor_number": 4},
    {"ward_id": 11, "ward_name": "General Medicine B", "department": "Internal Medicine", "bed_capacity": 40, "ward_type": "General", "floor_number": 4},
    {"ward_id": 12, "ward_name": "Neurology", "department": "Neurosciences", "bed_capacity": 20, "ward_type": "Specialty", "floor_number": 6},
]

# Staff roles
STAFF_ROLES = [
    "Attending Physician",
    "Resident",
    "Nurse Practitioner",
    "Registered Nurse",
    "Licensed Practical Nurse",
    "Nursing Assistant",
    "Physical Therapist",
    "Occupational Therapist",
    "Respiratory Therapist",
    "Pharmacist",
]

# Medication categories
MEDICATION_CLASSES = [
    "Antibiotic",
    "Analgesic",
    "Anticoagulant",
    "Antihypertensive",
    "Diuretic",
    "Antidiabetic",
    "Anticonvulsant",
    "Bronchodilator",
    "Sedative",
    "Antidepressant",
]

# Common diagnoses (ICD-10 codes)
COMMON_DIAGNOSES = [
    {"icd10_code": "I21.9", "diagnosis_name": "Acute Myocardial Infarction", "category": "Cardiovascular", "severity_level": "Critical"},
    {"icd10_code": "J18.9", "diagnosis_name": "Pneumonia", "category": "Respiratory", "severity_level": "Moderate"},
    {"icd10_code": "I50.9", "diagnosis_name": "Heart Failure", "category": "Cardiovascular", "severity_level": "Serious"},
    {"icd10_code": "N39.0", "diagnosis_name": "Urinary Tract Infection", "category": "Genitourinary", "severity_level": "Mild"},
    {"icd10_code": "E11.9", "diagnosis_name": "Type 2 Diabetes Mellitus", "category": "Endocrine", "severity_level": "Moderate"},
    {"icd10_code": "I63.9", "diagnosis_name": "Cerebral Infarction (Stroke)", "category": "Neurological", "severity_level": "Critical"},
    {"icd10_code": "J44.1", "diagnosis_name": "COPD with Exacerbation", "category": "Respiratory", "severity_level": "Moderate"},
    {"icd10_code": "K80.2", "diagnosis_name": "Cholecystitis", "category": "Digestive", "severity_level": "Moderate"},
    {"icd10_code": "S72.0", "diagnosis_name": "Hip Fracture", "category": "Injury", "severity_level": "Serious"},
    {"icd10_code": "C50.9", "diagnosis_name": "Breast Cancer", "category": "Neoplasm", "severity_level": "Serious"},
    {"icd10_code": "I10", "diagnosis_name": "Essential Hypertension", "category": "Cardiovascular", "severity_level": "Mild"},
    {"icd10_code": "K21.9", "diagnosis_name": "GERD", "category": "Digestive", "severity_level": "Mild"},
]

# Vital signs normal ranges
VITAL_SIGNS_RANGES = {
    "blood_pressure_systolic": (90, 180),
    "blood_pressure_diastolic": (60, 120),
    "heart_rate": (50, 120),
    "temperature": (36.0, 39.0),  # Celsius
    "respiratory_rate": (12, 25),
    "oxygen_saturation": (85, 100),
    "pain_level": (0, 10),
}

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, ANALYTICS_DATA_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

