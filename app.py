import streamlit as st
import rasterio
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
import folium
from folium.plugins import HeatMap

# Configure default page settings
st.set_page_config(page_title="LST Hotspot Analyzer", layout="wide")

def main():
    st.title("🌡️ Satellite Thermal Hotspot Analysis System")
    
    # Sidebar navigation with buttons
    st.sidebar.title("Navigation")
    analyzer_button = st.sidebar.button("Analyzer")
    documentation_button = st.sidebar.button("Documentation")
    
    # Display the appropriate tab based on button clicks
    if analyzer_button:
        analyzer_tab()
    elif documentation_button:
        documentation_tab()
    else:
        st.write("Click a button in the sidebar to navigate.")

def analyzer_tab():
    st.subheader("Analyzer")
    # File path handling
    FILE_PATH = "./Landsat8_LST_Winter2025_Normalized.tif"
    
    # Sidebar controls
    with st.sidebar:
        st.header("Analysis Parameters")
        upper_percentile = st.slider(
            "Upper Percentile Limit (%)", 
            75, 100, 95, 1,
            help="Adjust the limit for detecting extreme values as hotspots. \
                  Lower values highlight more extreme hotspots."
        )
        heat_radius = st.slider("Heatmap Radius", 5, 50, 15,
                               help="Visualization intensity radius")
        color_scheme = st.selectbox("Color Scheme", 
                                   ["Viridis", "Plasma", "Inferno", "Magma"],
                                   index=0)

        # Add app developer details
        st.markdown("---")
        st.markdown("**App Details:**")
        st.markdown("Developed by: **Hawkar Ali Abdulhaq**")
        st.markdown("Contact: [ha@releafs.co](mailto:ha@releafs.co)")
        st.markdown("This is a **demo version** designed for real-time applications of geolocation polluters.")

    # Color gradient configuration
    GRADIENTS = {
        "Viridis": {'0.1': '#440154', '0.5': '#21918c', '0.9': '#fde725'},
        "Plasma": {'0.1': '#0d0887', '0.5': '#cc4778', '0.9': '#f0f921'},
        "Inferno": {'0.1': '#000004', '0.5': '#bc3754', '0.9': '#fca50a'},
        "Magma": {'0.1': '#000004', '0.5': '#b73779', '0.9': '#fcffa4'}
    }

    try:
        # Data processing pipeline
        with rasterio.open(FILE_PATH) as src:
            band = src.read(1)
            transform = src.transform
            nodata = src.nodata or -9999
            
            # Convert to float32 for better memory handling
            data = band.astype(np.float32)
            data[data == nodata] = np.nan

        # Statistical analysis
        valid_vals = data[~np.isnan(data)]
        threshold = np.percentile(valid_vals, upper_percentile)

        # Coordinate conversion with type safety
        hotspots = []
        rows, cols = np.where(data > threshold)
        for r, c in zip(rows.astype(int), cols.astype(int)):
            lon, lat = rasterio.transform.xy(transform, r, c)
            hotspots.append([
                float(np.round(lat, 6)),  # Ensure native Python float
                float(np.round(lon, 6))
            ])

        # Visualization
        m = folium.Map(
            location=[36.2, 43.9],
            zoom_start=11,
            tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
            attr="Google Satellite",
            control_scale=True
        )

        if hotspots:
            HeatMap(
                name="Thermal Hotspots",
                data=hotspots,
                radius=heat_radius,
                gradient=GRADIENTS[color_scheme],
                min_opacity=0.3,
                blur=10,
                max_zoom=14
            ).add_to(m)
        else:
            st.warning("No hotspots detected with current parameters")

        # Metrics dashboard
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Upper Threshold Value", f"{threshold:.2f}°C")
        with col2:
            st.metric("Identified Hotspots", f"{len(hotspots):,}")
        with col3:
            st.metric("Data Coverage", 
                     f"{(valid_vals.size/data.size)*100:.1f}%")

        # Map display
        with st.expander("Interactive Thermal Map", expanded=True):
            st.components.v1.html(m._repr_html_(), height=650)

    except Exception as e:
        st.error(f"""
        🚨 Processing Error: {str(e)}
        - Verify file exists at: {FILE_PATH}
        - Check file format (must be GeoTIFF)
        - Ensure coordinate system is WGS84 (EPSG:4326)
        """)
        st.stop()

def documentation_tab():
    st.subheader("📖 Documentation")
    st.markdown("""
    ### Explanation of the Basemap
    The basemap in our application is a satellite image layer that provides a visual reference for the region we are analyzing. It helps users understand where the detected hotspots are located geographically, showing features like roads, buildings, and land cover.

    However, it’s important to note that the basemap is not a live or up-to-date image. It’s a general background map sourced from pre-existing satellite imagery, which means:
    
    - **Static Nature**: The basemap represents a snapshot of the area captured in the past. It may not reflect recent changes, such as new construction, deforestation, or other developments.
    - **Reference Only**: It serves as a guide to help locate hotspots but does not change dynamically with the thermal data we analyze.
    - **No Connection to the Analysis**: The thermal hotspots we detect come from the separate, specialized LST data file (Land Surface Temperature). The basemap is simply a tool for visualization.

    ### Why Use This Basemap?
    - **Clarity**: It’s visually clear and shows landmarks, helping users easily identify locations of hotspots.
    - **Accessibility**: Using a standard satellite basemap ensures the app is lightweight and user-friendly without requiring additional processing power.

    ### Future Improvements
    In future updates, the basemap could be replaced or enhanced with real-time or high-resolution imagery to reflect the most current conditions on the ground. This would provide an even better understanding of the context surrounding the detected hotspots. For now, the basemap remains a practical and helpful tool for navigating and interpreting the thermal data.
    """)

if __name__ == "__main__":
    main()
