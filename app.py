import streamlit as st
import geopandas as gpd
import pandas as pd
import glob
from shapely.ops import unary_union
import folium
from streamlit_folium import st_folium

st.set_page_config(layout="wide")

st.title("ellenor Catchment Area Map")

st.markdown("""
This map shows the merged catchment area for all GP practices included in the organisation.
Use the filters to explore specific practices or search a postcode to check coverage.
""")

# --- Load GP practices ---
gp_df = pd.read_csv("ellenor GP postcodes.csv")


# Add postcode input
from geopy.geocoders import Nominatim

geolocator = Nominatim(user_agent="geo_app")

postcode = st.sidebar.text_input("Enter a postcode to check location:")

# Convert postcode to coordinates
postcode_location = None

if postcode:
    try:
        location = geolocator.geocode(postcode)
        if location:
            postcode_location = (location.latitude, location.longitude)
            st.success(f"Found location: {location.address}")
        else:
            st.error("Postcode not found.")
    except:
        st.error("Error looking up postcode.")

# --- Load boundary files ---
files = glob.glob("GP boundary files/*.geojson")

gdfs = [gpd.read_file(f) for f in files]
all_boundaries = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True))

# Ensure CRS
all_boundaries = all_boundaries.to_crs(epsg=4326)

# Merge boundaries
merged_geometry = unary_union(all_boundaries.geometry)
merged_gdf = gpd.GeoDataFrame(geometry=[merged_geometry], crs="EPSG:4326")

# Check if postcode is inside catchment
from shapely.geometry import Point

if postcode_location:
    point = Point(postcode_location[1], postcode_location[0])  # lon, lat

    if merged_geometry.contains(point):
        st.success("✅ This postcode is INSIDE the catchment area")
    else:
        st.warning("❌ This postcode is OUTSIDE the catchment area")

# --- Create map ---
m = folium.Map(
    location=[gp_df.Latitude.mean(), gp_df.Longitude.mean()],
    zoom_start=10
)

# Add merged boundary
folium.GeoJson(
    merged_gdf,
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