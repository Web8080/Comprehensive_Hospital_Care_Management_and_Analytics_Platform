"""
MediCare Analytics Platform - Main Streamlit Application

Author: Victor Ibhafidon
Description: Entry point for the healthcare analytics dashboard. Provides navigation to 5 analytical views
             (Executive, Ward Operations, Patient Care Plan, Medication Analytics, Quality Outcomes).
             Handles database initialization and displays high-level hospital statistics.
Pipeline Role: Presentation layer consuming GOLD layer analytics. 
              Serves as the business intelligence interface for end users.
"""

import streamlit as st
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config import APP_TITLE, HOSPITAL_NAME

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stAlert > div {
        padding: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Main title
st.markdown(f'<div class="main-header">{APP_TITLE}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="sub-header">{HOSPITAL_NAME}</div>', unsafe_allow_html=True)

# Welcome message
st.write("""
Welcome to the MediCare Analytics Platform. This comprehensive dashboard provides real-time insights 
into hospital operations, patient care, and clinical outcomes.
""")

# Navigation instructions
st.info("""
**Getting Started:**
- Use the sidebar to navigate between different dashboard views
- **Executive Dashboard**: High-level KPIs and trends
- **Ward Operations**: Real-time bed status and discharge forecasts  
- **Patient Care Plan**: Individual patient tracking and care management
- **Medication Analytics**: Medication administration tracking and adherence
- **Quality & Outcomes**: Clinical quality metrics and readmission analysis
""")

# Quick stats preview
st.subheader("Quick Overview")

try:
    from streamlit_app.utils.database import query_to_df, initialize_database_from_csv, test_connection
    
    # Test connection
    if not test_connection():
        st.error("Database connection failed. Please check your configuration.")
        st.info("If using DuckDB, click the button below to initialize the database from CSV files.")
        
        if st.button("Initialize Database from CSV"):
            with st.spinner("Loading data..."):
                try:
                    initialize_database_from_csv()
                    st.success("Database initialized successfully!")
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"Initialization failed: {e}")
    else:
        # Display quick stats
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            try:
                result = query_to_df("SELECT COUNT(*) as count FROM dim_patients")
                st.metric("Total Patients", f"{result['count'][0]:,}")
            except:
                st.metric("Total Patients", "N/A")
        
        with col2:
            try:
                result = query_to_df("SELECT COUNT(*) as count FROM fact_admissions")
                st.metric("Total Admissions", f"{result['count'][0]:,}")
            except:
                st.metric("Total Admissions", "N/A")
        
        with col3:
            try:
                result = query_to_df("SELECT COUNT(*) as count FROM dim_staff WHERE is_active = TRUE")
                st.metric("Active Staff", f"{result['count'][0]:,}")
            except:
                st.metric("Active Staff", "N/A")
        
        with col4:
            try:
                result = query_to_df("SELECT SUM(bed_capacity) as count FROM dim_wards")
                st.metric("Total Beds", f"{result['count'][0]:,}")
            except:
                st.metric("Total Beds", "N/A")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("""
    **Troubleshooting:**
    1. Make sure you've run the data generation script: `python scripts/01_generate_data.py`
    2. Check that the database is properly initialized
    3. Verify your database connection settings in the .env file
    """)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9rem;'>
    <p>MediCare Analytics Platform | Built with Streamlit & Snowflake</p>
    <p>For demonstration and portfolio purposes</p>
</div>
""", unsafe_allow_html=True)

