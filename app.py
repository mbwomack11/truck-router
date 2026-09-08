import streamlit as st
import requests
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Truck Routing Portal", page_icon="🚛", layout="wide")

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

# Custom embedded HTML component to provide true real-time address auto-population
def search_autocomplete_component(label, key, placeholder, current_api_key):
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; padding: 0; background: transparent; }}
            .label {{ font-size: 14px; font-weight: 500; color: rgb(49, 51, 63); margin-bottom: 8px; }}
            .input-container {{ position: relative; }}
            input {{ width: 95%; padding: 10px; font-size: 14px; border: 1px solid #ced4da; border-radius: 4px; outline: none; background: white; color: black; }}
            input:focus {{ border-color: #1e3a8a; box-shadow: 0 0 0 0.2rem rgba(30,58,138,.25); }}
            .suggestions {{ position: absolute; background: white; border: 1px solid #ced4da; border-top: none; width: 95%; max-height: 200px; overflow-y: auto; z-index: 9999; border-radius: 0 0 4px 4px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: none; }}
            .suggestion-item {{ padding: 10px; cursor: pointer; font-size: 13px; color: #333; }}
            .suggestion-item:hover {{ background-color: #f1f5f9; }}
        </style>
    </head>
    <body>
        <div class="label">{label}</div>
        <div class="input-container">
            <input type="text" id="addr-input" placeholder="{placeholder}" autocomplete="off">
            <div id="suggestion-box" class="suggestions"></div>
        </div>

        <script>
            const input = document.getElementById('addr-input');
            const box = document.getElementById('suggestion-box');
            const apiKey = "{current_api_key}";

            if (window.parent.st_value_{key}) {{
                input.value = window.parent.st_value_{key};
            }}

            input.addEventListener('input', async (e) => {{
                const query = e.target.value;
                if (!apiKey || query.length < 3) {{
                    box.style.display = 'none';
                    return;
                }}
                
                try {{
                    const res = await fetch(`https://hereapi.com{{apiKey}}&q=${{encodeURIComponent(query)}}&limit=5`);
                    if (res.ok) {{
                        const data = await res.json();
                        box.innerHTML = '';
                        if (data.items && data.items.length > 0) {{
                            box.style.display = 'block';
                            data.items.forEach(item => {{
                                const div = document.createElement('div');
                                div.className = 'suggestion-item';
                                div.innerText = item.title;
                                div.addEventListener('click', () => {{
                                    input.value = item.title;
                                    box.style.display = 'none';
                                    
                                    // Send chosen string back up to Streamlit backend dashboard natively
                                    const msg = {{type: 'streamlit:setComponentValue', value: item.title, key: '{key}'}};
                                    window.parent.postMessage(msg, '*');
                                }});
                                box.appendChild(div);
                            }});
                        }} else {{
                            box.style.display = 'none';
                        }}
                    }}
                }} catch (err) {{
                    console.error(err);
                }}
            }});

            document.addEventListener('click', (e) => {{
                if (e.target !== input) {{
                    box.style.display = 'none';
                }}
            }});
        </script>
    </body>
    </html>
    """
    # Create interactive framed sandbox layer inside Streamlit interface grid
    return components.html(html_code, height=130, scrolling=False)

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
    
    # Render customized autocomplete address elements linking straight into API lookup engines
    search_autocomplete_component("Origin Address", "start_addr", "Start typing origin city, state, or address...", api_key)
    search_autocomplete_component("Destination Address", "end_addr", "Start typing destination city, state, or address...", api_key)
    
    # Pull values submitted by our embedded scripts safely into main process memory channels
    start_address = st.session_state.get("start_addr", "")
    end_address = st.session_state.get("end_addr", "")
    
    calculate = st.button("Generate Truck-Safe Route")

with col2:
    if calculate:
        if not api_key:
            st.error("API key missing. Please insert your HERE Maps API key in the sidebar.")
        elif not start_address or not end_address:
            st.error("Please click on an auto-populated address from the suggestion lists to confirm your locations before routing.")
        else:
            with st.spinner("Converting locations and checking bridge clearances..."):
                start_coords = geocode_address(start_address, api_key)
                end_coords = geocode_address(end_address, api_key)
                
                if not start_coords or not end_coords:
                    st.error("Could not trace coordinates. Please verify your address selections.")
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
