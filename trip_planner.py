import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import pydeck as pdk

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

# --- MAIN CONTENT ---
st.markdown(f"<h1 style='text-align: center; font-size: 3rem;'>{trip_name}</h1>", unsafe_allow_html=True)

m1, m2, m3 = st.columns(3)
m1.metric("Total Budget", f"${total_cost:,.2f}")
m2.metric("Trip Duration", f"{(end_date - start_date).days + 1} Days")
m3.metric("Total Activities", len(st.session_state.trip_data))

st.divider()

# --- ADD / EDIT ACTIVITY ---
is_edit = st.session_state.edit_idx is not None
edit_item = st.session_state.trip_data[st.session_state.edit_idx] if is_edit else {}

with st.expander("➕ Add / Edit Activity", expanded=is_edit):
    with st.form("activity_form", clear_on_submit=not is_edit):
        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            act_name = st.text_input("Activity/Location Name", value=edit_item.get('activity', ''))
            
            # Manual Activity Type Selection
            type_opts = ["Excursion", "Travel", "Housing"]
            def_type = edit_item.get('type', 'Excursion')
            type_idx = type_opts.index(def_type) if def_type in type_opts else 0
            act_type = st.selectbox("Activity Type", type_opts, index=type_idx)
            
            # Safe date parsing for edit mode
            def_date = start_date
            if is_edit and 'date' in edit_item:
                try:
                    def_date = datetime.strptime(edit_item['date'], "%Y-%m-%d").date()
                except: pass
            act_date = st.date_input("Date", value=def_date, min_value=start_date, max_value=end_date)
            
        with f2:
            act_start = st.text_input("Start Point (Optional)", value=edit_item.get('start_loc', ''))
            act_end = st.text_input("End Point (Optional)", value=edit_item.get('end_loc', ''))
            act_coords = st.text_input("Coordinates (lat, lon)", placeholder="e.g. 34.07, -118.44", value=edit_item.get('coords', ''))
            act_cost = st.number_input("Cost ($)", min_value=0.0, value=float(edit_item.get('cost', 0.0)))
            
        with f3:
            status_opts = ["Planned", "Planned but not booked", "Needs Review"]
            def_status = edit_item.get('status', 'Needs Review')
            stat_idx = status_opts.index(def_status) if def_status in status_opts else 0
            act_status = st.selectbox("Status", status_opts, index=stat_idx)
            act_link = st.text_input("Link (URL)", value=edit_item.get('link', ''))
            
        act_notes = st.text_area("Notes", value=edit_item.get('notes', ''))
        
        traveler_names = [t["name"] for t in st.session_state.travelers]
        if is_edit:
            def_people = [p for p in edit_item.get('people', []) if p in traveler_names]
        else:
            def_people = traveler_names[:1] if traveler_names else []
            
        act_people = st.multiselect("Assign To", traveler_names, default=def_people)
        
        submit_label = "Update Activity" if is_edit else "Confirm Activity"
        if st.form_submit_button(submit_label, use_container_width=True):
            if act_name:
                
                # Apply Emojis and Colors based on manual selection
                if act_type == "Travel":
                    detected_emoji = "✈️"
                    color_hex = "#4285F4" # Blue map pin
                elif act_type == "Housing":
                    detected_emoji = "🏨"
                    color_hex = "#34A853" # Green map pin
                else:
                    detected_emoji = "🎒"
                    color_hex = "#EA4335" # Red map pin
                
                # Parse the coordinates safely
                parsed_lat, parsed_lon = None, None
                if act_coords:
                    try:
                        lat_str, lon_str = act_coords.split(",")
                        parsed_lat = float(lat_str.strip())
                        parsed_lon = float(lon_str.strip())
                    except ValueError:
                        st.error("⚠️ Invalid coordinate format. Please use 'lat, lon'. Activity saved without coordinates on the map.")
                
                new_data = {
                    "date": str(act_date),
                    "activity": act_name,
                    "type": act_type,
                    "emoji": detected_emoji,
                    "color": color_hex,
                    "coords": act_coords, # Save the raw string so it stays in the text box when editing
                    "lat": parsed_lat,    # Save the parsed float for the map
                    "lon": parsed_lon,    # Save the parsed float for the map
                    "start_loc": act_start,
                    "end_loc": act_end,
                    "people": act_people,
                    "status": act_status,
                    "cost": act_cost,
                    "link": act_link,
                    "notes": act_notes
                }
                if is_edit:
                    st.session_state.trip_data[st.session_state.edit_idx] = new_data
                    st.session_state.edit_idx = None
                else:
                    st.session_state.trip_data.append(new_data)
                st.rerun()
                
    # Separate Cancel/Delete buttons when in Edit Mode
    if is_edit:
        c1, c2 = st.columns(2)
        if c1.button("❌ Cancel Edit", use_container_width=True):
            st.session_state.edit_idx = None
            st.rerun()
        if c2.button("🗑️ Delete Activity", use_container_width=True):
            st.session_state.trip_data.pop(st.session_state.edit_idx)
            st.session_state.edit_idx = None
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
                    card_html = f"""<div class="activity-card" style="border-left: 12px solid {border_color}; background-color: {card_bg};"><div style="display: flex; justify-content: space-between; align-items: center;"><span style="font-size: 1.4rem; font-weight: 700;">{item.get('emoji', '🎒')} {item.get('activity', 'Unknown')}</span><span style="font-size: 0.75rem; font-weight: 900; color: white; background: {border_color}; padding: 6px 14px; border-radius: 4px;">{status_val.upper()}</span></div><div style="margin-top: 10px;">{route_html}👤 <b>Assignees:</b> {", ".join(people_list)} | 💰 <b>Cost:</b> ${item.get('cost', 0.0):,.2f}<br>{link_html}{notes_html}</div></div>"""
                    
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Just the Pencil Edit Button
                    if st.button("✏️ Edit Activity", key=f"edit_{idx}", use_container_width=True):
                        st.session_state.edit_idx = idx
                        st.rerun()

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
        if activity.get('lat') is not None and activity.get('lon') is not None:
            # Convert hex string (e.g., "#EA4335") to RGB list (e.g., [234, 67, 53]) for PyDeck
            hex_c = activity.get('color', '#EA4335').lstrip('#')
            rgb = [int(hex_c[i:i+2], 16) for i in (0, 2, 4)]
            
            map_data.append({
                "name": activity.get("activity", "Unknown"),
                "lat": activity.get('lat'), 
                "lon": activity.get('lon'),
                "color": rgb
            })
            path_coords.append([activity.get('lon'), activity.get('lat')])
            
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
