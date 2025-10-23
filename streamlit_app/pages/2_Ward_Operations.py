"""
Ward Operations Dashboard - Real-time Bed Status and Operational Management

Author: Victor Ibhafidon
Description: Operational dashboard for charge nurses and floor managers displaying real-time bed occupancy,
             48-hour discharge forecasts, and ward-level performance metrics. Enables efficient bed allocation
             and patient flow management.
Pipeline Role: Real-time operational analytics from GOLD layer fact_admissions and dim_wards.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import pandas as pd
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.utils.database import query_to_df
from streamlit_app.utils.queries import (
    QUERY_BED_STATUS,
    QUERY_DISCHARGE_FORECAST
)

st.set_page_config(page_title="Ward Operations", layout="wide")

st.title("Ward Operations Dashboard")
st.markdown("Real-time ward status and operational metrics")

# Bed Status Overview
st.subheader("Current Bed Status by Ward")

try:
    bed_status = query_to_df(QUERY_BED_STATUS)
    
    if not bed_status.empty:
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_beds = bed_status['bed_capacity'].sum()
            st.metric("Total Hospital Beds", f"{total_beds}")
        
        with col2:
            occupied = bed_status['occupied_beds'].sum()
            st.metric("Occupied Beds", f"{occupied}")
        
        with col3:
            available = bed_status['available_beds'].sum()
            st.metric("Available Beds", f"{available}", delta=f"{(available/total_beds*100):.1f}% available")
        
        st.markdown("---")
        
        # Ward-level breakdown
        col_chart, col_table = st.columns([2, 1])
        
        with col_chart:
            fig = px.bar(
                bed_status,
                x='ward_name',
                y=['occupied_beds', 'available_beds'],
                title='Bed Occupancy by Ward',
                labels={'value': 'Number of Beds', 'variable': 'Status'},
                barmode='stack',
                color_discrete_map={'occupied_beds': '#ff6b6b', 'available_beds': '#51cf66'}
            )
            fig.update_layout(height=400)
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_table:
            # Format for display
            display_df = bed_status[['ward_name', 'occupied_beds', 'available_beds', 'occupancy_pct']].copy()
            display_df.columns = ['Ward', 'Occupied', 'Available', 'Occupancy %']
            
            # Color code occupancy
            def highlight_occupancy(val):
                if val > 90:
                    return 'background-color: #ffcccc'
                elif val < 50:
                    return 'background-color: #ccffcc'
                return ''
            
            st.dataframe(
                display_df.style.map(highlight_occupancy, subset=['Occupancy %']),
                hide_index=True,
                use_container_width=True,
                height=400
            )
    else:
        st.info("No bed status data available")

except Exception as e:
    st.error(f"Error loading bed status: {e}")

st.markdown("---")

# Discharge Forecast
st.subheader("Discharge Forecast (Next 48 Hours)")

try:
    discharges = query_to_df(QUERY_DISCHARGE_FORECAST)
    
    if not discharges.empty:
        # Summary
        st.info(f"**{len(discharges)} patients** scheduled for discharge in the next 48 hours")
        
        # Group by discharge date and ward
        col1, col2 = st.columns(2)
        
        with col1:
            # By date
            daily_count = discharges.groupby('discharge_date').size().reset_index(name='count')
            fig = px.bar(
                daily_count,
                x='discharge_date',
                y='count',
                title='Discharges by Date',
                labels={'discharge_date': 'Date', 'count': 'Number of Patients'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # By ward
            ward_count = discharges.groupby('ward_name').size().reset_index(name='count')
            fig = px.pie(
                ward_count,
                names='ward_name',
                values='count',
                title='Discharges by Ward'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Detailed list
        st.subheader("Patient Details")
        
        # Format for display
        display_df = discharges[['mrn', 'patient_name', 'ward_name', 'admission_date', 'discharge_date', 'length_of_stay', 'diagnosis_name']].copy()
        display_df.columns = ['MRN', 'Patient Name', 'Ward', 'Admission Date', 'Discharge Date', 'LOS (days)', 'Diagnosis']
        display_df = display_df.sort_values('Discharge Date')
        
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No upcoming discharges scheduled")

except Exception as e:
    st.error(f"Error loading discharge forecast: {e}")

# Ward Performance Metrics
st.markdown("---")
st.subheader("Ward Performance Metrics")

try:
    # Occupancy trend by ward type
    ward_type_query = """
    SELECT 
        w.ward_type,
        COUNT(a.admission_id) as current_patients,
        SUM(w.bed_capacity) as total_beds,
        ROUND(COUNT(a.admission_id) * 100.0 / SUM(w.bed_capacity), 1) as occupancy_rate
    FROM dim_wards w
    LEFT JOIN fact_admissions a ON w.ward_id = a.ward_id 
        AND (a.discharge_date IS NULL OR a.discharge_date >= CURRENT_DATE)
    GROUP BY w.ward_type
    ORDER BY occupancy_rate DESC
    """
    
    ward_types = query_to_df(ward_type_query)
    
    if not ward_types.empty:
        fig = px.bar(
            ward_types,
            x='ward_type',
            y='occupancy_rate',
            title='Occupancy Rate by Ward Type',
            labels={'ward_type': 'Ward Type', 'occupancy_rate': 'Occupancy %'},
            color='occupancy_rate',
            color_continuous_scale='RdYlGn_r'
        )
        fig.add_hline(y=85, line_dash="dash", line_color="red", annotation_text="Target: 85%")
        st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Error loading ward performance: {e}")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

