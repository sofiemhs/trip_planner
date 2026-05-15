import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import pydeck as pdk
import math

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

if 'edit_idx' not in st.session_state:
    st.session_state.edit_idx = None

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
        st.session_state.edit_idx = None
        st.rerun()

# --- CALCULATIONS ---
total_cost = sum(item.get('cost', 0.0) for item in st.session_state.trip_data)

def haversine_miles(lat1, lon1, lat2, lon2):
    R = 3958.8  # Radius of Earth in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))

# Compute Miles Traveled
sorted_activities_calc = sorted(st.session_state.trip_data, key=lambda x: x.get('date', '9999-12-31'))
path_calc = []
for activity in sorted_activities_calc:
    lat_s = activity.get('lat_start', activity.get('lat'))
    lon_s = activity.get('lon_start', activity.get('lon'))
    lat_e = activity.get('lat_end')
    lon_e = activity.get('lon_end')
    
    if lat_s is not None and lon_s is not None:
        path_calc.append((lat_s, lon_s))
    if lat_e is not None and lon_e is not None:
        path_calc.append((lat_e, lon_e))

total_miles = 0.0
for i in range(len(path_calc) - 1):
    total_miles += haversine_miles(path_calc[i][0], path_calc[i][1], path_calc[i+1][0], path_calc[i+1][1])

# --- MAIN CONTENT ---
st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{trip_name}</h1>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Trip Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Miles Traveled", f"{total_miles:,.0f} mi")

st.divider()

# --- ADD ACTIVITY (Top Section Only) ---
with st.expander("➕ Add Activity", expanded=False):
    with st.form("activity_form", clear_on_submit=True):
        
        # Row 1
        r1c1, r1c2, r1c3 = st.columns(3)
        act_name = r1c1.text_input("Activity/Location Name")
        act_start = r1c2.text_input("Start Point (Optional)")
        act_coords_start = r1c3.text_input("Start Coords (lat, lon)", placeholder="e.g. 34.07, -118.44")
        
        # Row 2
        r2c1, r2c2, r2c3 = st.columns(3)
        type_opts = ["Excursion", "Travel", "Housing"]
        act_type = r2c1.selectbox("Activity Type", type_opts, index=0)
        act_end = r2c2.text_input("End Point (Optional)")
        act_coords_end = r2c3.text_input("End Coords (lat, lon)", placeholder="e.g. 51.50, -0.12")
        
        # Row 3
        r3c1, r3c2, r3c3 = st.columns(3)
        status_opts = ["Booked", "Planned but not booked", "Needs Review"]
        act_status = r3c1.selectbox("Status", status_opts, index=0)
        act_cost = r3c2.number_input("Cost ($)", min_value=0.0, value=0.0)
        act_date = r3c3.date_input("Date", value=start_date, min_value=start_date, max_value=end_date)
        
        act_notes = st.text_area("Notes")
        
        traveler_names = [t["name"] for t in st.session_state.travelers]
        act_people = st.multiselect("Assign To", traveler_names, default=traveler_names[:1] if traveler_names else [])
        
        if st.form_submit_button("Confirm Activity", use_container_width=True):
            if act_name:
                
                # Apply Emojis and Colors based on manual selection
                if act_type == "Travel":
                    detected_emoji, color_hex = "✈️", "#4285F4"
                elif act_type == "Housing":
                    detected_emoji, color_hex = "🏨", "#34A853"
                else:
                    detected_emoji, color_hex = "🎒", "#EA4335"
                
                # Parse Start coordinates safely
                parsed_lat_start, parsed_lon_start = None, None
                if act_coords_start:
                    try:
                        lat_str, lon_str = act_coords_start.split(",")
                        parsed_lat_start = float(lat_str.strip())
                        parsed_lon_start = float(lon_str.strip())
                    except ValueError:
                        st.error("⚠️ Invalid Start coordinate format. Please use 'lat, lon'. Activity saved without start coordinates on the map.")

                # Parse End coordinates safely
                parsed_lat_end, parsed_lon_end = None, None
                if act_coords_end:
                    try:
                        lat_str, lon_str = act_coords_end.split(",")
                        parsed_lat_end = float(lat_str.strip())
                        parsed_lon_end = float(lon_str.strip())
                    except ValueError:
                        st.error("⚠️ Invalid End coordinate format. Please use 'lat, lon'. Activity saved without end coordinates on the map.")
                
                new_data = {
                    "date": str(act_date),
                    "activity": act_name,
                    "type": act_type,
                    "emoji": detected_emoji,
                    "color": color_hex,
                    "coords_start": act_coords_start,
                    "lat_start": parsed_lat_start,
                    "lon_start": parsed_lon_start,
                    "coords_end": act_coords_end,
                    "lat_end": parsed_lat_end,
                    "lon_end": parsed_lon_end,
                    "start_loc": act_start,
                    "end_loc": act_end,
                    "people": act_people,
                    "status": act_status,
                    "cost": act_cost,
                    "notes": act_notes
                }
                
                st.session_state.trip_data.append(new_data)
                st.rerun()

