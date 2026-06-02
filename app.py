import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
import requests

def get_lat_lon(postcode):
    postcode = postcode.replace(" ", "")
    url = f"https://api.postcodes.io/postcodes/{postcode}"

    try:
        res = requests.get(url, timeout=5)

        if res.status_code != 200:
            return None

        data = res.json()
        return data["result"]["latitude"], data["result"]["longitude"]

    except requests.RequestException:
        return None

st.set_page_config(layout="wide")

st.title("ellenor Catchment Area Map")

st.markdown("""
This map shows the merged catchment area for all GP practices included in the organisation.
Search a postcode to check whether it falls within the catchment.
""")

# --- Load GP practices ---
gp_df = pd.read_csv("ellenor GP full address.csv")


# --- LOAD MERGED GEOJSON (no geopandas) ---
with open("merged_boundary.geojson") as f:
    merged_geojson = json.load(f)

# Convert GeoJSON → shapely geometry for analysis
merged_geometry = shape(merged_geojson["features"][0]["geometry"])


# --- Convert postcode to coordinates ---
postcode = st.sidebar.text_input("Enter a postcode to check if location is in catchment area:")

postcode_location = None

if postcode:
    coords = get_lat_lon(postcode)

    if coords is None:
        st.error("Postcode not found")
    else:
        lat, lon = coords
        postcode_location = (lat, lon)

        st.success(f"Postcode found: {postcode.upper()}")

        # ✅ Catchment check
        point = Point(lon, lat)

        if merged_geometry.contains(point):
            st.success("✅ This postcode is INSIDE the catchment area")
        else:
            st.warning("❌ This postcode is OUTSIDE the catchment area")


# --- Create map ---
m = folium.Map(
    location=[gp_df.lat.mean(), gp_df.lon.mean()],
    zoom_start=10
)

# --- ADD CATCHMENT AREA ---
folium.GeoJson(
    merged_geojson,
    name="Catchment Area",
    style_function=lambda x: {
        "fillColor": "blue",
        "color": "blue",
        "weight": 2,
        "fillOpacity": 0.2,
    }
).add_to(m)

# Add GP markers
from folium.plugins import MarkerCluster

cluster = MarkerCluster().add_to(m)

for _, row in gp_df.iterrows():
    folium.Marker(
        [row["lat"], row["lon"]],
        popup=row["GP surgery"],
        icon=folium.Icon(color="green")
    ).add_to(cluster)

# Add organisation marker
org_lat, org_lon = 51.421241, 0.355335  # replace
folium.Marker(
    [org_lat, org_lon],
    popup="ellenor",
    icon=folium.Icon(color="orange")
).add_to(m)

# Add postcode marker to map

if postcode_location:
    folium.Marker(
        postcode_location,
        popup="Searched Postcode",
        icon=folium.Icon(color="purple")
    ).add_to(m)


# --- Legend ---
st.markdown("""
### Map legend
- 🟦 Blue area = Catchment area 
- 🟢 Green markers = GP practices  
- 🟠 Orange marker = ellenor 
- 🟣 Purple marker = Postcode search  
""")

# Display in Streamlit
st_folium(m, width="100%", height=700)