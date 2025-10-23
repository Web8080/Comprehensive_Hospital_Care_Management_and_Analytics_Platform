"""
Medication Analytics Dashboard - Safety and Adherence Monitoring

Author: Victor Ibhafidon
Description: Pharmacy and quality assurance dashboard tracking medication administration adherence,
             error rates (missed/refused/held doses), cost analysis, and timing patterns.
             Provides ward-level safety alerts when adherence falls below 95% target.
Pipeline Role: Patient safety analytics from GOLD layer fact_medication_administration.
              Supports quality improvement and cost optimization initiatives.
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
    QUERY_MEDICATION_ADHERENCE,
    QUERY_MEDICATION_ERRORS,
    QUERY_TOP_MEDICATIONS
)

st.set_page_config(page_title="Medication Analytics", layout="wide")

st.title("Medication Analytics Dashboard")
st.markdown("Medication administration tracking, adherence, and safety metrics")

# KPI Cards
st.subheader("Medication Administration Overview (Historical Data)")

try:
    adherence_data = query_to_df(QUERY_MEDICATION_ADHERENCE)
    
    if not adherence_data.empty:
        total_doses = adherence_data['total_doses'].sum()
        doses_given = adherence_data['doses_given'].sum()
        overall_adherence = (doses_given / total_doses * 100) if total_doses > 0 else 0
        doses_missed = total_doses - doses_given
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Scheduled Doses", f"{total_doses:,}")
        
        with col2:
            st.metric("Doses Administered", f"{doses_given:,}")
        
        with col3:
            st.metric("Overall Adherence Rate", f"{overall_adherence:.1f}%", 
                     delta=f"{overall_adherence - 95:.1f}% vs target" if overall_adherence else None,
                     delta_color="normal")
        
        with col4:
            st.metric("Doses Not Given", f"{doses_missed:,}")
    else:
        st.info("No medication data available for the selected period")

except Exception as e:
    st.error(f"Error loading medication KPIs: {e}")

st.markdown("---")

# Adherence by Ward
col1, col2 = st.columns(2)

with col1:
    st.subheader("Medication Adherence by Ward")
    
    try:
        adherence_data = query_to_df(QUERY_MEDICATION_ADHERENCE)
        
        if not adherence_data.empty:
            fig = px.bar(
                adherence_data.sort_values('adherence_rate'),
                x='adherence_rate',
                y='ward_name',
                orientation='h',
                title='Adherence Rate by Ward (%)',
                labels={'adherence_rate': 'Adherence %', 'ward_name': 'Ward'},
                color='adherence_rate',
                color_continuous_scale='RdYlGn',
                range_color=[80, 100]
            )
            fig.add_vline(x=95, line_dash="dash", line_color="red", annotation_text="Target: 95%")
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            # Data table
            display_df = adherence_data[['ward_name', 'total_doses', 'doses_given', 'adherence_rate']].copy()
            display_df.columns = ['Ward', 'Scheduled', 'Given', 'Adherence %']
            display_df = display_df.sort_values('Adherence %')
            
            st.dataframe(display_df, hide_index=True, use_container_width=True)
        else:
            st.info("No adherence data available")
    
    except Exception as e:
        st.error(f"Error loading adherence data: {e}")

with col2:
    st.subheader("Medication Administration Issues")
    
    try:
        errors = query_to_df(QUERY_MEDICATION_ERRORS)
        
        if not errors.empty:
            # Pie chart of error types
            fig = px.pie(
                errors,
                names='status',
                values='count',
                title='Distribution of Non-Administered Doses',
                color_discrete_map={
                    'Missed': '#ff6b6b',
                    'Refused': '#feca57',
                    'Held': '#48dbfb'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Bar chart by ward
            fig2 = px.bar(
                errors,
                x='ward_name',
                y='count',
                color='status',
                title='Issues by Ward',
                labels={'count': 'Count', 'ward_name': 'Ward'},
                barmode='stack'
            )
            fig2.update_xaxes(tickangle=45)
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No medication issues recorded")
    
    except Exception as e:
        st.error(f"Error loading medication errors: {e}")

st.markdown("---")

# Top Medications
st.subheader("Most Administered Medications (Last 90 Days of Data)")

try:
    top_meds = query_to_df(QUERY_TOP_MEDICATIONS)
    
    if not top_meds.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.bar(
                top_meds.head(15),
                x='administration_count',
                y='drug_name',
                orientation='h',
                title='Top 15 Medications by Administration Count',
                labels={'administration_count': 'Number of Doses', 'drug_name': 'Medication'},
                color='drug_class',
                hover_data=['drug_class', 'total_cost']
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            # Cost analysis
            st.markdown("**Cost Analysis**")
            
            total_cost = top_meds['total_cost'].sum()
            st.metric("Total Medication Cost", f"${total_cost:,.2f}")
            
            # Top cost drivers
            st.markdown("**Most Expensive Medications**")
            cost_df = top_meds.nlargest(10, 'total_cost')[['drug_name', 'total_cost']].copy()
            cost_df['total_cost'] = cost_df['total_cost'].apply(lambda x: f"${x:,.2f}")
            cost_df.columns = ['Medication', 'Total Cost']
            st.dataframe(cost_df, hide_index=True, use_container_width=True)
        
        # Drug class distribution
        st.markdown("### Administration by Drug Class")
        class_summary = top_meds.groupby('drug_class').agg({
            'administration_count': 'sum',
            'total_cost': 'sum'
        }).reset_index().sort_values('administration_count', descending=True)
        
        fig3 = px.treemap(
            class_summary,
            path=['drug_class'],
            values='administration_count',
            title='Medication Volume by Drug Class',
            color='total_cost',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("No medication data available")

except Exception as e:
    st.error(f"Error loading top medications: {e}")

# Timing Analysis
st.markdown("---")
st.subheader("Medication Administration Timing Analysis")

try:
    timing_query = """
    SELECT 
        EXTRACT(HOUR FROM scheduled_datetime) as hour,
        COUNT(*) as scheduled_count,
        SUM(CASE WHEN status = 'Given' THEN 1 ELSE 0 END) as given_count
    FROM fact_medication_administration
    WHERE scheduled_datetime >= (SELECT MAX(scheduled_datetime) FROM fact_medication_administration) - INTERVAL '30 days'
    GROUP BY EXTRACT(HOUR FROM scheduled_datetime)
    ORDER BY hour
    """
    
    timing = query_to_df(timing_query)
    
    if not timing.empty:
        timing['on_time_rate'] = (timing['given_count'] / timing['scheduled_count'] * 100).round(1)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=timing['hour'],
            y=timing['scheduled_count'],
            name='Scheduled',
            marker_color='lightblue'
        ))
        fig.add_trace(go.Bar(
            x=timing['hour'],
            y=timing['given_count'],
            name='Administered',
            marker_color='darkblue'
        ))
        
        fig.update_layout(
            title='Medication Administration by Hour of Day',
            xaxis_title='Hour (24-hour format)',
            yaxis_title='Number of Doses',
            barmode='group',
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Peak hours
        peak_hour = timing.loc[timing['scheduled_count'].idxmax(), 'hour']
        st.info(f"**Peak medication administration hour:** {int(peak_hour)}:00 with {timing['scheduled_count'].max()} scheduled doses")
    
except Exception as e:
    st.error(f"Error loading timing analysis: {e}")

# Safety Alerts
st.markdown("---")
st.subheader("Safety Alerts & Recommendations")

try:
    adherence_data = query_to_df(QUERY_MEDICATION_ADHERENCE)
    
    if not adherence_data.empty:
        low_adherence_wards = adherence_data[adherence_data['adherence_rate'] < 95]
        
        if not low_adherence_wards.empty:
            st.warning("**Wards Below Target Adherence (95%):**")
            for _, ward in low_adherence_wards.iterrows():
                st.write(f"- **{ward['ward_name']}**: {ward['adherence_rate']:.1f}% adherence")
        else:
            st.success("All wards meeting adherence targets (>95%)")
    
    # Check for high error rates
    errors = query_to_df(QUERY_MEDICATION_ERRORS)
    if not errors.empty:
        high_error_wards = errors.groupby('ward_name')['count'].sum().reset_index()
        high_error_wards = high_error_wards[high_error_wards['count'] > 20]
        
        if not high_error_wards.empty:
            st.error("**Wards with High Error Counts (>20 issues):**")
            for _, ward in high_error_wards.iterrows():
                st.write(f"- **{ward['ward_name']}**: {ward['count']} issues")

except Exception as e:
    pass

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

