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

# Corrected gradient options with float keys
gradient_options = {
    "Yellow to Red": {0.0: "yellow", 1.0: "red"},
    "Blue to Red": {0.0: "blue", 1.0: "red"},
    "Green to Red": {0.0: "green", 1.0: "red"}
}

try:
    # Use relative path for GitHub compatibility
    file_path = "Landsat8_LST_Winter2025_Normalized.tif"
    
    with rasterio.open(file_path) as src:
        # Read data without cropping
        lst_data = src.read(1)
        transform = src.transform

        # Handle nodata values
        lst_data = np.where(lst_data == src.nodata, np.nan, lst_data)

    # Data processing
    valid_data = lst_data[~np.isnan(lst_data)]
    q1, q3 = np.percentile(valid_data, [25, 75])
    iqr = q3 - q1
    upper_bound = q3 + threshold_multiplier * iqr

    # Convert coordinates to (lat, lon) tuples
    hotspot_points = []
    rows, cols = np.where(lst_data > upper_bound)
    for row, col in zip(rows, cols):
        lon, lat = rasterio.transform.xy(transform, row, col)
        hotspot_points.append((float(lat), float(lon)))  # Ensure float conversion

    # Create Folium map
    m = folium.Map(
        location=[36.2, 43.9],
        zoom_start=10,
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite'
    )

    # Add heatmap with explicit type conversion
    HeatMap(
        data=hotspot_points,
        radius=heatmap_radius,
        gradient=gradient_options[color_gradient],
        min_opacity=0.5,
        max_zoom=12
    ).add_to(m)

    # Display components
    st.subheader("Extreme Hotspots Map")
    st.components.v1.html(m._repr_html_(), height=600)

    # Statistics
    st.subheader("Detection Statistics")
    cols = st.columns(2)
    with cols[0]:
        st.metric("Upper Bound Temperature", f"{upper_bound:.2f}°C")
        st.metric("Total Hotspots Detected", len(hotspot_points))
    with cols[1]:
        st.metric("Threshold Multiplier", f"{threshold_multiplier:.1f}x IQR")
        st.metric("Data Coverage", f"{len(valid_data)/lst_data.size*100:.1f}%")

except Exception as e:
    st.error(f"Processing error: {str(e)}")
