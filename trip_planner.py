import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIG ---
st.set_page_config(page_title="Wanderlust Planner", layout="wide", page_icon="✈️")

# --- CUSTOM THEME (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;700&display=swap');

    html, body, [class*="css"]  {
        font-family: 'Montserrat', sans-serif;
    }

    /* Background Gradient */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(255, 255, 255, 0.8);
        border-right: 1px solid #e0e0e0;
    }

    /* Card Styling */
    .trip-card {
        background: rgba(255, 255, 255, 0.7);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 15px;
        margin-bottom: 15px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
        transition: transform 0.2s ease;
    }
    
    .trip-card:hover {
        transform: translateY(-3px);
    }

    /* Metric Box */
    [data-testid="stMetricValue"] {
        color: #1E3A8A;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'trip_data' not in st.session_state:
    st.session_state.trip_data = []

# --- SIDEBAR ---
with st.sidebar:
    st.title("✈️ Trip Controls")
    trip_name = st.text_input("Trip Name", value="Italy Coastline 2026")
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", datetime.now())
    end_date = col2.date_input("End", datetime.now() + timedelta(days=5))
    
    st.markdown("### 👥 Travelers")
    p1_name = st.text_input("Traveler 1", value="Alice")
    p1_color = st.color_picker(f"Color for {p1_name}", "#FFDEDE")
    
    p2_name = st.text_input("Traveler 2", value="Bob")
    p2_color = st.color_picker(f"Color for {p2_name}", "#DEEDFF")
    
    shared_color = st.color_picker("Shared Activity Color", "#E2FFDE")
    
    st.divider()
    
    # Save/Load
    st.subheader("💾 Plan Management")
    trip_json = json.dumps(st.session_state.trip_data, indent=4)
    st.download_button("📥 Save Plan to Computer", data=trip_json, file_name="trip_plan.json", use_container_width=True)
    
    uploaded_file = st.file_uploader("📂 Import Previous Plan", type="json")
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)
    
    if st.button("🗑️ Reset All Data", use_container_width=True):
        st.session_state.trip_data = []
        st.rerun()

# --- HEADER ---
st.markdown(f"<h1 style='text-align: center; color: #1E3A8A;'>🌍 {trip_name}</h1>", unsafe_allow_html=True)

# Calculations
df = pd.DataFrame(st.session_state.trip_data)
total_cost = df['cost'].sum() if not df.empty else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Total Investment", f"${total_cost:,.2f}")
m2.metric("Days Away", (end_date - start_date).days + 1)
m3.metric("Planned Stops", len(st.session_state.trip_data))

st.divider()

# --- ADD ACTIVITY ---
with st.expander("✨ Add a New Memory", expanded=False):
    with st.form("activity_form", clear_on_submit=True):
        f1, f2 = st.columns([2, 1])
        with f1:
            act_name = st.text_input("What are we doing?")
            act_date = st.date_input("When?", min_value=start_date, max_value=end_date)
        with f2:
            act_cost = st.number_input("Cost ($)", min_value=0.0)
            act_status = st.selectbox("Current Status", ["Planned", "Planned but not booked", "Needs Review"])
            
        act_people = st.multiselect("Who's going?", [p1_name, p2_name], default=[p1_name, p2_name])
        
        if st.form_submit_button("Add Activity to Itinerary", use_container_width=True):
            if act_name:
                st.session_state.trip_data.append({
                    "date": str(act_date),
                    "activity": act_name,
                    "people": act_people,
                    "status": act_status,
                    "cost": act_cost
                })
                st.rerun()

# --- ITINERARY ---
status_colors = {
    "Planned": "#2ecc71",              # Green
    "Planned but not booked": "#f1c40f", # Yellow
    "Needs Review": "#e74c3c"           # Red
}

date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    day_plans = [i for i in st.session_state.trip_data if i['date'] == date_str]
    
    st.markdown(f"### 🗓️ {d.strftime('%A, %b %d')}")
    
    if not day_plans:
        st.markdown("<p style='color: #666;'>Relaxation day... no plans yet!</p>", unsafe_allow_html=True)
    else:
        for item in day_plans:
            # Logic for background color
            if p1_name in item['people'] and p2_name in item['people']:
                card_bg = shared_color
            elif p1_name in item['people']:
                card_bg = p1_color
            else:
                card_bg = p2_color
                
            border_color = status_colors.get(item['status'], "#333")
            
            # Rendering the beautiful card
            st.markdown(f"""
                <div class="trip-card" style="border-left: 10px solid {border_color}; background-color: {card_bg};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.25rem; font-weight: 700; color: #2C3E50;">{item['activity']}</span>
                        <span style="font-size: 0.85rem; font-weight: bold; color: white; background: {border_color}; padding: 4px 12px; border-radius: 50px;">
                            {item['status'].upper()}
                        </span>
                    </div>
                    <div style="margin-top: 12px; display: flex; gap: 20px; font-size: 0.9rem; color: #34495E;">
                        <span>👤 <b>{", ".join(item['people'])}</b></span>
                        <span>💰 <b>${item['cost']:,.2f}</b></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
