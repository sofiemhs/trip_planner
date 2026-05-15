import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIG ---
st.set_page_config(page_title="Jungle Trip Planner", layout="wide", page_icon="🌿")

# --- JUNGLE THEME (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');

    /* Global Font & Jungle Background */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        color: #1B2E1D;
    }

    .stApp {
        background: linear-gradient(135deg, #0B2010 0%, #1E3D24 100%);
    }

    /* Sidebar - Earthy Look */
    [data-testid="stSidebar"] {
        background-color: #F5F5DC !important;
        border-right: 2px solid #3D5A45;
    }

    /* Activity Cards - High Readability */
    .jungle-card {
        background-color: #FFFFFF; /* Pure white/cream for max contrast */
        padding: 22px;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        color: #1B2E1D !important; /* Dark Jungle Green Text */
    }
    
    .jungle-card b, .jungle-card span {
        color: #1B2E1D !important;
    }

    /* Header Styling */
    h1, h2, h3, h4 {
        color: #E9F5DB !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }

    /* Input Form Styling */
    .stForm {
        background-color: rgba(255, 255, 255, 0.9);
        border-radius: 15px;
        padding: 20px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        color: #B5E48C !important;
    }
    [data-testid="stMetricLabel"] {
        color: #FFFFFF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- SESSION STATE ---
if 'trip_data' not in st.session_state:
    st.session_state.trip_data = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color:#2D4739 !important;'>🌴 Expedition Setup</h1>", unsafe_allow_html=True)
    trip_name = st.text_input("Trip Name", value="Amazon Expedition 2026")
    
    col1, col2 = st.columns(2)
    start_date = col1.date_input("Start", datetime.now())
    end_date = col2.date_input("End", datetime.now() + timedelta(days=7))
    
    st.divider()
    
    st.markdown("### 🐾 Explorer Colors")
    p1_name = st.text_input("Explorer 1", value="Tarzan")
    p1_color = st.color_picker(f"Color for {p1_name}", "#D4E9D7") # Pale Mint
    
    p2_name = st.text_input("Explorer 2", value="Jane")
    p2_color = st.color_picker(f"Color for {p2_name}", "#FFE8D6") # Sandy Peach
    
    shared_color = st.color_picker("Both Together", "#FFF9C4") # Sunbeam Yellow
    
    st.divider()
    
    # Save/Load
    st.subheader("💾 Field Notes")
    trip_json = json.dumps(st.session_state.trip_data, indent=4)
    st.download_button("💾 Save to Device", data=trip_json, file_name="jungle_plan.json", use_container_width=True)
    
    uploaded_file = st.file_uploader("📂 Import Plan", type="json")
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)
    
    if st.button("🔥 Burn All Data", use_container_width=True):
        st.session_state.trip_data = []
        st.rerun()

# --- MAIN HEADER ---
st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>🎋 {trip_name}</h1>", unsafe_allow_html=True)

# Calculation Logic
df = pd.DataFrame(st.session_state.trip_data)
total_cost = df['cost'].sum() if not df.empty else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Total Supplies Cost", f"${total_cost:,.2f}")
m2.metric("Nights in Jungle", (end_date - start_date).days)
m3.metric("Markers Placed", len(st.session_state.trip_data))

st.divider()

# --- ADD ACTIVITY ---
with st.expander("📍 Mark a New Location / Activity", expanded=False):
    with st.form("jungle_form", clear_on_submit=True):
        f1, f2 = st.columns([2, 1])
        with f1:
            act_name = st.text_input("What's the plan?")
            act_date = st.date_input("Date", min_value=start_date, max_value=end_date)
        with f2:
            act_cost = st.number_input("Cost ($)", min_value=0.0)
            act_status = st.selectbox("Current Status", ["Planned", "Planned but not booked", "Needs Review"])
            
        act_people = st.multiselect("Assign To", [p1_name, p2_name], default=[p1_name, p2_name])
        
        if st.form_submit_button("🍃 Add to Map", use_container_width=True):
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
status_border_colors = {
    "Planned": "#2D6A4F",              # Deep Leaf Green
    "Planned but not booked": "#FFB703", # Sunset Yellow
    "Needs Review": "#BC4749"           # Predator Red
}

date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    day_plans = [i for i in st.session_state.trip_data if i['date'] == date_str]
    
    st.markdown(f"### 🗓️ {d.strftime('%A, %b %d')}")
    
    if not day_plans:
        st.markdown("<p style='color: #A3B18A;'>No paths cleared for this day.</p>", unsafe_allow_html=True)
    else:
        for item in day_plans:
            # Routing Color Logic
            if p1_name in item['people'] and p2_name in item['people']:
                card_bg = shared_color
            elif p1_name in item['people']:
                card_bg = p1_color
            else:
                card_bg = p2_color
                
            border_color = status_border_colors.get(item['status'], "#333")
            
            # THE JUNGLE CARD
            st.markdown(f"""
                <div class="jungle-card" style="border-left: 12px solid {border_color}; background-color: {card_bg};">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 1.4rem; font-weight: 700;">{item['activity']}</span>
                        <span style="
                            font-size: 0.75rem; 
                            font-weight: 900; 
                            color: white; 
                            background: {border_color}; 
                            padding: 6px 14px; 
                            border-radius: 4px;
                            letter-spacing: 1px;
                        ">
                            {item['status'].upper()}
                        </span>
                    </div>
                    <div style="margin-top: 15px; display: flex; gap: 30px; font-size: 1rem;">
                        <span>👤 <b>{", ".join(item['people'])}</b></span>
                        <span>💰 <b>${item['cost']:,.2f}</b></span>
                    </div>
                </div>
            """, unsafe_allow_html=True)
