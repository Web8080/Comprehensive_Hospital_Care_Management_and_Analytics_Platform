"""
Executive Dashboard - High-level KPIs and Hospital Performance Metrics

Author: Victor Ibhafidon
Description: Strategic dashboard for hospital administrators showing occupancy rates, length of stay,
             readmission rates, admission trends, revenue analysis, and top diagnoses. 
             Provides automated alerts when metrics exceed target thresholds.
Pipeline Role: Consumes aggregated GOLD layer data to deliver executive-level insights.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.utils.database import query_to_df
from streamlit_app.utils.queries import (
    QUERY_CURRENT_OCCUPANCY,
    QUERY_AVG_LENGTH_OF_STAY,
    QUERY_READMISSION_RATE,
    QUERY_TODAY_ADMISSIONS,
    QUERY_ADMISSION_TRENDS,
    QUERY_REVENUE_BY_DEPARTMENT,
    QUERY_TOP_DIAGNOSES
)

st.set_page_config(page_title="Executive Dashboard", layout="wide")

st.title("Executive Dashboard")
st.markdown("Hospital-wide performance metrics and key indicators")

# KPI Cards
st.subheader("Key Performance Indicators")

try:
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        occupancy = query_to_df(QUERY_CURRENT_OCCUPANCY)
        if not occupancy.empty:
            rate = occupancy['occupancy_rate'][0]
            st.metric(
                "Bed Occupancy Rate",
                f"{rate}%",
                delta=f"{rate - 85:.1f}% vs target" if rate else None,
                delta_color="inverse"  # Red if above 85%
            )
        else:
            st.metric("Bed Occupancy Rate", "N/A")
    
    with col2:
        los = query_to_df(QUERY_AVG_LENGTH_OF_STAY)
        if not los.empty:
            avg_los = los['avg_los'][0]
            st.metric("Avg Length of Stay", f"{avg_los} days")
        else:
            st.metric("Avg Length of Stay", "N/A")
    
    with col3:
        readmit = query_to_df(QUERY_READMISSION_RATE)
        if not readmit.empty:
            rate = readmit['readmission_rate'][0]
            st.metric(
                "30-Day Readmission Rate",
                f"{rate}%",
                delta=f"{rate - 12:.1f}% vs target" if rate else None,
                delta_color="inverse"
            )
        else:
            st.metric("30-Day Readmission Rate", "N/A")
    
    with col4:
        today_admits = query_to_df(QUERY_TODAY_ADMISSIONS)
        if not today_admits.empty:
            count = today_admits['today_admissions'][0]
            st.metric("Today's Admissions", f"{count}")
        else:
            st.metric("Today's Admissions", "0")

except Exception as e:
    st.error(f"Error loading KPIs: {e}")

st.markdown("---")

# Admission Trends
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Admission Trends (Last 12 Months)")
    try:
        trends = query_to_df(QUERY_ADMISSION_TRENDS)
        if not trends.empty:
            # Get last 12 months
            trends['month'] = pd.to_datetime(trends['month'])
            trends = trends.sort_values('month').tail(12)
            
            fig = px.line(
                trends,
                x='month',
                y='admission_count',
                title='Monthly Admissions',
                labels={'month': 'Month', 'admission_count': 'Admissions'},
                markers=True
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No admission data available")
    except Exception as e:
        st.error(f"Error loading trends: {e}")

with col_right:
    st.subheader("Top 10 Diagnoses (Last 6 Months)")
    try:
        diagnoses = query_to_df(QUERY_TOP_DIAGNOSES)
        if not diagnoses.empty:
            fig = px.bar(
                diagnoses,
                x='count',
                y='diagnosis_name',
                orientation='h',
                color='category',
                title='Most Common Diagnoses',
                labels={'count': 'Number of Cases', 'diagnosis_name': 'Diagnosis'}
            )
            fig.update_layout(height=400, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No diagnosis data available")
    except Exception as e:
        st.error(f"Error loading diagnoses: {e}")

st.markdown("---")

# Revenue Analysis
st.subheader("Revenue by Department (Last 90 Days)")

try:
    revenue = query_to_df(QUERY_REVENUE_BY_DEPARTMENT)
    if not revenue.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                revenue,
                x='department',
                y='total_revenue',
                title='Total Revenue by Department',
                labels={'department': 'Department', 'total_revenue': 'Revenue ($)'},
                color='total_revenue',
                color_continuous_scale='Blues'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.dataframe(
                revenue[['department', 'total_revenue', 'admission_count']].head(10),
                hide_index=True,
                use_container_width=True
            )
    else:
        st.info("No revenue data available")
except Exception as e:
    st.error(f"Error loading revenue data: {e}")

# Alert Section
st.markdown("---")
st.subheader("Alerts & Notifications")

try:
    # Check for critical metrics
    alerts = []
    
    occupancy = query_to_df(QUERY_CURRENT_OCCUPANCY)
    if not occupancy.empty and occupancy['occupancy_rate'][0] > 90:
        alerts.append(("warning", f"High occupancy rate: {occupancy['occupancy_rate'][0]}% (Target: <90%)"))
    
    readmit = query_to_df(QUERY_READMISSION_RATE)
    if not readmit.empty and readmit['readmission_rate'][0] > 15:
        alerts.append(("error", f"Elevated readmission rate: {readmit['readmission_rate'][0]}% (Target: <12%)"))
    
    if alerts:
        for alert_type, message in alerts:
            if alert_type == "error":
                st.error(message)
            else:
                st.warning(message)
    else:
        st.success("All metrics within normal ranges")

except:
    pass

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

