import streamlit as st
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import Polygon, Point
import folium
from rasterio.mask import mask
from folium.plugins import HeatMap

# Title of the app
st.title("Extreme Hotspots Detection and Visualization")

# Define the GeoTIFF file path in the repository
file_path = "./Landsat8_LST_Winter2025_Normalized.tif"

# Define the region of interest (ROI) as a polygon
roi_coordinates = [
    [43.81757833693511, 36.36206691158832],
    [43.60746481154448, 36.20487179466631],
    [43.93980123732573, 35.98071126783735],
    [44.02357198927886, 35.9429184506907],
    [44.28037740920073, 36.21373627164827],
    [43.91782858107573, 36.40407948647744],
    [43.81757833693511, 36.36206691158832]  # Close the polygon
]
roi_polygon = Polygon(roi_coordinates)

# Sidebar controls for user customization
st.sidebar.header("Customize Hotspot Detection")
threshold_multiplier = st.sidebar.slider("Threshold Multiplier", 1.0, 3.0, 1.5, step=0.1)
heatmap_radius = st.sidebar.slider("Heatmap Radius", 1, 20, 5)
color_gradient = st.sidebar.radio(
    "Heatmap Color Gradient",
    options=["Yellow to Red", "Blue to Red", "Green to Red"],
    index=0
)

# CORRECTED: Use float keys in gradient definition
gradient_options = {
    "Yellow to Red": {0.0: "yellow", 1.0: "red"},
    "Blue to Red": {0.0: "blue", 1.0: "red"},
    "Green to Red": {0.0: "green", 1.0: "red"}
}
# Open the GeoTIFF file
try:
    with rasterio.open(file_path) as src:
        # Extract metadata
        metadata = src.meta
        bounds = src.bounds
        transform = src.transform

        # Read the data and clip it to ROI
        shapes = [roi_polygon]
        lst_data_clipped, transform_clipped = mask(src, shapes, crop=True, nodata=np.nan)
        lst_data_clipped = lst_data_clipped[0]

        # Check for valid `nodata` value and handle it
        nodata_value = src.nodata
        if nodata_value is not None and np.isscalar(nodata_value):
            lst_data_clipped = np.where(lst_data_clipped == nodata_value, np.nan, lst_data_clipped)

    # Ensure valid data is available
    valid_data = lst_data_clipped[~np.isnan(lst_data_clipped)]
    if valid_data.size == 0:
        st.error("No valid data available in the selected region. Please check the GeoTIFF file or region of interest.")
        st.stop()

    # Detect extreme hotspots using the customized threshold
    q1 = np.percentile(valid_data, 25)  # First quartile
    q3 = np.percentile(valid_data, 75)  # Third quartile
    iqr = q3 - q1  # Interquartile range
    upper_bound = q3 + threshold_multiplier * iqr  # Upper bound based on user-defined multiplier

    # Identify extreme hotspots
    hotspots_map = np.where(lst_data_clipped > upper_bound, 1, 0)

    # Convert extreme hotspots to polygons for visualization
    hotspot_polygons = []
    for row in range(hotspots_map.shape[0]):
        for col in range(hotspots_map.shape[1]):
            if hotspots_map[row, col] == 1:
                x, y = rasterio.transform.xy(transform_clipped, row, col, offset="center")
                hotspot_polygons.append(Point(x, y))

    gdf_hotspots = gpd.GeoDataFrame(geometry=hotspot_polygons, crs="EPSG:4326")

    # Print statistics
    st.write("Extreme Hotspot Detection Statistics:")
    st.write(f"Threshold Multiplier: {threshold_multiplier:.2f}")
    st.write(f"Upper Bound for Hotspots: {upper_bound:.2f}")
    st.write(f"Number of Extreme Hotspots: {len(hotspot_polygons)}")
    st.write(f"Percentage of Hotspots: {len(hotspot_polygons) / len(valid_data) * 100:.2f}%")

    # Create a Folium map with a satellite basemap
    m = folium.Map(
        location=[36.2, 43.9],
        zoom_start=10,
        tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
        attr='Google Satellite',
        control_scale=True
    )

    # Add the hotspots to the map as a heatmap with user-selected gradient
    HeatMap(
        data=[[point.y, point.x] for point in hotspot_polygons],
        radius=heatmap_radius,
        gradient=gradient_options[color_gradient],
    ).add_to(m)

    # Display the map
    st.subheader("Extreme Hotspots Map")
    st.components.v1.html(m._repr_html_(), height=600)

except Exception as e:
    st.error(f"An error occurred while processing the file: {e}")
