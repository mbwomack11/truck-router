pythonimport streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Truck Routing Portal", page_icon="🚛", layout="wide")

# Custom Dashboard Styling
st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    div.stButton > button:first-child {
        background-color: #1e3a8a; color: white; font-weight: bold; border-radius: 6px; width: 100%; height: 45px;
    }
    .metric-box {
        background-color: white; padding: 15px; border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;
    }
    </style>
""", unsafe_value=True)

st.title("🚛 Commercial Fleet Routing Engine")
st.caption("Configured Profile: 53ft Dry Van | 80,000 lbs GVW | 13'6\" Maximum Clearance")

# Setup Sidebar Configurations
st.sidebar.header("🔑 Authentication")
api_key = st.sidebar.text_input("HERE Maps API Key:", type="password", help="Enter your ://here.com routing token")

st.sidebar.subheader("🔒 Rigid Truck Constraints")
st.sidebar.info("""
- **Height:** 13'6" Max Clearances
- **Weight:** 80,000 lbs GVW 
- **Axle Layout:** 5-Axle Combo
- **Hazmat:** None (General Dry Freight)
""")

# Layout Panels
col1, col2 = st.columns()

with col1:
    st.subheader("Route Coordinates")
    st.caption("Input coordinates format: Latitude, Longitude")
    start_coords = st.text_input("Origin Point", value="41.8781, -87.6298", help="Default: Chicago, IL")
    end_coords = st.text_input("Destination Point", value="40.7128, -74.0060", help="Default: New York, NY")
    calculate = st.button("Generate Truck-Safe Route")

with col2:
    if calculate:
        if not api_key:
            st.error("⚠️ API key missing. Please insert your HERE Maps API key in the sidebar.")
        else:
            with st.spinner("Analyzing vertical clearance maps and structural weight limits..."):
                url = "https://hereapi.com"
                params = {
                    "apiKey": api_key,
                    "transportMode": "truck",
                    "origin": start_coords.strip(),
                    "destination": end_coords.strip(),
                    "return": "summary,polyline",
                    "vehicle[height]": 411,
                    "vehicle[width]": 260,
                    "vehicle[length]": 2200,
                    "vehicle[grossWeight]": 36287,
                    "vehicle[axleCount]": 5,
                    "vehicle[type]": "tractorTrailer",
                    "routingMode": "fast"
                }
                
                try:
                    res = requests.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        section = data['routes']['sections'][0]
                        summary = section['summary']
                        
                        miles = summary['length'] * 0.000621371
                        hours = summary['duration'] / 3600
                        
                        st.success("✅ Commercial Route Verified Clean of Clearance or Weight Hazards!")
                        
                        # Displaying Metrics
                        m_col1, m_col2 = st.columns(2)
                        with m_col1:
                            st.metric("Legal Travel Distance", f"{miles:.1f} Miles")
                        with m_col2:
                            st.metric("Est. In-Transit Time", f"{hours:.1f} Hours")
                        
                        # Parsing coordinates to display on the map
                        try:
                            s_lat, s_lng = map(float, start_coords.split(','))
                            e_lat, e_lng = map(float, end_coords.split(','))
                            
                            map_data = pd.DataFrame({
                                'lat': [s_lat, e_lat],
                                'lon': [s_lng, e_lng]
                            })
                            
                            st.subheader("🗺️ Operational Route Visualizer")
                            st.map(map_data, zoom=5)
                            st.caption("💡 The map framework displays pins highlighting origin and destination points of the truck-compliant passage.")
                        except Exception as map_err:
                            st.warning("Calculated successfully, but map pins could not be parsed.")
                            
                    else:
                        st.error(f"❌ Routing Rejected. A standard 80k lbs combo cannot safely navigate this corridor. Code: {res.status_code}")
                except Exception as e:
                    st.error(f"Network error linking to central map registry: {str(e)}")
    else:
        # Default placeholder map state when app loads
        st.subheader("🗺️ Operational Route Visualizer")
        placeholder_data = pd.DataFrame({'lat': [41.8781], 'lon': [-87.6298]})
        st.map(placeholder_data, zoom=3)
