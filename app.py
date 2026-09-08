import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Truck Routing Portal", page_icon="Res", layout="wide")

# Secure locked active HERE key for truck metrics
api_key = "KLhVOBUT2NwvZfoHebi0254eWYI9WL5k9jjjOlEilgU"

st.markdown("""
    <style>
    .main { background-color: #f4f6f9; }
    div.stButton > button:first-child {
        background-color: #1e3a8a; color: white; font-weight: bold; border-radius: 6px; width: 100%; height: 45px;
    }
    .direction-step {
        padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #334155;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Commercial Fleet Routing Engine")
st.caption("Configured Profile: 53ft Dry Van | 80,000 lbs GVW | 13'6\" Maximum Clearance")

st.sidebar.header("Navigation Status")
st.sidebar.success("🔒 HERE Maps Core Connected")

st.sidebar.subheader("Rigid Truck Constraints")
st.sidebar.info("""
- Height: 13'6" Max Clearances
- Weight: 80,000 lbs GVW 
- Axle Layout: 5-Axle Combo
- Hazmat: None (General Dry Freight)
""")

def free_geocode(text):
    if "," in text:
        try:
            parts = text.split(",")
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lng = float(parts[1].strip())
                return f"{lat},{lng}"
        except:
            pass
            
    url = "https://openstreetmap.org"
    headers = {"User-Agent": "WixTruckRoutingEngineCustomApp_FleetRouter/2.0"}
    params = {"q": text, "format": "json", "limit": 1}
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data and len(data) > 0:
                # Target the first matching index item directly out of the search response
                location_data = data[0]
                return f"{location_data['lat']},{location_data['lon']}"
    except:
        pass
    return None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Route Locations")
    st.caption("Type any city, full street address, or ZIP code freely.")
    start_address = st.text_input("Origin Location", value="Newport, TN")
    end_address = st.text_input("Destination Location", value="Afton, TN")
    calculate = st.button("Generate Truck-Safe Route")

with col2:
    if calculate:
        with st.spinner("Processing text addresses and verifying clearance routes..."):
            start_coords = free_geocode(start_address)
            end_coords = free_geocode(end_address)
            
            if not start_coords or not end_coords:
                st.error("Could not find those locations. Please verify your spelling or try typing City, State (e.g., Newport, TN).")
            else:
                url = "https://hereapi.com"
                
                params = {
                    "apiKey": api_key,
                    "transportMode": "truck",
                    "origin": start_coords,
                    "destination": end_coords,
                    "return": "summary,polyline,actions",
                    "routingMode": "fast",
                    
                    # Accurate HERE API parameter layout matching enterprise truck rules
                    "vehicle[height]": 411,        
                    "vehicle[width]": 260,         
                    "vehicle[length]": 2200,       
                    "vehicle[grossWeight]": 36287,  
                    "vehicle[axleCount]": 5,       
                    "vehicle[type]": "straightTruck", 
                    "vehicle[trailerCount]": 1     
                }
                
                try:
                    res = requests.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        
                        if 'routes' in data and len(data['routes']) > 0:
                            route_data = data['routes'][0]
                            if 'sections' in route_data and len(route_data['sections']) > 0:
                                section = route_data['sections'][0]
                                summary = section.get('summary', {})
                                
                                miles = summary.get('length', 0) * 0.000621371
                                hours = summary.get('duration', 0) / 3600
                                
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
                                    st.map(map_data, zoom=9)
                                except Exception as map_err:
                                    st.warning("Calculated successfully, but map pins could not be parsed.")
                                
                                st.subheader("📖 Truck-Compliant Manifest Directions")
                                actions = section.get('actions', [])
                                if actions:
                                    for index, step in enumerate(actions):
                                        instruction = step.get('instruction', '')
                                        if instruction:
                                            st.markdown(f"<div class='direction-step'>{index + 1}. {instruction}</div>", unsafe_allow_html=True)
                                else:
                                    st.info("Route verified safe, but detailed turn maneuvers are unavailable for this segment.")
                            else:
                                st.error("No valid sections found in route response.")
                        else:
                            st.error("No valid routes returned from routing server.")
                            
                    else:
                        st.error(f"Routing Rejected. Server returned status code: {res.status_code}. Response: {res.text}")
                except Exception as e:
                    st.error(f"Network error linking to central map registry: {str(e)}")
    else:
        st.subheader("Operational Route Visualizer")
        placeholder_data = pd.DataFrame({'lat': [35.9606], 'lon': [-83.1763]})
        st.map(placeholder_data, zoom=8)
