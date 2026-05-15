import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIG & SESSION STATE ---
st.set_page_config(page_title="Custom Trip Planner", layout="wide")

if 'trip_data' not in st.session_state:
    st.session_state.trip_data = []

# --- SIDEBAR: SETTINGS & CUSTOMIZATION ---
with st.sidebar:
    st.header("🎨 Trip Customization")
    trip_name = st.text_input("Trip Name", value="Grand Voyage 2026")
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start Date", datetime.now())
    end_date = col2.date_input("End Date", datetime.now() + timedelta(days=5))
    
    st.divider()
    
    # Traveler 1 Setup
    p1_name = st.text_input("Traveler 1 Name", value="Explorer A")
    p1_color = st.color_picker(f"Color for {p1_name}", "#E1F5FE")
    
    # Traveler 2 Setup
    p2_name = st.text_input("Traveler 2 Name", value="Explorer B")
    p2_color = st.color_picker(f"Color for {p2_name}", "#F8BBD0")
    
    # Shared Color Setup
    shared_color = st.color_picker("Color for Shared Activities", "#F3E5F5")
    
    st.divider()
    
    # Save/Load
    st.subheader("💾 Data Management")
    trip_json = json.dumps(st.session_state.trip_data, indent=4)
    st.download_button(
        label="Download Plan (JSON)",
        data=trip_json,
        file_name=f"{trip_name.replace(' ', '_')}.json",
        mime="application/json"
    )
    
    uploaded_file = st.file_uploader("Upload existing plan", type="json")
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)
    
    if st.button("Clear All Data"):
        st.session_state.trip_data = []
        st.rerun()

# --- LOGIC & CALCULATIONS ---
df_display = pd.DataFrame(st.session_state.trip_data)
total_cost = df_display['cost'].sum() if not df_display.empty else 0.0

# --- HEADER SECTION ---
st.title(f"📍 {trip_name}")
m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Activities", len(st.session_state.trip_data))

st.divider()

# --- ADD ACTIVITY FORM ---
with st.expander("➕ Add New Activity / Route", expanded=False):
    with st.form("activity_form", clear_on_submit=True):
        f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
        
        with f_col1:
            act_name = st.text_input("Activity/Location Name")
            act_date = st.date_input("Date", min_value=start_date, max_value=end_date)
        
        with f_col2:
            act_person = st.multiselect("Assign To", [p1_name, p2_name], default=[p1_name, p2_name])
            act_status = st.selectbox("Status", ["Planned", "Planned but not booked", "Needs Review"])
        
        with f_col3:
            act_cost = st.number_input("Cost ($)", min_value=0.0, step=10.0)
            submit = st.form_submit_button("Add to Itinerary", use_container_width=True)
            
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

# --- ITINERARY DISPLAY ---
st.subheader("🗓️ Your Schedule")

# Status Color Map for the Left Border
status_colors = {
    "Planned": "#28a745",              # Green
    "Planned but not booked": "#ffaa00", # Yellow/Orange
    "Needs Review": "#ff4b4b"           # Red
}

date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    day_activities = [item for item in st.session_state.trip_data if item['date'] == date_str]
    
    st.markdown(f"#### {d.strftime('%A, %b %d')}")
    
    if not day_activities:
        st.caption("No plans yet.")
    else:
        for item in day_activities:
            # Determine Background Color based on people
            if p1_name in item['people'] and p2_name in item['people']:
                bg_color = shared_color
            elif p1_name in item['people']:
                bg_color = p1_color
            elif p2_name in item['people']:
                bg_color = p2_color
            else:
                bg_color = "#f0f2f6"
            
            # Determine Left Border Color based on status
            border_color = status_colors.get(item['status'], "#333")
            
            # HTML Injection for the "Prettier" Card
            st.markdown(
                f"""
                <div style="
                    background-color: {bg_color}; 
                    padding: 18px; 
                    border-radius: 12px; 
                    margin-bottom: 12px; 
                    border-left: 8px solid {border_color};
                    box-shadow: 2px 4px 6px rgba(0,0,0,0.05);
                    color: #111;
                ">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.2rem; font-weight: 700;">{item['activity']}</span>
                        <span style="
                            background: rgba(255,255,255,0.6); 
                            padding: 2px 10px; 
                            border-radius: 20px; 
                            font-size: 0.8rem; 
                            font-weight: bold;
                            border: 1px solid {border_color};
                        ">
                            {item['status'].upper()}
                        </span>
                    </div>
                    <div style="margin-top: 10px; font-size: 0.95rem;">
                        👤 <b>Assignee:</b> {", ".join(item['people'])} 
                        <span style="margin: 0 15px;">|</span>
                        💰 <b>Cost:</b> ${item['cost']:,.2f}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