# --- ITINERARY ---
status_colors = {"Booked": "#2D6A4F", "Planned but not booked": "#FFB703", "Needs Review": "#BC4749"}
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
                
                # --- INLINE EDIT BLOCK ---
                if st.session_state.edit_idx == idx:
                    with st.container():
                        st.markdown(f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 15px;'>", unsafe_allow_html=True)
                        st.markdown("<h4 style='color: #004D00 !important; text-shadow: none;'>✏️ Edit Activity</h4>", unsafe_allow_html=True)
                        with st.form(key=f"inline_edit_{idx}"):
                            
                            # Row 1
                            er1c1, er1c2, er1c3 = st.columns(3)
                            e_name = er1c1.text_input("Activity/Location Name", value=item.get('activity', ''), key=f"ename_{idx}")
                            e_start = er1c2.text_input("Start Point (Optional)", value=item.get('start_loc', ''), key=f"estart_{idx}")
                            # Provide backward compatibility with older "coords" key
                            old_c = item.get('coords', '')
                            val_c_start = item.get('coords_start', old_c)
                            e_coords_start = er1c3.text_input("Start Coords (lat, lon)", placeholder="e.g. 34.07, -118.44", value=val_c_start, key=f"ecoords_s_{idx}")

                            # Row 2
                            er2c1, er2c2, er2c3 = st.columns(3)
                            type_opts = ["Excursion", "Travel", "Housing"]
                            def_type = item.get('type', 'Excursion')
                            type_idx = type_opts.index(def_type) if def_type in type_opts else 0
                            e_type = er2c1.selectbox("Activity Type", type_opts, index=type_idx, key=f"etype_{idx}")
                            e_end = er2c2.text_input("End Point (Optional)", value=item.get('end_loc', ''), key=f"eend_{idx}")
                            val_c_end = item.get('coords_end', '')
                            e_coords_end = er2c3.text_input("End Coords (lat, lon)", placeholder="e.g. 51.50, -0.12", value=val_c_end, key=f"ecoords_e_{idx}")

                            # Row 3
                            er3c1, er3c2, er3c3 = st.columns(3)
                            status_opts = ["Booked", "Planned but not booked", "Needs Review"]
                            def_status = item.get('status', 'Needs Review')
                            if def_status == "Planned": def_status = "Booked" # Catch old saves
                            stat_idx = status_opts.index(def_status) if def_status in status_opts else 0
                            e_status = er3c1.selectbox("Status", status_opts, index=stat_idx, key=f"estatus_{idx}")
                            e_cost = er3c2.number_input("Cost ($)", min_value=0.0, value=float(item.get('cost', 0.0)), key=f"ecost_{idx}")
                            
                            def_date = start_date
                            try: def_date = datetime.strptime(item.get('date', str(start_date)), "%Y-%m-%d").date()
                            except: pass
                            e_date = er3c3.date_input("Date", value=def_date, min_value=start_date, max_value=end_date, key=f"edate_{idx}")
                            
                            e_notes = st.text_area("Notes", value=item.get('notes', ''), key=f"enotes_{idx}")
                            
                            traveler_names = [t["name"] for t in st.session_state.travelers]
                            def_people = [p for p in item.get('people', []) if p in traveler_names]
                            e_people = st.multiselect("Assign To", traveler_names, default=def_people, key=f"epeople_{idx}")
                            
                            if st.form_submit_button("💾 Save Changes", use_container_width=True):
                                if e_name:
                                    if e_type == "Travel":
                                        detected_emoji, color_hex = "✈️", "#4285F4"
                                    elif e_type == "Housing":
                                        detected_emoji, color_hex = "🏨", "#34A853"
                                    else:
                                        detected_emoji, color_hex = "🎒", "#EA4335"
                                    
                                    # Parse Start coordinates safely
                                    parsed_lat_start, parsed_lon_start = None, None
                                    if e_coords_start:
                                        try:
                                            lat_str, lon_str = e_coords_start.split(",")
                                            parsed_lat_start = float(lat_str.strip())
                                            parsed_lon_start = float(lon_str.strip())
                                        except ValueError:
                                            st.error("⚠️ Invalid Start coordinate format. Please use 'lat, lon'.")

                                    # Parse End coordinates safely
                                    parsed_lat_end, parsed_lon_end = None, None
                                    if e_coords_end:
                                        try:
                                            lat_str, lon_str = e_coords_end.split(",")
                                            parsed_lat_end = float(lat_str.strip())
                                            parsed_lon_end = float(lon_str.strip())
                                        except ValueError:
                                            st.error("⚠️ Invalid End coordinate format. Please use 'lat, lon'.")
                                            
                                    st.session_state.trip_data[idx] = {
                                        "date": str(e_date),
                                        "activity": e_name,
                                        "type": e_type,
                                        "emoji": detected_emoji,
                                        "color": color_hex,
                                        "coords_start": e_coords_start,
                                        "lat_start": parsed_lat_start,
                                        "lon_start": parsed_lon_start,
                                        "coords_end": e_coords_end,
                                        "lat_end": parsed_lat_end,
                                        "lon_end": parsed_lon_end,
                                        "start_loc": e_start,
                                        "end_loc": e_end,
                                        "people": e_people,
                                        "status": e_status,
                                        "cost": e_cost,
                                        "notes": e_notes
                                    }
                                    st.session_state.edit_idx = None
                                    st.rerun()
                                    
                        # Buttons outside the form for Cancel and Delete
                        c1, c2 = st.columns(2)
                        if c1.button("❌ Cancel Edit", key=f"cancel_{idx}", use_container_width=True):
                            st.session_state.edit_idx = None
                            st.rerun()
                        if c2.button("🗑️ Delete Activity", key=f"del_{idx}", use_container_width=True):
                            st.session_state.trip_data.pop(idx)
                            st.session_state.edit_idx = None
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                # --- STANDARD CARD BLOCK ---
                else:
                    # Safe fetching of people list
                    people_list = item.get('people', [])
                    
                    # Color Logic
                    if len(people_list) > 1: card_bg = shared_color
                    elif len(people_list) == 1:
                        card_bg = next((t["color"] for t in st.session_state.travelers if t["name"] == people_list[0]), "#FFFFFF")
                    else: card_bg = "#FFFFFF"
                    
                    status_val = item.get('status', 'Needs Review')
                    if status_val == "Planned": status_val = "Booked" # Catch old saves
                    border_color = status_colors.get(status_val, "#333")
                    
                    with st.container():
                        
                        # Pre-format the dynamic HTML elements so there are absolutely no newlines causing markdown breaks
                        route_html = f"📍 <b>Route:</b> {item.get('start_loc', '')} → {item.get('end_loc', '')}<br>" if item.get('start_loc') or item.get('end_loc') else ""
                        notes_html = f"📝 <b>Notes:</b> {item.get('notes', '')}" if item.get('notes') else ""
                        
                        # Construct single continuous HTML string with margin-bottom hack to pull the button inside visually
                        card_html = f"""<div class="activity-card" style="border-left: 12px solid {border_color}; background-color: {card_bg}; margin-bottom: -60px; padding-bottom: 75px; position: relative;"><div style="display: flex; justify-content: space-between; align-items: flex-start;"><span style="font-size: 1.4rem; font-weight: 700;">{item.get('emoji', '🎒')} {item.get('activity', 'Unknown')}</span><span style="font-size: 0.75rem; font-weight: 900; color: white; background: {border_color}; padding: 6px 14px; border-radius: 4px;">{status_val.upper()}</span></div><div style="margin-top: 10px; width: 75%;">{route_html}👤 <b>Assignees:</b> {", ".join(people_list)} | 💰 <b>Cost:</b> ${item.get('cost', 0.0):,.2f}<br>{notes_html}</div></div>"""
                        
                        st.markdown(card_html, unsafe_allow_html=True)
                        
                        # Just the Pencil Edit Button, pulled up directly under the status bubble using columns
                        col_empty, col_btn = st.columns([5, 1.5])
                        with col_btn:
                            if st.button("✏️ Edit Activity", key=f"edit_{idx}", use_container_width=True):
                                st.session_state.edit_idx = idx
                                st.rerun()
                                
                        # Spacer to fix the layout for the next card below
                        st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)

