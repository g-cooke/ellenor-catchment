import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
from geopy.geocoders import Nominatim
from shapely.geometry import shape, Point

st.set_page_config(layout="wide")

st.title("ellenor Catchment Area Map")

st.markdown("""
This map shows the merged catchment area for all GP practices included in the organisation.
Search a postcode to check whether it falls within the catchment.
""")

# --- Load GP practices ---
gp_df = pd.read_csv("ellenor GP postcodes.csv")


# --- LOAD MERGED GEOJSON (no geopandas) ---
with open("merged_boundary.geojson") as f:
    merged_geojson = json.load(f)

# Convert GeoJSON → shapely geometry for analysis
merged_geometry = shape(merged_geojson["features"][0]["geometry"])


# --- Convert postcode to coordinates ---
geolocator = Nominatim(user_agent="geo_app")

postcode = st.sidebar.text_input("Enter a postcode to check if location is in catchment area:")

postcode_location = None

if postcode:
    location = geolocator.geocode(postcode)

    if location:
        postcode_location = (location.latitude, location.longitude)

        st.success(f"Found location: {location.address}")

        # ✅ Catchment check
        point = Point(location.longitude, location.latitude)

        if merged_geometry.contains(point):
            st.success("✅ This postcode is INSIDE the catchment area")
        else:
            st.warning("❌ This postcode is OUTSIDE the catchment area")

    else:
        st.error("Postcode not found")

# --- Create map ---
m = folium.Map(
    location=[gp_df.Latitude.mean(), gp_df.Longitude.mean()],
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
        [row["Latitude"], row["Longitude"]],
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