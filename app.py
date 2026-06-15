import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import json
from shapely.geometry import shape, Point
import requests
from folium.plugins import MarkerCluster

# --- FUNCTION: POSTCODE LOOKUP ---
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


# --- PAGE SETUP ---
st.set_page_config(layout="wide")

st.title("ellenor Catchment Area Map")

st.markdown("""
This map shows:
- DGS GP catchment area
- Bexley GP catchment area
- ellenor location

Search a postcode to check whether it falls within either catchment.
""")

# --- LOAD GP DATA ---
dgs_df = pd.read_csv("DGS GP addresses.csv")
bexley_df = pd.read_csv("Bexley GP addresses.csv")

# --- LOAD GEOJSON FILES ---
with open("merged_boundary_dgs.geojson") as f:
    dgs_geojson = json.load(f)

with open("merged_boundary_bexley.geojson") as f:
    bexley_geojson = json.load(f)

# --- CONVERT TO SHAPELY ---
dgs_geometry = shape(dgs_geojson["features"][0]["geometry"])
bexley_geometry = shape(bexley_geojson["features"][0]["geometry"])

# --- POSTCODE SEARCH ---
postcode = st.sidebar.text_input(
    "Enter a postcode to check if location is in catchment area:"
)

postcode_location = None

if postcode:
    coords = get_lat_lon(postcode)

    if coords is None:
        st.error("Postcode not found")
    else:
        lat, lon = coords
        postcode_location = (lat, lon)

        st.success(f"Postcode found: {postcode.upper()}")

        point = Point(lon, lat)

        # ✅ Check both areas
        in_dgs = dgs_geometry.contains(point)
        in_bexley = bexley_geometry.contains(point)

        if in_dgs or in_bexley:
            st.success("✅ This postcode is INSIDE a catchment area")

            if in_dgs:
                st.info("• Inside DGS catchment")
            if in_bexley:
                st.info("• Inside Bexley catchment")

        else:
            st.warning("❌ This postcode is OUTSIDE both catchment areas")


# --- CREATE MAP ---
m = folium.Map(
    location=[dgs_df.lat.mean(), dgs_df.lon.mean()],
    zoom_start=10
)

# --- ADD DGS CATCHMENT ---
folium.GeoJson(
    dgs_geojson,
    name="DGS Catchment",
    style_function=lambda x: {
        "fillColor": "blue",
        "color": "blue",
        "weight": 2,
        "fillOpacity": 0.2,
    }
).add_to(m)

# --- ADD BEXLEY CATCHMENT ---
folium.GeoJson(
    bexley_geojson,
    name="Bexley Catchment",
    style_function=lambda x: {
        "fillColor": "red",
        "color": "red",
        "weight": 2,
        "fillOpacity": 0.2,
    }
).add_to(m)

# --- MARKER CLUSTERS ---
dgs_cluster = MarkerCluster(name="DGS GP Surgeries").add_to(m)
bexley_cluster = MarkerCluster(name="Bexley GP Surgeries").add_to(m)

# --- ADD DGS GP MARKERS ---
for _, row in dgs_df.iterrows():
    folium.Marker(
        [row["lat"], row["lon"]],
        popup=row["GP surgery"],
        icon=folium.Icon(color="green")
    ).add_to(dgs_cluster)

# --- ADD BEXLEY GP MARKERS ---
for _, row in bexley_df.iterrows():
    folium.Marker(
        [row["lat"], row["lon"]],
        popup=row["GP surgery"],
        icon=folium.Icon(color="blue")
    ).add_to(bexley_cluster)

# --- ADD ORGANISATION MARKER ---
org_lat, org_lon = 51.421241, 0.355335

folium.Marker(
    [org_lat, org_lon],
    popup="ellenor",
    icon=folium.Icon(color="orange")
).add_to(m)

# --- ADD POSTCODE MARKER ---
if postcode_location:
    folium.Marker(
        postcode_location,
        popup="Searched Postcode",
        icon=folium.Icon(color="purple")
    ).add_to(m)

# --- LAYER CONTROL ---
folium.LayerControl().add_to(m)

# --- LEGEND ---
st.markdown("""
### Map legend
- 🟦 Blue area = DGS Catchment  
- 🟥 Red area = Bexley Catchment  
- 🟢 Green markers = DGS GP practices  
- 🔵 Blue markers = Bexley GP practices  
- 🟠 Orange marker = ellenor  
- 🟣 Purple marker = Postcode search  
""")

# --- DISPLAY MAP ---
st_folium(m, width="100%", height=700)
