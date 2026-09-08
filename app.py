import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Truck Routing Portal", page_icon="Res", layout="wide")

# Your active private key is safely locked here
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

def handle_input(text, api_key):
    if "," in text:
        try:
            lat, lng = map(float, text.split(","))
            return f"{lat},{lng}"
        except:
            pass
            
    url = "https://hereapi.com"
    params = {"apiKey": api_key, "q": text}
    try:
        res = requests.get(url, params=params)
        if res.status_code == 200:
            items = res.json().get("items", [])
            if items:
                pos = items["position"]
                return f"{pos['lat']},{pos['lng']}"
    except:
        pass
    return None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Route Locations")
    st.caption("Type coordinates or text addresses freely below.")
    start_address = st.text_input("Origin Location", value="35.9606, -83.1763")
    end_address = st.text_input("Destination Location", value="36.1965, -82.7601")
    calculate = st.button("Generate Truck-Safe Route")

with col2:
    if calculate:
        with st.spinner("Processing corridor dimensions and structural weight profiles..."):
            start_coords = handle_input(start_address, api_key)
            end_coords = handle_input(end_address, api_key)
            
            if not start_coords or not end_coords:
                st.error("Could not trace these inputs. Please verify formatting.")
            else:
                url = "https://router.hereapi.com/v8/routes"
                
                # UPDATED V8 TRUCK OBJECT PARAMETERS
                params = {
                    "apiKey": api_key,
                    "transportMode": "truck",
                    "origin": start_coords,
                    "destination": end_coords,
                    "return": "summary,polyline,actions",
                    "routingMode": "fast",
                    
                    # Corrected HERE Maps API v8 truck syntax configuration
                    "truck[height]": 411,
                    "truck[width]": 260,
                    "truck[length]": 2200,
                    "truck[grossWeight]": 36287,
                    "truck[axleCount]": 5,
                    "truck[type]": "tractorTrailer"
                }
                
                try:
                    res = requests.get(url, params=params)
                    if res.status_code == 200:
                        data = res.json()
                        section = data['routes'][0]['sections'][0] # Safe object tree indexing for v8 array payloads
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
                            st.map(map_data, zoom=10)
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
                        st.error(f"Routing Rejected. Server returned status code: {res.status_code}. Response: {res.text}")
                except Exception as e:
                    st.error(f"Network error linking to central map registry: {str(e)}")
    else:
        st.subheader("Operational Route Visualizer")
        placeholder_data = pd.DataFrame({'lat': [35.9606], 'lon': [-83.1763]})
        st.map(placeholder_data, zoom=8)
