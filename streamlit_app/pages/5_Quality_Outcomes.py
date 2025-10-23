"""
Quality & Outcomes Dashboard - Clinical Excellence and Performance Tracking

Author: Victor Ibhafidon
Description: Quality assurance dashboard for clinical leadership analyzing 30-day readmission rates,
             length of stay trends, discharge dispositions, and quality improvement opportunities.
             Identifies high-risk diagnoses and wards requiring intervention.
Pipeline Role: Population health analytics from GOLD layer aggregated metrics.
              Drives clinical quality initiatives and regulatory compliance.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.utils.database import query_to_df
from streamlit_app.utils.queries import (
    QUERY_READMISSION_BY_DIAGNOSIS,
    QUERY_AVERAGE_LOS_BY_WARD,
    QUERY_READMISSION_RATE
)

st.set_page_config(page_title="Quality & Outcomes", layout="wide")

st.title("Quality & Outcomes Dashboard")
st.markdown("Clinical quality metrics, readmission analysis, and patient outcomes")

# Quality Metrics Overview
st.subheader("Quality Metrics Summary")

try:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        readmit_rate = query_to_df(QUERY_READMISSION_RATE)
        if not readmit_rate.empty:
            rate = readmit_rate['readmission_rate'][0]
            st.metric(
                "30-Day Readmission Rate",
                f"{rate}%",
                delta=f"{rate - 12:.1f}% vs target (12%)",
                delta_color="inverse"
            )
        else:
            st.metric("30-Day Readmission Rate", "N/A")
    
    with col2:
        # Average LOS
        los_query = """
        SELECT ROUND(AVG(length_of_stay), 1) as avg_los
        FROM fact_admissions
        WHERE discharge_date >= CURRENT_DATE - INTERVAL '30 days'
        """
        los = query_to_df(los_query)
        if not los.empty:
            st.metric("Average Length of Stay", f"{los['avg_los'][0]} days")
        else:
            st.metric("Average Length of Stay", "N/A")
    
    with col3:
        # Patient satisfaction (simulated)
        st.metric("Patient Satisfaction Score", "4.2 / 5.0", delta="+0.3 vs last month")

except Exception as e:
    st.error(f"Error loading quality metrics: {e}")

st.markdown("---")

# Readmission Analysis
st.subheader("30-Day Readmission Analysis")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Readmission Rates by Diagnosis")
    
    try:
        readmissions = query_to_df(QUERY_READMISSION_BY_DIAGNOSIS)
        
        if not readmissions.empty:
            fig = px.bar(
                readmissions,
                x='readmission_rate',
                y='diagnosis_name',
                orientation='h',
                title='Top 10 Diagnoses by Readmission Rate',
                labels={'readmission_rate': 'Readmission %', 'diagnosis_name': 'Diagnosis'},
                color='readmission_rate',
                color_continuous_scale='Reds',
                hover_data=['total_admissions', 'readmissions']
            )
            fig.add_vline(x=12, line_dash="dash", line_color="red", annotation_text="Target: 12%")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            display_df = readmissions[['diagnosis_name', 'category', 'total_admissions', 'readmissions', 'readmission_rate']].copy()
            display_df.columns = ['Diagnosis', 'Category', 'Total Admits', 'Readmissions', 'Rate %']
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.info("Insufficient data for readmission analysis")
    
    except Exception as e:
        st.error(f"Error loading readmission data: {e}")

with col2:
    st.markdown("### Readmission Trends Over Time")
    
    try:
        trend_query = """
        SELECT 
            DATE_TRUNC('month', discharge_date) as month,
            COUNT(*) as total_discharges,
            SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) as readmissions,
            ROUND(SUM(CASE WHEN is_readmission THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as readmission_rate
        FROM fact_admissions
        WHERE discharge_date >= CURRENT_DATE - INTERVAL '12 months'
        GROUP BY DATE_TRUNC('month', discharge_date)
        ORDER BY month
        """
        
        trends = query_to_df(trend_query)
        
        if not trends.empty:
            trends['month'] = pd.to_datetime(trends['month'])
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=trends['month'],
                y=trends['readmission_rate'],
                name='Readmission Rate',
                line=dict(color='red', width=3),
                mode='lines+markers'
            ))
            
            fig.add_hline(y=12, line_dash="dash", line_color="green", annotation_text="Target: 12%")
            
            fig.update_layout(
                title='Monthly Readmission Rate Trend',
                xaxis_title='Month',
                yaxis_title='Readmission Rate (%)',
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Stats
            latest_rate = trends.iloc[-1]['readmission_rate']
            avg_rate = trends['readmission_rate'].mean()
            
            if latest_rate < avg_rate:
                st.success(f"Current month ({latest_rate}%) is below 12-month average ({avg_rate:.1f}%)")
            else:
                st.warning(f"Current month ({latest_rate}%) is above 12-month average ({avg_rate:.1f}%)")
        else:
            st.info("Insufficient data for trend analysis")
    
    except Exception as e:
        st.error(f"Error loading readmission trends: {e}")

st.markdown("---")

# Length of Stay Analysis
st.subheader("Length of Stay Analysis")

try:
    los_data = query_to_df(QUERY_AVERAGE_LOS_BY_WARD)
    
    if not los_data.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                los_data.sort_values('avg_los', ascending=False),
                x='ward_name',
                y='avg_los',
                title='Average Length of Stay by Ward',
                labels={'avg_los': 'Avg LOS (days)', 'ward_name': 'Ward'},
                color='ward_type',
                hover_data=['admission_count', 'min_los', 'max_los']
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**LOS Statistics**")
            
            display_df = los_data[['ward_name', 'avg_los', 'admission_count']].copy()
            display_df.columns = ['Ward', 'Avg LOS', 'Admissions']
            display_df = display_df.sort_values('Avg LOS', ascending=False)
            
            st.dataframe(display_df, hide_index=True, use_container_width=True)
    else:
        st.info("No LOS data available")

except Exception as e:
    st.error(f"Error loading LOS data: {e}")

st.markdown("---")

# Patient Flow Analysis
st.subheader("Patient Flow Metrics")

try:
    flow_query = """
    SELECT 
        admission_type,
        COUNT(*) as count,
        ROUND(AVG(length_of_stay), 1) as avg_los
    FROM fact_admissions
    WHERE admission_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY admission_type
    ORDER BY count DESC
    """
    
    flow = query_to_df(flow_query)
    
    if not flow.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.pie(
                flow,
                names='admission_type',
                values='count',
                title='Admissions by Type (Last 90 Days)'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig2 = px.bar(
                flow,
                x='admission_type',
                y='avg_los',
                title='Average LOS by Admission Type',
                labels={'avg_los': 'Avg LOS (days)', 'admission_type': 'Type'},
                color='avg_los',
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig2, use_container_width=True)
    
except Exception as e:
    st.error(f"Error loading patient flow data: {e}")

# Discharge Disposition
st.markdown("---")
st.subheader("Discharge Disposition Analysis")

try:
    disposition_query = """
    SELECT 
        discharge_disposition,
        COUNT(*) as count,
        ROUND(AVG(length_of_stay), 1) as avg_los
    FROM fact_admissions
    WHERE discharge_date >= CURRENT_DATE - INTERVAL '90 days'
    GROUP BY discharge_disposition
    ORDER BY count DESC
    """
    
    disposition = query_to_df(disposition_query)
    
    if not disposition.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                disposition,
                x='discharge_disposition',
                y='count',
                title='Discharge Disposition (Last 90 Days)',
                labels={'count': 'Number of Patients', 'discharge_disposition': 'Disposition'},
                color='avg_los',
                color_continuous_scale='Viridis'
            )
            fig.update_xaxes(tickangle=45)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Disposition Breakdown**")
            
            total_discharges = disposition['count'].sum()
            disposition['percentage'] = (disposition['count'] / total_discharges * 100).round(1)
            
            display_df = disposition[['discharge_disposition', 'count', 'percentage']].copy()
            display_df.columns = ['Disposition', 'Count', '%']
            
            st.dataframe(display_df, hide_index=True, use_container_width=True)
    
except Exception as e:
    st.error(f"Error loading disposition data: {e}")

# Quality Improvement Recommendations
st.markdown("---")
st.subheader("Quality Improvement Recommendations")

try:
    recommendations = []
    
    # Check readmission rate
    readmit = query_to_df(QUERY_READMISSION_RATE)
    if not readmit.empty and readmit['readmission_rate'][0] > 12:
        recommendations.append(
            ("High Readmission Rate", 
             f"Current rate is {readmit['readmission_rate'][0]}%. Focus on discharge planning and follow-up care.")
        )
    
    # Check LOS outliers
    los_data = query_to_df(QUERY_AVERAGE_LOS_BY_WARD)
    if not los_data.empty:
        high_los_wards = los_data[los_data['avg_los'] > los_data['avg_los'].mean() + los_data['avg_los'].std()]
        if not high_los_wards.empty:
            ward_list = ", ".join(high_los_wards['ward_name'].tolist())
            recommendations.append(
                ("High Length of Stay", 
                 f"Wards with above-average LOS: {ward_list}. Review care pathways for efficiency.")
            )
    
    if recommendations:
        for title, desc in recommendations:
            st.warning(f"**{title}:** {desc}")
    else:
        st.success("All quality metrics within acceptable ranges. Continue monitoring.")

except:
    pass

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

