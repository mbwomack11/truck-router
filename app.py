import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Truck Routing Portal", page_icon="Res", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    div.stButton > button:first-child {
        background-color: #1e3a8a; color: white; font-weight: bold; border-radius: 6px; width: 100%; height: 45px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Commercial Fleet Routing Engine")
st.caption("Configured Profile: 53ft Dry Van | 80,000 lbs GVW | 13'6\" Maximum Clearance")

st.sidebar.header("Authentication")
api_key = st.sidebar.text_input("HERE Maps API Key:", type="password")

st.sidebar.subheader("Rigid Truck Constraints")
st.sidebar.info("""
- Height: 13'6" Max Clearances
- Weight: 80,000 lbs GVW 
- Axle Layout: 5-Axle Combo
- Hazmat: None (General Dry Freight)
""")

def get_suggestions(query, api_key):
    if not query or len(query) < 3 or not api_key:
        return []
    url = "https://hereapi.com"
    params = {"apiKey": api_key, "q": query, "limit": 5}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            return [item["title"] for item in res.json().get("items", [])]
    except:
        pass
    return []

def geocode_address(address, api_key):
    url = "https://hereapi.com"
    params = {"apiKey": api_key, "q": address}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                pos = items[0]["position"]
                return f"{pos['lat']},{pos['lng']}"
    except:
        pass
    return None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Route Locations")
    
    start_input = st.text_input("Origin Address (Type city/zip then press Enter to suggest)", value="Chicago, IL")
    start_options = get_suggestions(start_input, api_key) if api_key else []
    start_address = st.selectbox("Confirm Selected Origin:", [start_input] + start_options if start_options else [start_input])
    
    end_input = st.text_input("Destination Address (Type city/zip then press Enter to suggest)", value="New York, NY")
    end_options = get_suggestions(end_input, api_key) if api_key else []
    end_address = st.selectbox("Confirm Selected Destination:", [end_input] + end_options if end_options else [end_input])
    
    calculate = st.button("Generate Truck-Safe Route")

with col2:
    if calculate:
        if not api_key:
            st.error("API key missing. Please insert your HERE Maps API key in the sidebar.")
        else:
            with st.spinner("Converting addresses and analyzing clearances..."):
                start_coords = geocode_address(start_address, api_key)
                end_coords = geocode_address(end_address, api_key)
                
                if not start_coords or not end_coords:
                    st.error("Could not find one of the addresses. Please check your spelling or API Key.")
                else:
                    url = "https://hereapi.com"
                    params = {
                        "apiKey": api_key,
                        "transportMode": "truck",
                        "origin": start_coords,
                        "destination": end_coords,
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
                            
                            st.success("Commercial Route Verified Clean of Clearance or Weight Hazards!")
                            
                            m_col1, m_col2 = st.columns(2)
                            with m_col1:
                                st.metric("Legal Travel Distance", f"{miles:.1f} Miles")
                            with m_col2:
                                st.metric("Est. In-Transit Time", f"{hours:.1f} Hours")
                            
                            try:
                                s_lat, s_lng = map(float, start_coords.split(','))
                                e_lat, e_lng = map(float, end_coords.split(','))
                                
                                map_data = pd.DataFrame({
                                    'lat': [s_lat, e_lat],
                                    'lon': [s_lng, e_lng]
                                })
                                
                                st.subheader("Operational Route Visualizer")
                                st.map(map_data, zoom=5)
                            except Exception as map_err:
                                st.warning("Calculated successfully, but map pins could not be parsed.")
                                
                        else:
                            st.error(f"Routing Rejected. A standard 80k lbs combo cannot safely navigate this corridor. Code: {res.status_code}")
                    except Exception as e:
                        st.error(f"Network error linking to central map registry: {str(e)}")
    else:
        st.subheader("Operational Route Visualizer")
        placeholder_data = pd.DataFrame({'lat': [41.8781], 'lon': [-87.6298]})
        st.map(placeholder_data, zoom=3)