st.divider()

# --- MAP SECTION ---
with st.expander("🗺️ Travel Route Map", expanded=True):
    st.write("Map pins and connections are automatically generated from the coordinates you add to your planned activities!")
    st.markdown("**Map Legend:** ✈️ Travel (Blue Pin) | 🏨 Housing (Green Pin) | 🎒 Excursion (Red Pin)")
    
    # Sort activities chronologically to ensure route connects in order
    sorted_activities = sorted(st.session_state.trip_data, key=lambda x: x.get('date', '9999-12-31'))
    
    # Extract only valid coordinates for the map
    map_data = []
    path_coords = []
    
    for activity in sorted_activities:
        # Fallback to older 'lat'/'lon' structure to maintain backwards compatibility
        lat_s = activity.get('lat_start', activity.get('lat'))
        lon_s = activity.get('lon_start', activity.get('lon'))
        lat_e = activity.get('lat_end')
        lon_e = activity.get('lon_end')
        
        # Convert hex string (e.g., "#EA4335") to RGB list (e.g., [234, 67, 53]) for PyDeck
        hex_c = activity.get('color', '#EA4335').lstrip('#')
        rgb = [int(hex_c[i:i+2], 16) for i in (0, 2, 4)]
        
        has_both = (lat_s is not None) and (lat_e is not None)
        base_name = activity.get("activity", "Unknown")
        
        if lat_s is not None and lon_s is not None:
            map_data.append({
                "name": f"{base_name} (Start)" if has_both else base_name,
                "lat": lat_s, 
                "lon": lon_s,
                "color": rgb
            })
            path_coords.append([lon_s, lat_s])
            
        if lat_e is not None and lon_e is not None:
            map_data.append({
                "name": f"{base_name} (End)",
                "lat": lat_e, 
                "lon": lon_e,
                "color": rgb
            })
            path_coords.append([lon_e, lat_e])
            
    if map_data:
        # Define PyDeck Scatterplot Layer (The Pins)
        scatter_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_data,
            get_position="[lon, lat]",
            get_color="color",
            get_radius=10000,
            radius_scale=1,
            radius_min_pixels=6,
            radius_max_pixels=15,
            pickable=True
        )
        
        # Build layers list
        layers = [scatter_layer]
        
        # Add PyDeck Path Layer (The Connections) if there is more than 1 point
        if len(path_coords) > 1:
            path_layer = pdk.Layer(
                "PathLayer",
                data=[{"path": path_coords}],
                get_path="path",
                get_color=[200, 200, 200, 200], # Light Gray line
                width_scale=20,
                width_min_pixels=2,
                get_width=3
            )
            layers.insert(0, path_layer) # Insert path under the pins
        
        # Calculate center of the map
        avg_lat = sum(d['lat'] for d in map_data) / len(map_data)
        avg_lon = sum(d['lon'] for d in map_data) / len(map_data)
        
        # Render the map
        view_state = pdk.ViewState(latitude=avg_lat, longitude=avg_lon, zoom=5, pitch=0)
        r = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{name}"})
        st.pydeck_chart(r)
        
    else:
        # Default map centered on Peru if no points are added yet
        st.info("No pins added yet. Map is currently centered on Peru.")
        view_state = pdk.ViewState(latitude=-9.1900, longitude=-75.0152, zoom=5, pitch=0)
        r = pdk.Deck(initial_view_state=view_state)
        st.pydeck_chart(r)
