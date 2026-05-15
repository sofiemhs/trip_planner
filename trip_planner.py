import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json

# --- CONFIG ---
st.set_page_config(page_title="Trip Planner", layout="wide", page_icon="📍")

# --- CUSTOM THEME (CSS) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700&display=swap');

    /* Global Font & Background */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0B2010 0%, #1E3D24 100%);
    }

    /* Sidebar - High Contrast Styling */
    [data-testid="stSidebar"] {
        background-color: #F5F5DC !important; /* Beige background */
        border-right: 2px solid #3D5A45;
    }

    /* Force all sidebar text to be Dark Forest Green */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown {
        color: #0B2010 !important;
        font-weight: 600;
    }

    /* Activity Cards */
    .activity-card {
        background-color: #FFFFFF;
        padding: 22px;
        border-radius: 18px;
        margin-bottom: 18px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.3);
        color: #1B2E1D !important;
    }
    
    .activity-card b, .activity-card span {
        color: #1B2E1D !important;
    }

    /* Header Styling */
    h1, h2, h3, h4 {
        color: #E9F5DB !important;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
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

if 'travelers' not in st.session_state:
    # Start with 1 traveler
    st.session_state.travelers = [{"name": "Traveler 1", "color": "#D4E9D7"}]

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1>Trip Setup</h1>", unsafe_allow_html=True)
    trip_name = st.text_input("Trip Name", value="Italy Coastline 2026")
    
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", datetime.now())
    end_date = col_b.date_input("End Date", datetime.now() + timedelta(days=7))
    
    st.divider()
    
    st.markdown("### Travelers")
    
    # Dynamic Traveler Management
    updated_travelers = []
    for i, traveler in enumerate(st.session_state.travelers):
        c1, c2 = st.columns([2, 1])
        t_name = c1.text_input(f"Name {i+1}", value=traveler["name"], key=f"tname_{i}")
        t_color = c2.color_picker(f"Color", value=traveler["color"], key=f"tcol_{i}")
        updated_travelers.append({"name": t_name, "color": t_color})
    
    st.session_state.travelers = updated_travelers

    if st.button("➕ Add Traveler"):
        st.session_state.travelers.append({"name": f"Traveler {len(st.session_state.travelers)+1}", "color": "#FFFFFF"})
        st.rerun()
    
    shared_color = st.color_picker("Color for Multiple People", "#FFF9C4")
    
    st.divider()
    
    st.subheader("Data Management")
    trip_json = json.dumps(st.session_state.trip_data, indent=4)
    st.download_button("💾 Save Plan", data=trip_json, file_name="trip_plan.json", use_container_width=True)
    
    uploaded_file = st.file_uploader("📂 Load Plan", type="json")
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)
    
    if st.button("🗑️ Reset Trip Data", use_container_width=True):
        st.session_state.trip_data = []
        st.rerun()

# --- MAIN CONTENT ---
st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{trip_name}</h1>", unsafe_allow_html=True)

# Totals
df = pd.DataFrame(st.session_state.trip_data)
total_cost = df['cost'].sum() if not df.empty else 0.0

m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Trip Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Activities", len(st.session_state.trip_data))

st.divider()

# --- ADD ACTIVITY ---
with st.expander("➕ Add Activity", expanded=False):
    with st.form("activity_form", clear_on_submit=True):
        f1, f2 = st.columns([2, 1])
        with f1:
            act_name = st.text_input("Activity/Location Name")
            act_date = st.date_input("Date", min_value=start_date, max_value=end_date)
        with f2:
            act_cost = st.number_input("Cost ($)", min_value=0.0)
            act_status = st.selectbox("Status", ["Planned", "Planned but not booked", "Needs Review"])
            
        traveler_names = [t["name"] for t in st.session_state.travelers]
        act_people = st.multiselect("Assign To", traveler_names, default=traveler_names[:1])
        
        if st.form_submit_button("Confirm Activity", use_container_width=True):
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
    "Planned": "#2D6A4F",              # Green
    "Planned but not booked": "#FFB703", # Yellow
    "Needs Review": "#BC4749"           # Red
}

date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    day_plans = [i for i in st.session_state.trip_data if i['date'] == date_str]
    
    st.markdown(f"### 🗓️ {d.strftime('%A, %b %d')}")
    
    if not day_plans:
        st.markdown("<p style='color: #A3B18A; font-style: italic;'>No activities planned.</p>", unsafe_allow_html=True)
    else:
        for item in day_plans:
            # Color Logic
            if len(item['people']) > 1:
                card_bg = shared_color
            elif len(item['people']) == 1:
                # Find the color of the specific person
                person_name = item['people'][0]
                card_bg = next((t["color"] for t in st.session_state.travelers if t["name"] == person_name), "#FFFFFF")
            else:
                card_bg = "#FFFFFF"
                
            border_color = status_colors.get(item['status'], "#333")
            
            st.markdown(f"""
                <div class="activity-card" style="border-left: 12px solid {border_color}; background-color: {card_bg};">
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
