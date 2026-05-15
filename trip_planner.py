import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIG & SESSION STATE ---
st.set_page_config(page_title="Duo Trip Planner", layout="wide")

if 'trip_data' not in st.session_state:
    st.session_state.trip_data = []

# --- HELPERS ---
def save_plan():
    return json.dumps(st.session_state.trip_data, indent=4)

def load_plan(uploaded_file):
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)

# --- SIDEBAR: TRIP SETTINGS ---
with st.sidebar:
    st.header("🌍 Trip Settings")
    trip_name = st.text_input("Trip Name", value="Summer Adventure 2026")
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", datetime.now())
    end_date = col2.date_input("End Date", datetime.now() + timedelta(days=5))
    
    person_a = st.text_input("Person 1 Name", value="Explorer A")
    person_b = st.text_input("Person 2 Name", value="Explorer B")
    
    st.divider()
    
    # Save/Load Functionality
    st.subheader("💾 Save & Load")
    st.download_button(
        label="Download Trip Plan (JSON)",
        data=save_plan(),
        file_name=f"{trip_name.replace(' ', '_')}.json",
        mime="application/json"
    )
    
    uploaded_file = st.file_uploader("Upload existing plan", type="json")
    if uploaded_file:
        load_plan(uploaded_file)

# --- CALCULATE TOTALS ---
df_display = pd.DataFrame(st.session_state.trip_data)
total_cost = 0
if not df_display.empty:
    total_cost = df_display['cost'].sum()

# --- MAIN INTERFACE ---
st.title(f"📍 {trip_name}")

# High-level Metrics
m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Activities", len(st.session_state.trip_data))

st.divider()

# --- ADD ACTIVITY SECTION ---
with st.expander("➕ Add New Activity", expanded=True):
    with st.form("activity_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        
        with f_col1:
            act_name = st.text_input("Activity/Location Name")
            act_date = st.date_input("Date", min_value=start_date, max_value=end_date)
        
        with f_col2:
            act_person = st.multiselect("Who is doing this?", [person_a, person_b], default=[person_a, person_b])
            act_status = st.selectbox("Status", ["Planned", "Planned but not booked", "Needs Review"])
        
        with f_col3:
            act_cost = st.number_input("Cost ($)", min_value=0.0, step=10.0)
            submit = st.form_submit_button("Add to Itinerary")
            
        if submit:
            if not act_name:
                st.error("Please enter an activity name.")
            else:
                new_entry = {
                    "date": str(act_date),
                    "activity": act_name,
                    "people": act_person,
                    "status": act_status,
                    "cost": act_cost
                }
                st.session_state.trip_data.append(new_entry)
                st.rerun()

# --- ITINERARY VIEW ---
st.subheader("🗓️ Your Daily Schedule")

# Generate range of dates
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    st.markdown(f"### {d.strftime('%A, %b %d')}")
    
    # Filter data for this day
    day_activities = [item for item in st.session_state.trip_data if item['date'] == date_str]
    
    if not day_activities:
        st.info("No activities planned for this day.")
    else:
        for idx, item in enumerate(day_activities):
            # Color coding based on person/overlap
            bg_color = "#f0f2f6" # Default
            if person_a in item['people'] and person_b in item['people']:
                bg_color = "#e1f5fe" # Overlap (Light Blue)
            elif person_a in item['people']:
                bg_color = "#fff9c4" # Person A (Light Yellow)
            elif person_b in item['people']:
                bg_color = "#f8bbd0" # Person B (Light Pink)
            
            # Status badge color
            status_map = {
                "Planned": "🟢",
                "Planned but not booked": "🟡",
                "Needs Review": "🔴"
            }
            
            with st.container():
                st.markdown(
                    f"""
                    <div style="background-color:{bg_color}; padding:15px; border-radius:10px; margin-bottom:10px; border-left: 5px solid #333;">
                        <div style="display: flex; justify-content: space-between;">
                            <span style="font-weight: bold; font-size: 1.1rem;">{item['activity']}</span>
                            <span>{status_map.get(item['status'], '')} {item['status']}</span>
                        </div>
                        <div style="color: #555; font-size: 0.9rem;">
                            👤 <b>Who:</b> {", ".join(item['people'])} | 💰 <b>Cost:</b> ${item['cost']:,.2f}
                        </div>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

# --- CLEAR ALL ---
if st.sidebar.button("Clear All Data"):
    st.session_state.trip_data = []
    st.rerun()
