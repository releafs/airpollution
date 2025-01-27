import streamlit as st
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
import folium
from rasterio.mask import mask
from folium.plugins import HeatMap

st.title("Enhanced UX for Extreme Hotspots Detection and Visualization")

# Define the region of interest (ROI) as a polygon
roi_coordinates = [
    [43.81757833693511, 36.36206691158832],
    [43.60746481154448, 36.20487179466631],
    [43.93980123732573, 35.98071126783735],
    [44.02357198927886, 35.9429184506907],
    [44.28037740920073, 36.21373627164827],
    [43.91782858107573, 36.40407948647744],
    [43.81757833693511, 36.36206691158832]
]
roi_polygon = Polygon(roi_coordinates)

# Sidebar controls
st.sidebar.header("Customize Hotspot Detection")
threshold_multiplier = st.sidebar.slider("Threshold Multiplier", 1.0, 3.0, 1.5, step=0.1)
heatmap_radius = st.sidebar.slider("Heatmap Radius", 1, 20, 5)
color_gradient = st.sidebar.radio(
    "Heatmap Color Gradient",
    options=["Yellow to Red", "Blue to Red", "Green to Red"],
    index=0
)

# ... (keep all imports)

# Modified gradient configuration with string keys
gradient_options = {
    "Yellow to Red": {'0': 'yellow', '1': 'red'},
    "Blue to Red": {'0': 'blue', '1': 'red'},
    "Green to Red": {'0': 'green', '1': 'red'}
}

try:
    file_path = "./Landsat8_LST_Winter2025_Normalized.tif"
    
    with rasterio.open(file_path) as src:
        # Read data with explicit dtype conversion
        lst_data = src.read(1).astype(np.float64)
        transform = src.transform

        # Handle nodata using rasterio's built-in masking
        lst_data = np.ma.masked_array(lst_data, mask=(lst_data == src.nodata)).filled(np.nan)

    # Convert coordinates with explicit type casting
    hotspot_points = []
    rows, cols = np.where(lst_data > upper_bound)
    
    for row, col in zip(rows.astype(int), cols.astype(int)):  # Ensure integer indices
        lon, lat = rasterio.transform.xy(transform, row, col)
        # Explicit type conversion to native Python floats
        hotspot_points.append([
            float(lat.item()) if isinstance(lat, np.generic) else float(lat),
            float(lon.item()) if isinstance(lon, np.generic) else float(lon)
        ])

    # Create Folium map with compatibility settings
    m = folium.Map(
        location=[36.2, 43.9],
        zoom_start=10,
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri World Imagery'
    )

    # Add heatmap with validation
    if hotspot_points:
        HeatMap(
            data=hotspot_points,
            radius=heatmap_radius,
            gradient=gradient_options[color_gradient],
            min_opacity=0.6,
            max_zoom=12
        ).add_to(m)
    else:
        st.warning("No hotspots detected with current threshold settings")

    # ... (rest of the code)

except Exception as e:
    st.error(f"Processing error: {str(e)}")
