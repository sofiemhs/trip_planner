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

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }

    .stApp {
        background: linear-gradient(135deg, #0B2010 0%, #1E3D24 100%);
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #F5F5DC !important;
        border-right: 2px solid #3D5A45;
    }

    /* Data Management & Sidebar Readability Fix */
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] .stMarkdown {
        color: #228B22 !important;
        font-weight: 600;
    }
    
    /* Make specific upload label DARK GREEN */
    [data-testid="stSidebar"] .stFileUploader label p {
        color: #004D00 !important; 
    }
    
    /* FORCE Sidebar Headings to be 100% Solid Dark Green with NO shadow or opacity effects */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #004D00 !important;
        text-shadow: none !important;
        opacity: 1 !important;
    }
    
    /* Make "save plan", dropzone text, and "Reset" related buttons off-white/white */
    [data-testid="stSidebar"] .stDownloadButton button p,
    [data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] *,
    [data-testid="stSidebar"] .stFileUploader small,
    [data-testid="stSidebar"] .stFileUploader button,
    [data-testid="stSidebar"] .stButton button p {
        color: #FFFFFF !important; /* Pure white text for the dropzone and buttons */
    }

    /* Add a dark green background to the buttons so the white text is readable */
    [data-testid="stSidebar"] .stDownloadButton button,
    [data-testid="stSidebar"] .stFileUploaderDropzone,
    [data-testid="stSidebar"] .stFileUploader button,
    [data-testid="stSidebar"] .stButton button {
        background-color: #2D6A4F !important;
        border: 1px solid #1E3D24 !important;
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
    
    .activity-card b, .activity-card span, .activity-card a {
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
    st.session_state.travelers = [{"name": "Traveler 1", "color": "#D4E9D7"}]

if 'city_coords' not in st.session_state:
    st.session_state.city_coords = []

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='color: #004D00 !important; text-shadow: none !important; opacity: 1 !important;'>Trip Setup</h1>", unsafe_allow_html=True)
    trip_name = st.text_input("Trip Name", value="Italy Coastline 2026")
    
    col_a, col_b = st.columns(2)
    start_date = col_a.date_input("Start Date", datetime.now())
    end_date = col_b.date_input("End Date", datetime.now() + timedelta(days=7))
    
    st.divider()
    
    st.markdown("<h3 style='color: #004D00 !important; text-shadow: none !important; opacity: 1 !important;'>Travelers</h3>", unsafe_allow_html=True)
    temp_travelers = []
    for i, traveler in enumerate(st.session_state.travelers):
        col1, col2, col3 = st.columns([2, 1, 1])
        t_name = col1.text_input(f"Name", value=traveler["name"], key=f"tname_{i}", label_visibility="collapsed")
        t_color = col2.color_picker(f"Col", value=traveler["color"], key=f"tcol_{i}", label_visibility="collapsed")
        if col3.button("🗑️", key=f"remove_t_{i}"):
            st.session_state.travelers.pop(i)
            st.rerun()
        temp_travelers.append({"name": t_name, "color": t_color})
    
    st.session_state.travelers = temp_travelers

    if st.button("➕ Add Traveler"):
        st.session_state.travelers.append({"name": f"Traveler {len(st.session_state.travelers)+1}", "color": "#FFFFFF"})
        st.rerun()
    
    shared_color = st.color_picker("Shared Color", "#FFF9C4")
    
    st.divider()
    
    st.markdown("<h3 style='color: #004D00 !important; text-shadow: none !important; opacity: 1 !important;'>Data Management</h3>", unsafe_allow_html=True)
    trip_json = json.dumps(st.session_state.trip_data, indent=4)
    st.download_button("💾 save plan", data=trip_json, file_name="trip_plan.json", use_container_width=True)
    
    st.caption("How to upload: Click 'Browse files' below and select a previously saved 'trip_plan.json' file to restore your itinerary data.")
    uploaded_file = st.file_uploader("📂 Upload", type="json")
    if uploaded_file:
        st.session_state.trip_data = json.load(uploaded_file)
        st.success("✅ Plan uploaded successfully!")
    
    if st.button("🗑️ Reset", use_container_width=True):
        st.session_state.trip_data = []
        st.rerun()

# --- CALCULATIONS ---
total_cost = sum(item.get('cost', 0.0) for item in st.session_state.trip_data)
cities_visited = list(set([item.get('city', 'Unknown') for item in st.session_state.trip_data if item.get('city')]))

# --- MAIN CONTENT ---
st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{trip_name}</h1>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Trip Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Cities Visited", len(cities_visited))

st.divider()

# --- ADD ACTIVITY ---
with st.expander("➕ Add / Edit Activity", expanded=False):
    with st.form("activity_form", clear_on_submit=True):
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            act_name = st.text_input("Activity/Location Name")
            act_city = st.text_input("City")
            act_date = st.date_input("Date", min_value=start_date, max_value=end_date)
        with f2:
            act_start = st.text_input("Start Point (Optional)")
            act_end = st.text_input("End Point (Optional)")
            act_cost = st.number_input("Cost ($)", min_value=0.0)
        with f3:
            act_status = st.selectbox("Status", ["Planned", "Planned but not booked", "Needs Review"])
            act_link = st.text_input("Link (URL)")
            
        act_notes = st.text_area("Notes")
        traveler_names = [t["name"] for t in st.session_state.travelers]
        act_people = st.multiselect("Assign To", traveler_names, default=traveler_names[:1] if traveler_names else [])
        
        if st.form_submit_button("Confirm Activity", use_container_width=True):
            if act_name:
                st.session_state.trip_data.append({
                    "date": str(act_date),
                    "activity": act_name,
                    "city": act_city,
                    "start_loc": act_start,
                    "end_loc": act_end,
                    "people": act_people,
                    "status": act_status,
                    "cost": act_cost,
                    "link": act_link,
                    "notes": act_notes
                })
                st.rerun()

# --- ITINERARY ---
status_colors = {"Planned": "#2D6A4F", "Planned but not booked": "#FFB703", "Needs Review": "#BC4749"}
date_range = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

for d in date_range:
    date_str = str(d)
    day_plans = [i for i in st.session_state.trip_data if i.get('date') == date_str]
    st.markdown(f"### 🗓️ {d.strftime('%A, %b %d')}")
    
    if not day_plans:
        st.markdown("<p style='color: #A3B18A; font-style: italic;'>No activities.</p>", unsafe_allow_html=True)
    else:
        for idx, item in enumerate(st.session_state.trip_data):
            if item.get('date') == date_str:
                # Safe fetching of people list
                people_list = item.get('people', [])
                
                # Color Logic
                if len(people_list) > 1: card_bg = shared_color
                elif len(people_list) == 1:
                    card_bg = next((t["color"] for t in st.session_state.travelers if t["name"] == people_list[0]), "#FFFFFF")
                else: card_bg = "#FFFFFF"
                
                status_val = item.get('status', 'Needs Review')
                border_color = status_colors.get(status_val, "#333")
                
                with st.container():
                    
                    # Pre-format the dynamic HTML elements so there are absolutely no newlines causing markdown breaks
                    route_html = f"📍 <b>Route:</b> {item.get('start_loc', '')} → {item.get('end_loc', '')}<br>" if item.get('start_loc') or item.get('end_loc') else ""
                    link_html = f"🔗 <a href='{item.get('link', '')}'>Visit Link</a><br>" if item.get('link') else ""
                    notes_html = f"📝 <b>Notes:</b> {item.get('notes', '')}" if item.get('notes') else ""
                    
                    # Construct single continuous HTML string
                    card_html = f"""<div class="activity-card" style="border-left: 12px solid {border_color}; background-color: {card_bg};"><div style="display: flex; justify-content: space-between; align-items: center;"><span style="font-size: 1.4rem; font-weight: 700;">{item.get('activity', 'Unknown')} ({item.get('city', 'N/A')})</span><span style="font-size: 0.75rem; font-weight: 900; color: white; background: {border_color}; padding: 6px 14px; border-radius: 4px;">{status_val.upper()}</span></div><div style="margin-top: 10px;">{route_html}👤 <b>Assignees:</b> {", ".join(people_list)} | 💰 <b>Cost:</b> ${item.get('cost', 0.0):,.2f}<br>{link_html}{notes_html}</div></div>"""
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Edit/Move/Delete Buttons
                    b1, b2, b3, b4 = st.columns([1,1,1,5])
                    if b1.button("🗑️", key=f"del_{idx}"):
                        st.session_state.trip_data.pop(idx)
                        st.rerun()
                    if b2.button("⬆️", key=f"up_{idx}") and idx > 0:
                        st.session_state.trip_data[idx], st.session_state.trip_data[idx-1] = st.session_state.trip_data[idx-1], st.session_state.trip_data[idx]
                        st.rerun()
                    if b3.button("⬇️", key=f"down_{idx}") and idx < len(st.session_state.trip_data)-1:
                        st.session_state.trip_data[idx], st.session_state.trip_data[idx+1] = st.session_state.trip_data[idx+1], st.session_state.trip_data[idx]
                        st.rerun()

st.divider()

# --- MAP SECTION ---
with st.expander("🗺️ Travel Route Map"):
    st.write("Add your city coordinates here to see them on the map:")
    map_col1, map_col2, map_col3 = st.columns([2, 1, 1])
    c_name = map_col1.text_input("City Name")
    c_lat = map_col2.number_input("Lat", format="%.4f")
    c_lon = map_col3.number_input("Lon", format="%.4f")
    if st.button("📍 Add to Map"):
        st.session_state.city_coords.append({"city": c_name, "lat": c_lat, "lon": c_lon})
    
    if st.session_state.city_coords:
        map_df = pd.DataFrame(st.session_state.city_coords)
        st.map(map_df)
