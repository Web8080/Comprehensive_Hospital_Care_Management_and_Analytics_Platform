"""
Patient Care Plan Dashboard - Comprehensive Individual Patient Management

Author: Victor Ibhafidon
Description: Clinical dashboard for bedside nurses and physicians providing 360-degree patient view.
             Features medication administration record (MAR), vital signs trending, daily activity logging
             with comments, lab results, procedures, care goals, and 5-year admission history.
             Core feature: Daily Activity Log with nursing comments for care documentation.
Pipeline Role: Primary clinical interface querying GOLD layer patient-specific fact tables.
              Supports real-time care documentation and historical analysis.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, date

sys.path.append(str(Path(__file__).parent.parent.parent))

from streamlit_app.utils.database import query_to_df
from streamlit_app.utils.queries import *

st.set_page_config(page_title="Patient Care Plan", layout="wide")

st.title("Patient Care Plan Dashboard")
st.markdown("Comprehensive patient care tracking and management")

# Patient Search
st.subheader("Find Patient")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    search_term = st.text_input("Search by MRN, Name, or Ward", placeholder="Enter patient MRN or name...")

with col2:
    st.markdown("<br>", unsafe_allow_html=True)
    search_button = st.button("Search", type="primary", use_container_width=True)

with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    clear_button = st.button("Clear", use_container_width=True)

if clear_button:
    st.session_state.selected_patient = None
    st.experimental_rerun()

# Search and display patients
if search_button and search_term:
    try:
        search_pattern = f"%{search_term}%"
        patients = query_to_df(QUERY_SEARCH_PATIENTS, (search_pattern, search_pattern, search_pattern))
        
        if not patients.empty:
            st.success(f"Found {len(patients)} patient(s)")
            
            # Display search results
            for idx, patient in patients.iterrows():
                col_info, col_action = st.columns([4, 1])
                
                with col_info:
                    age = (datetime.now().date() - patient['date_of_birth']).days // 365
                    st.write(f"**{patient['patient_name']}** | MRN: {patient['mrn']} | Age: {age} | {patient['gender']} | Blood Type: {patient['blood_type']}")
                    st.caption(f"Ward: {patient['ward_name']} | Bed: {patient['bed_number']} | Admitted: {patient['admission_date']} | Dx: {patient['diagnosis_name']}")
                
                with col_action:
                    if st.button(f"View", key=f"view_{patient['patient_id']}"):
                        st.session_state.selected_patient = patient['patient_id']
                        st.session_state.selected_admission = patient['admission_id']
                        st.experimental_rerun()
                
                st.markdown("---")
        else:
            st.warning("No patients found matching your search criteria")
    
    except Exception as e:
        st.error(f"Error searching patients: {e}")

# Display selected patient details
if 'selected_patient' in st.session_state and st.session_state.selected_patient:
    try:
        patient_id = st.session_state.selected_patient
        admission_id = st.session_state.selected_admission
        
        # Get patient details
        patient = query_to_df(QUERY_PATIENT_DETAILS, (patient_id,))
        
        if not patient.empty:
            p = patient.iloc[0]
            
            # Patient Header Card
            st.markdown("### Current Admission")
            
            header_col1, header_col2, header_col3, header_col4 = st.columns(4)
            
            with header_col1:
                age = (datetime.now().date() - p['date_of_birth']).days // 365
                st.metric("Patient", f"{p['first_name']} {p['last_name']}")
                st.caption(f"MRN: {p['mrn']} | Age: {age} | {p['gender']}")
            
            with header_col2:
                st.metric("Location", p['ward_name'])
                st.caption(f"Bed: {p['bed_number']} | Dept: {p['department']}")
            
            with header_col3:
                st.metric("Primary Diagnosis", p['severity_level'])
                st.caption(p['diagnosis_name'])
            
            with header_col4:
                los = (datetime.now().date() - p['admission_date']).days
                st.metric("Length of Stay", f"{los} days")
                st.caption(f"Admitted: {p['admission_date']}")
            
            st.markdown("---")
            
            # Tabs for different sections
            tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
                "Care Goals",
                "Medication (MAR)",
                "Vital Signs",
                "Daily Activities",
                "Lab Results",
                "Procedures",
                "History"
            ])
            
            # Tab 1: Care Goals
            with tab1:
                st.subheader("Active Care Plan Goals")
                
                goals = query_to_df(QUERY_PATIENT_CARE_GOALS, (admission_id,))
                
                if not goals.empty:
                    for _, goal in goals.iterrows():
                        with st.container():
                            col_goal, col_progress = st.columns([3, 1])
                            
                            with col_goal:
                                st.write(f"**{goal['goal_type']}**")
                                st.write(goal['goal_description'])
                                st.caption(f"Target: {goal['target_date']} | Status: {goal['status']}")
                            
                            with col_progress:
                                st.progress(goal['progress_pct'] / 100)
                                st.caption(f"{goal['progress_pct']}% Complete")
                            
                            st.markdown("---")
                else:
                    st.info("No active care goals")
            
            # Tab 2: Medication Administration Record (MAR)
            with tab2:
                st.subheader("Medication Administration Record (Last 72 Hours)")
                
                meds = query_to_df(QUERY_PATIENT_MEDICATIONS, (admission_id,))
                
                if not meds.empty:
                    # Format for display
                    meds['scheduled_datetime'] = pd.to_datetime(meds['scheduled_datetime'])
                    meds['date'] = meds['scheduled_datetime'].dt.strftime('%Y-%m-%d')
                    meds['time'] = meds['scheduled_datetime'].dt.strftime('%H:%M')
                    
                    # Group by medication
                    unique_meds = meds['drug_name'].unique()
                    
                    for med_name in unique_meds:
                        with st.expander(f"**{med_name}**", expanded=True):
                            med_df = meds[meds['drug_name'] == med_name].copy()
                            
                            # Display as table
                            display_df = med_df[['date', 'time', 'dosage', 'route', 'status', 'administered_by']].copy()
                            display_df.columns = ['Date', 'Time', 'Dose', 'Route', 'Status', 'Given By']
                            
                            # Color code status
                            def color_status(val):
                                if val == 'Given':
                                    return 'background-color: #d4edda'
                                elif val == 'Missed':
                                    return 'background-color: #f8d7da'
                                elif val == 'Refused':
                                    return 'background-color: #fff3cd'
                                elif val == 'Held':
                                    return 'background-color: #d1ecf1'
                                return ''
                            
                            st.dataframe(
                                display_df.style.applymap(color_status, subset=['Status']),
                                hide_index=True,
                                use_container_width=True
                            )
                else:
                    st.info("No recent medication records")
            
            # Tab 3: Vital Signs
            with tab3:
                st.subheader("Vital Signs Trends (Last 72 Hours)")
                
                vitals = query_to_df(QUERY_PATIENT_VITALS, (admission_id,))
                
                if not vitals.empty:
                    vitals['recorded_datetime'] = pd.to_datetime(vitals['recorded_datetime'])
                    vitals = vitals.sort_values('recorded_datetime')
                    
                    # Create charts
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=vitals['recorded_datetime'],
                            y=vitals['blood_pressure_systolic'],
                            name='Systolic',
                            line=dict(color='red')
                        ))
                        fig.add_trace(go.Scatter(
                            x=vitals['recorded_datetime'],
                            y=vitals['blood_pressure_diastolic'],
                            name='Diastolic',
                            line=dict(color='blue')
                        ))
                        fig.update_layout(title='Blood Pressure', yaxis_title='mmHg', height=300)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        fig2 = px.line(
                            vitals,
                            x='recorded_datetime',
                            y='heart_rate',
                            title='Heart Rate',
                            labels={'heart_rate': 'BPM'}
                        )
                        fig2.update_layout(height=300)
                        st.plotly_chart(fig2, use_container_width=True)
                    
                    with col2:
                        fig3 = px.line(
                            vitals,
                            x='recorded_datetime',
                            y='temperature',
                            title='Temperature',
                            labels={'temperature': 'Celsius'}
                        )
                        fig3.update_layout(height=300)
                        st.plotly_chart(fig3, use_container_width=True)
                        
                        fig4 = px.line(
                            vitals,
                            x='recorded_datetime',
                            y='oxygen_saturation',
                            title='Oxygen Saturation',
                            labels={'oxygen_saturation': 'SpO2 %'}
                        )
                        fig4.update_layout(height=300)
                        st.plotly_chart(fig4, use_container_width=True)
                else:
                    st.info("No vital signs data available")
            
            # Tab 4: Daily Activities (THE STAR FEATURE with Comments)
            with tab4:
                st.subheader("Daily Activity Log (Activities of Daily Living)")
                
                # Activity Input Form
                with st.expander("**Log New Daily Activity**", expanded=False):
                    st.write("Enter today's activity information:")
                    
                    form_col1, form_col2 = st.columns(2)
                    
                    with form_col1:
                        activity_date = st.date_input("Date", value=date.today())
                        mobility_score = st.select_slider(
                            "Mobility",
                            options=[1, 2, 3, 4, 5],
                            value=3,
                            format_func=lambda x: {
                                1: "1 - Bedbound",
                                2: "2 - Chair only",
                                3: "3 - Walk with assistance",
                                4: "4 - Walk with device",
                                5: "5 - Independent"
                            }[x]
                        )
                        mobility_notes = st.text_input("Mobility Notes", placeholder="e.g., Walked to chair (assisted)")
                        
                        self_care_score = st.select_slider(
                            "Self-Care",
                            options=[1, 2, 3, 4, 5],
                            value=3,
                            format_func=lambda x: {
                                1: "1 - Total assistance",
                                2: "2 - Extensive help",
                                3: "3 - Moderate help",
                                4: "4 - Minimal help",
                                5: "5 - Independent"
                            }[x]
                        )
                        
                        st.markdown("**Meals Consumed (%)**")
                        breakfast = st.slider("Breakfast", 0, 100, 75, step=25)
                        lunch = st.slider("Lunch", 0, 100, 50, step=25)
                        dinner = st.slider("Dinner", 0, 100, 75, step=25)
                    
                    with form_col2:
                        mental_status = st.selectbox("Mental Status", ["Alert", "Confused", "Lethargic", "Agitated"])
                        mood = st.selectbox("Mood", ["Cooperative", "Anxious", "Depressed", "Irritable"])
                        
                        pain_level = st.slider("Pain Level (0-10)", 0, 10, 3)
                        pain_location = st.text_input("Pain Location", placeholder="e.g., Abdomen, Hip, etc.")
                        
                        bathroom_independence = st.checkbox("Bathroom Independence", value=True)
                        output_notes = st.text_input("Output Notes", placeholder="e.g., Urination normal, No BM")
                        
                        sleep_quality = st.slider("Sleep Quality (1-5)", 1, 5, 3)
                        sleep_hours = st.number_input("Sleep Hours", min_value=0.0, max_value=24.0, value=7.0, step=0.5)
                    
                    # COMMENTS SECTION (As requested by user)
                    comments = st.text_area(
                        "Nursing Comments/Observations",
                        placeholder="Enter any additional observations, concerns, or notes about the patient...",
                        height=100,
                        help="Free-text field for detailed nursing observations"
                    )
                    
                    if st.button("Save Daily Activity", type="primary"):
                        # In a real app, this would INSERT into the database
                        st.success("Daily activity logged successfully!")
                        st.info("Note: This is a demo - actual database INSERT would happen here")
                
                st.markdown("---")
                
                # Display historical daily activities
                st.write("**Recent Activity History (Last 7 Days)**")
                
                activities = query_to_df(QUERY_PATIENT_DAILY_ACTIVITIES, (admission_id,))
                
                if not activities.empty:
                    for _, activity in activities.iterrows():
                        with st.container():
                            st.markdown(f"### {activity['activity_date']}")
                            
                            col1, col2, col3, col4 = st.columns(4)
                            
                            with col1:
                                st.metric("Mobility", f"{activity['mobility_score']}/5")
                                st.caption(activity['mobility_notes'] if pd.notna(activity['mobility_notes']) else "")
                            
                            with col2:
                                st.metric("Self-Care", f"{activity['self_care_score']}/5")
                                avg_meal = (activity['breakfast_percent_consumed'] + activity['lunch_percent_consumed'] + activity['dinner_percent_consumed']) / 3
                                st.caption(f"Meals: {avg_meal:.0f}% avg")
                            
                            with col3:
                                st.metric("Mental Status", activity['mental_status'])
                                st.caption(f"Mood: {activity['mood']}")
                            
                            with col4:
                                st.metric("Pain Level", f"{activity['pain_level']}/10")
                                st.caption(f"Sleep: {activity['sleep_quality']}/5 quality")
                            
                            # Display comments if present
                            if pd.notna(activity['comments']) and activity['comments']:
                                st.info(f"**Comments:** {activity['comments']}")
                            
                            st.caption(f"Recorded by: {activity['recorded_by']}")
                            st.markdown("---")
                else:
                    st.info("No daily activity records yet")
            
            # Tab 5: Lab Results
            with tab5:
                st.subheader("Recent Lab Results")
                
                labs = query_to_df(QUERY_PATIENT_LABS, (admission_id,))
                
                if not labs.empty:
                    labs['collected_datetime'] = pd.to_datetime(labs['collected_datetime'])
                    
                    # Display by test type
                    test_types = labs['test_type'].unique()
                    
                    for test_type in test_types:
                        with st.expander(f"**{test_type}**", expanded=True):
                            test_df = labs[labs['test_type'] == test_type].copy()
                            
                            display_df = test_df[['test_name', 'test_value', 'unit_of_measure', 'reference_range', 'abnormal_flag', 'collected_datetime']].copy()
                            display_df.columns = ['Test', 'Value', 'Unit', 'Reference Range', 'Flag', 'Date']
                            display_df['Date'] = display_df['Date'].dt.strftime('%Y-%m-%d %H:%M')
                            
                            # Highlight abnormal results
                            def highlight_abnormal(val):
                                if val == 'Critical':
                                    return 'background-color: #f8d7da; font-weight: bold'
                                elif val in ['High', 'Low']:
                                    return 'background-color: #fff3cd'
                                return ''
                            
                            st.dataframe(
                                display_df.style.applymap(highlight_abnormal, subset=['Flag']),
                                hide_index=True,
                                use_container_width=True
                            )
                else:
                    st.info("No lab results available")
            
            # Tab 6: Procedures
            with tab6:
                st.subheader("Procedures Performed")
                
                procedures = query_to_df(QUERY_PATIENT_PROCEDURES, (admission_id,))
                
                if not procedures.empty:
                    for _, proc in procedures.iterrows():
                        with st.container():
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.write(f"**{proc['procedure_name']}** ({proc['procedure_type']})")
                                st.caption(f"Scheduled: {proc['scheduled_datetime']} | Actual: {proc['actual_datetime']}")
                                st.caption(f"Duration: {proc['duration_minutes']} minutes | Outcome: {proc['outcome']}")
                                if pd.notna(proc['notes']):
                                    st.info(proc['notes'])
                            
                            with col2:
                                st.caption(f"Performed by:\n{proc['performed_by']}")
                            
                            st.markdown("---")
                else:
                    st.info("No procedures recorded")
            
            # Tab 7: Historical Admissions
            with tab7:
                st.subheader("Previous Admissions (5-Year History)")
                
                history = query_to_df(QUERY_PATIENT_HISTORY, (patient_id,))
                
                if not history.empty:
                    st.write(f"**{len(history)} previous admissions**")
                    
                    display_df = history.copy()
                    display_df.columns = ['Admission Date', 'Discharge Date', 'LOS (days)', 'Admission Type', 'Ward', 'Diagnosis', 'Disposition']
                    
                    st.dataframe(
                        display_df,
                        hide_index=True,
                        use_container_width=True
                    )
                else:
                    st.info("No previous admissions on record")
    
    except Exception as e:
        st.error(f"Error loading patient details: {e}")
        import traceback
        st.code(traceback.format_exc())

else:
    st.info("Search for a patient above to view their care plan")

st.markdown("---")
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

