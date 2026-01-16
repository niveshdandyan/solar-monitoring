"""
🌞 Solar Panel Monitoring System
A comprehensive analysis and visualization tool for solar panel performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
from datetime import datetime

# Import custom modules
from modules.data_parser import (
    parse_data, 
    prepare_analysis_data, 
    detect_all_columns,
    get_available_columns,
    get_extra_columns
)
from modules.calculations import (
    calculate_power,
    calculate_expected_power,
    calculate_daily_metrics,
    calculate_monthly_metrics,
    calculate_performance_ratio,
    calculate_performance_ratio,
    get_all_anomalies,
    filter_anomalous_data
)
from modules.visualizations import (
    plot_daily_power_irradiance,
    plot_daily_power_irradiance_soc,
    plot_daily_temperature_effect,
    plot_daily_voltage_irradiance,
    plot_daily_current_irradiance,
    plot_monthly_hourly_power_irradiance,
    plot_monthly_hourly_power_irradiance_soc,
    plot_monthly_hourly_voltage_irradiance,
    plot_monthly_hourly_current_irradiance,
    plot_custom_range_hourly_power_irradiance,
    plot_custom_range_hourly_power_irradiance_soc,
    plot_custom_range_hourly_voltage_irradiance,
    plot_custom_range_hourly_current_irradiance,
    plot_selected_dates_hourly_power_irradiance,
    plot_selected_dates_hourly_power_irradiance_soc,
    plot_selected_dates_hourly_voltage_irradiance,
    plot_selected_dates_hourly_current_irradiance,
    plot_pr_trend,
    plot_specific_yield_trend,
    plot_expected_vs_actual,
    plot_monthly_summary,
    plot_temperature_effect_scatter,
    generate_all_daily_graphs,
    generate_all_monthly_graphs,
    plot_calendar_heatmap,
    plot_daily_summary_cards,
    detect_daily_anomalies,
    get_anomaly_summary,
    detect_power_anomalies,
    plot_power_anomaly_scatter,
    plot_power_anomaly_timeline
)
from modules.export import (
    get_export_directory,
    list_exported_files,
    create_zip_archive,
    clean_export_directory,
    get_export_summary,
    export_dataframe_to_csv
)
from modules.visualizations import (
    generate_all_daily_graphs,
    generate_all_monthly_graphs,
    generate_custom_export_graphs
)
from modules.data_quality import (
    check_data_completeness,
    validate_data_ranges,
    fill_data_gaps,
    detect_duplicates,
    get_data_quality_report
)
from modules.weather_api import (
    extract_coordinates_from_url,
    fetch_weather_data,
    merge_weather_with_solar,
    fetch_standalone_weather_data
)
from modules.weather_visualizations import (
    plot_weather_daily_irradiance,
    plot_weather_daily_temperature,
    plot_weather_monthly_avg_irradiance,
    plot_weather_monthly_avg_temperature,
    plot_weather_daily_summary,
    plot_weather_calendar_month_averages
)

# Page configuration
st.set_page_config(
    page_title="🌞 Solar Panel Monitoring",
    page_icon="🌞",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
    }
    .stMetric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeeba;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'analysis_df' not in st.session_state:
    st.session_state.analysis_df = None
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = None
if 'daily_metrics' not in st.session_state:
    st.session_state.daily_metrics = None
if 'monthly_metrics' not in st.session_state:
    st.session_state.monthly_metrics = None
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = 'data_analysis'  # 'data_analysis' or 'weather_analysis'

# Get export directory
EXPORT_DIR = get_export_directory(os.path.join(os.path.dirname(__file__), "exports"))


def main():
    # Header
    st.markdown('<h1 class="main-header">🌞 Solar Panel Monitoring System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive Performance Analysis & Visualization</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Configuration")
        
        # View mode toggle
        st.markdown("---")
        col_view1, col_view2 = st.columns(2)
        with col_view1:
            if st.button("📊 Data Analysis", use_container_width=True, 
                        type="primary" if st.session_state.view_mode == 'data_analysis' else "secondary"):
                st.session_state.view_mode = 'data_analysis'
                st.rerun()
        with col_view2:
            if st.button("🌤️ Weather Tool", use_container_width=True,
                        type="primary" if st.session_state.view_mode == 'weather_analysis' else "secondary"):
                st.session_state.view_mode = 'weather_analysis'
                st.rerun()
        
        st.markdown("---")
        st.subheader("📊 System Parameters")
        
        # User inputs for system constants
        nominal_power = st.number_input(
            "Nominal Power at STC (kWp)",
            min_value=0.001,
            max_value=1000.0,
            value=5.0,
            step=0.1,
            help="Your system's rated power at Standard Test Conditions (1000 W/m², 25°C)"
        )
        
        temp_coeff = st.number_input(
            "Power Temperature Coefficient (%/°C)",
            min_value=-1.0,
            max_value=0.0,
            value=-0.4,
            step=0.01,
            help="Typically -0.3% to -0.5% for silicon panels"
        )
        temp_coeff_decimal = temp_coeff / 100  # Convert to decimal
        
        st.markdown("---")
        st.subheader("🔧 Analysis Settings")
        
        soc_threshold = st.slider(
            "SoC Threshold for PR (%)",
            min_value=80,
            max_value=100,
            value=95,
            help="Exclude data points where SoC is above this threshold from PR calculation"
        )
        
        st.markdown("---")
        st.subheader("📊 Data Filtering Settings")
        st.caption("Filter out anomalous timestamps with high irradiance but no power output")
        
        irradiance_filter_threshold = st.number_input(
            "Irradiance Threshold (W/m²)",
            min_value=0.0,
            max_value=1000.0,
            value=50.0,
            step=10.0,
            help="Minimum irradiance to consider as 'should be producing power'. Timestamps with irradiance above this but zero power may be filtered."
        )
        
        power_filter_threshold = st.number_input(
            "Power Threshold (W)",
            min_value=0.0,
            max_value=100.0,
            value=0.0,
            step=1.0,
            help="Maximum power to consider as 'not producing'. Default is 0W."
        )
        
        soc_low_threshold = st.slider(
            "Low SoC Threshold (%)",
            min_value=50,
            max_value=100,
            value=95,
            help="Only filter data when SoC is below this (if SoC data available). This avoids filtering battery-full curtailment situations."
        )
        
        st.markdown("---")
        st.subheader("🌅 Daytime Definition")
        
        use_dynamic_sunrise = st.checkbox(
            "Use sunrise/sunset from weather data",
            value=False,
            key="use_dynamic_sunrise",
            help="If enabled and weather data is fetched, uses actual sunrise/sunset times. Otherwise defaults to 6 AM - 6 PM."
        )
        
        if not use_dynamic_sunrise:
            col_day1, col_day2 = st.columns(2)
            with col_day1:
                daytime_start = st.number_input(
                    "Daytime Start Hour",
                    min_value=0,
                    max_value=12,
                    value=6,
                    key="daytime_start_hour",
                    help="Hour when daytime begins (default: 6 AM)"
                )
            with col_day2:
                daytime_end = st.number_input(
                    "Daytime End Hour",
                    min_value=12,
                    max_value=23,
                    value=18,
                    key="daytime_end_hour",
                    help="Hour when daytime ends (default: 6 PM)"
                )
            st.session_state['daytime_start'] = daytime_start
            st.session_state['daytime_end'] = daytime_end
        else:
            st.session_state['daytime_start'] = None
            st.session_state['daytime_end'] = None
            st.info("📍 Daytime will be determined from sunrise/sunset data when weather is fetched.")
    
        # Default constants for anomaly detection (UI removed)
        vmpp = 30.0
        impp = 8.0
        
        st.markdown("---")
        st.subheader("📁 Upload Data")
        
        uploaded_file = st.file_uploader(
            "Upload CSV File",
            type=['csv', 'txt'],
            help="Upload your solar data in CSV format"
        )
        
        # Text paste option
        st.markdown("**Or paste data directly:**")
        text_data = st.text_area(
            "Paste CSV Data",
            height=150,
            placeholder="Timestamp,Current,Voltage,Irradiance,Temperature,SoC\n2024-01-01 08:00,5.2,32.1,450,28,45\n..."
        )
        
        process_btn = st.button("🚀 Process Data", type="primary", use_container_width=True)

        st.markdown("---")
        st.subheader("🌤️ Weather Data (Optional)")
        
        # Location input - either lat/long or URL
        location_mode = st.radio("Location Input", ["Lat/Long", "Google Maps URL"], horizontal=True, label_visibility="collapsed")
        
        lat_val, lon_val = 0.0, 0.0
        
        if location_mode == "Google Maps URL":
            map_url = st.text_input("Google Maps URL", help="Paste a Google Maps link to extract coordinates")
            if st.button("📍 Parse URL"):
                p_lat, p_lon = extract_coordinates_from_url(map_url)
                if p_lat is not None:
                    lat_val, lon_val = p_lat, p_lon
                    st.success(f"Found: {lat_val:.4f}, {lon_val:.4f}")
                    st.session_state['matched_coords'] = (lat_val, lon_val)
                else:
                    st.error("Could not extract coordinates from URL")
            
            # Use stored coords if available
            if 'matched_coords' in st.session_state:
                lat_val, lon_val = st.session_state['matched_coords']
        
        col_lat, col_lon = st.columns(2)
        with col_lat:
            latitude = st.number_input("Latitude", value=lat_val, format="%.4f", min_value=-90.0, max_value=90.0)
        with col_lon:
            longitude = st.number_input("Longitude", value=lon_val, format="%.4f", min_value=-180.0, max_value=180.0)
            
        fetch_weather = st.button("☁️ Fetch Weather Data", use_container_width=True)
        
        if fetch_weather:
             if not st.session_state.data_loaded:
                 st.warning("Please process solar data first!")
             else:
                 with st.spinner("Fetching weather data..."):
                     # Get date range from loaded data
                     df = st.session_state.analysis_df
                     if 'Timestamp' in df.columns:
                         start_date = df['Timestamp'].min()
                         end_date = df['Timestamp'].max()
                         
                         weather_df = fetch_weather_data(latitude, longitude, start_date, end_date)
                         
                         if weather_df is not None:
                             # Merge
                             merged_df, msgs = merge_weather_with_solar(df, weather_df)
                             
                             # Re-run calculations with new data
                             if 'Current_A' in merged_df.columns and 'Voltage_V' in merged_df.columns:
                                 merged_df = calculate_power(merged_df)
                             
                             # Recalculate metrics
                             daytime_start = st.session_state.get('daytime_start', 6) or 6
                             daytime_end = st.session_state.get('daytime_end', 18) or 18
                             
                             daily_metrics = calculate_daily_metrics(
                                 merged_df, nominal_power, temp_coeff_decimal,
                                 daytime_start=daytime_start, daytime_end=daytime_end
                             )
                             monthly_metrics = calculate_monthly_metrics(
                                 merged_df, nominal_power, temp_coeff_decimal,
                                 daytime_start=daytime_start, daytime_end=daytime_end
                             )
                             
                             # Update session state
                             st.session_state.analysis_df = merged_df
                             st.session_state.daily_metrics = daily_metrics
                             st.session_state.monthly_metrics = monthly_metrics
                             
                             st.success("✅ Weather data merged successfully!")
                             st.rerun()
                         else:
                             st.error("Failed to fetch weather data")
                     else:
                         st.error("Could not determine date range from data")

    
    # Main content area
    if process_btn:
        # Process the data
        data_source = None
        if uploaded_file is not None:
            data_source = uploaded_file
        elif text_data.strip():
            data_source = text_data
        
        if data_source is None:
            st.error("⚠️ Please upload a file or paste data to process.")
        else:
            with st.spinner("Processing data..."):
                try:
                    # Parse data
                    raw_df, column_mapping, messages = parse_data(data_source)
                    
                    # Display detection results
                    st.subheader("📋 Column Detection Results")
                    
                    cols = st.columns(3)
                    for i, (col_type, msg) in enumerate(messages.items()):
                        with cols[i % 3]:
                            if "✅" in msg:
                                st.success(msg)
                            elif "⚠️" in msg:
                                st.warning(msg)
                            elif "🔄" in msg:
                                st.info(msg)
                            else:
                                st.info(msg)
                    
                    # Prepare analysis data
                    analysis_df = prepare_analysis_data(raw_df, column_mapping)
                    
                    # Calculate power if we have current and voltage
                    if 'Current_A' in analysis_df.columns and 'Voltage_V' in analysis_df.columns:
                        analysis_df = calculate_power(analysis_df)
                    
                    # Calculate expected power if we have irradiance
                    if 'Irradiance_Wm2' in analysis_df.columns:
                        analysis_df = calculate_expected_power(
                            analysis_df, 
                            nominal_power, 
                            temp_coeff_decimal
                        )
                    
                    # Calculate metrics
                    # Retrieve daytime settings
                    daytime_start = st.session_state.get('daytime_start', 6) or 6
                    daytime_end = st.session_state.get('daytime_end', 18) or 18
                    
                    # Calculate metrics
                    daily_metrics = calculate_daily_metrics(
                        analysis_df, 
                        nominal_power, 
                        temp_coeff_decimal,
                        daytime_start=daytime_start,
                        daytime_end=daytime_end
                    )
                    monthly_metrics = calculate_monthly_metrics(
                        analysis_df, 
                        nominal_power, 
                        temp_coeff_decimal,
                        daytime_start=daytime_start,
                        daytime_end=daytime_end
                    )
                    
                    # Store in session state
                    st.session_state.data_loaded = True
                    st.session_state.analysis_df = analysis_df
                    st.session_state.column_mapping = column_mapping
                    st.session_state.daily_metrics = daily_metrics
                    st.session_state.monthly_metrics = monthly_metrics
                    st.session_state.nominal_power = nominal_power
                    st.session_state.temp_coeff = temp_coeff_decimal
                    st.session_state.soc_threshold = soc_threshold
                    st.session_state.irradiance_filter_threshold = irradiance_filter_threshold
                    st.session_state.power_filter_threshold = power_filter_threshold
                    st.session_state.soc_low_threshold = soc_low_threshold
                    
                    st.success("✅ Data processed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing data: {str(e)}")
                    st.exception(e)
    # View mode conditional display
    if st.session_state.view_mode == 'weather_analysis':
        # Weather Analysis Mode - Full screen dedicated view
        st.markdown("## 🌤️ Standalone Weather Analysis")
        st.caption("*Analyze historical weather data for any location - useful for site selection and solar potential analysis.*")
        display_weather_analysis(EXPORT_DIR)
    else:
        # Data Analysis Mode - Show uploaded data analysis
        if st.session_state.data_loaded:
            display_analysis_results(vmpp, impp)
        else:
            st.info("👆 **Upload your solar data** using the sidebar to begin analysis.")
            st.markdown("""
            ### 🚀 Quick Start
            1. Configure your **system parameters** (Nominal Power, Temperature Coefficient)
            2. **Upload a CSV file** or paste data directly
            3. Click **🚀 Process Data** to analyze
            
            ---
            
            💡 **Tip:** Use the **🌤️ Weather Tool** button above to explore historical weather data for any location without uploading solar data.
            """)


def display_analysis_results(vmpp: float, impp: float):
    """Display all analysis results and visualizations."""
    
    analysis_df = st.session_state.analysis_df
    daily_metrics = st.session_state.daily_metrics
    monthly_metrics = st.session_state.monthly_metrics
    nominal_power = st.session_state.nominal_power
    temp_coeff = st.session_state.temp_coeff
    soc_threshold = st.session_state.soc_threshold
    
    # Get filtering thresholds (with defaults for backward compatibility)
    irradiance_filter_threshold = st.session_state.get('irradiance_filter_threshold', 50.0)
    power_filter_threshold = st.session_state.get('power_filter_threshold', 0.0)
    soc_low_threshold = st.session_state.get('soc_low_threshold', 20)
    
    # Overview metrics
    st.subheader("📊 Performance Overview")
    
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    
    with col1:
        if 'Actual_Energy_kWh' in daily_metrics.columns:
            total_energy = daily_metrics['Actual_Energy_kWh'].sum()
            st.metric("Total Energy", f"{total_energy:.2f} kWh")
    
    with col2:
        if 'PR_pct' in daily_metrics.columns:
            avg_pr = daily_metrics['PR_pct'].mean()
            st.metric("Average PR", f"{avg_pr:.1f}%")
    
    with col3:
        if 'Specific_Yield_kWhkWp' in daily_metrics.columns:
            total_yield = daily_metrics['Specific_Yield_kWhkWp'].sum()
            st.metric("Specific Yield", f"{total_yield:.2f} kWh/kWp")
    
    with col4:
        if 'Date' in daily_metrics.columns:
            days = len(daily_metrics)
            st.metric("Days Analyzed", f"{days}")
    
    with col5:
        if 'High_SoC_Points' in daily_metrics.columns:
            excluded = daily_metrics['High_SoC_Points'].sum()
            st.metric("High SoC Points", f"{excluded}")
    
    with col6:
        if 'Anomalous_Points' in daily_metrics.columns:
            anomalous = daily_metrics['Anomalous_Points'].sum()
            st.metric("Anomalous Points", f"{int(anomalous)}", help="Timestamps with high irradiance but zero power")
    
    st.markdown("---")
    
    # Data Preview
    with st.expander("📋 Data Preview", expanded=False):
        st.dataframe(analysis_df.head(100), use_container_width=True)
    
    # Daily Metrics Table
    with st.expander("📅 Daily Metrics", expanded=False):
        st.dataframe(daily_metrics, use_container_width=True)
    
    # Monthly Metrics Table
    if len(monthly_metrics) > 0:
        with st.expander("📆 Monthly Metrics", expanded=False):
            st.dataframe(monthly_metrics, use_container_width=True)
    
    st.markdown("---")
    
    # Tabs for different visualizations
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
        "📈 Daily Graphs", 
        "📊 Monthly Graphs",
        "📅 Calendar View",
        "📆 Custom Range",
        "📈 PR & Yield Analysis", 
        "🌡️ Temperature Effects",
        "📋 Data Quality",
        "⚠️ Power Anomalies",
        "� Custom Metrics",
        "�💾 Export All"
    ])
    
    with tab1:
        display_daily_graphs(analysis_df, EXPORT_DIR)
    
    with tab2:
        display_monthly_graphs(analysis_df, EXPORT_DIR)
    
    with tab3:
        display_calendar_view(analysis_df, daily_metrics)
    
    with tab4:
        display_custom_range_graphs(analysis_df, EXPORT_DIR)
    
    with tab5:
        display_pr_yield_graphs(analysis_df, daily_metrics, monthly_metrics, EXPORT_DIR)
    
    with tab6:
        display_temperature_graphs(analysis_df, EXPORT_DIR)
    
    with tab7:
        display_data_quality(analysis_df)
    
    with tab8:
        display_power_anomalies(analysis_df, EXPORT_DIR)
    
    with tab9:
        display_custom_metrics(analysis_df, st.session_state.column_mapping, EXPORT_DIR)
    
    with tab10:
        display_export_section(analysis_df, daily_metrics, monthly_metrics, EXPORT_DIR)


def display_daily_graphs(analysis_df: pd.DataFrame, export_dir: str):
    """Display daily graphs with date selection."""
    
    st.subheader("📈 Daily Performance Graphs")
    
    if 'Date' not in analysis_df.columns:
        st.warning("Date information not available in the data.")
        return
    
    # Date selection
    unique_dates = sorted(analysis_df['Date'].unique())
    
    if len(unique_dates) == 0:
        st.warning("No dates found in the data.")
        return
    
    selected_date = st.selectbox(
        "Select Date",
        options=unique_dates,
        format_func=lambda x: str(x)
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Power & Irradiance")
        fig = plot_daily_power_irradiance(analysis_df, str(selected_date), export_dir, show_plot=True)
        if fig:
            st.pyplot(fig)
        else:
            st.info("Insufficient data for this graph.")
    
    with col2:
        if 'SoC_pct' in analysis_df.columns:
            st.markdown("#### Power, Irradiance & SoC")
            fig = plot_daily_power_irradiance_soc(analysis_df, str(selected_date), export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Battery SoC data not available.")
    
    # Second row: Voltage and Current graphs
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        if 'Voltage_V' in analysis_df.columns:
            st.markdown("#### Voltage & Irradiance")
            fig = plot_daily_voltage_irradiance(analysis_df, str(selected_date), export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Voltage data not available.")
    
    with col4:
        if 'Current_A' in analysis_df.columns:
            st.markdown("#### Current & Irradiance")
            fig = plot_daily_current_irradiance(analysis_df, str(selected_date), export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Current data not available.")


def display_monthly_graphs(analysis_df: pd.DataFrame, export_dir: str):
    """Display monthly hourly-averaged graphs with month selection."""
    
    st.subheader("📊 Monthly Performance Graphs (Hourly Averages)")
    
    st.info("These graphs show the **average values at each hour** across all days in the selected month. For example, the value at 10:00 represents the average of all readings taken at 10:00 throughout the month.")
    
    if 'Month' not in analysis_df.columns:
        st.warning("Month information not available in the data.")
        return
    
    # Month selection
    unique_months = sorted(analysis_df['Month'].astype(str).unique())
    
    if len(unique_months) == 0:
        st.warning("No months found in the data.")
        return
    
    col_sel1, col_sel2 = st.columns([2, 1])
    with col_sel1:
        selected_month = st.selectbox(
            "Select Month",
            options=unique_months,
            format_func=lambda x: str(x),
            key="monthly_graphs_month"
        )
    
    with col_sel2:
        data_mode = st.radio(
            "Data Mode",
            options=["All Data", "Filtered Data"],
            horizontal=True,
            key="monthly_data_mode",
            help="Filtered Data excludes different anomalous timestamps (high irradiance, zero power)"
        )
    
    # Get filtering thresholds from session state
    irradiance_threshold = st.session_state.get('irradiance_filter_threshold', 50.0)
    power_threshold = st.session_state.get('power_filter_threshold', 0.0)
    soc_low_threshold = st.session_state.get('soc_low_threshold', 20)
    
    # Get daytime settings (default to 6-18 if not set or dynamic mode enabled but no weather data yet)
    daytime_start = st.session_state.get('daytime_start')
    daytime_end = st.session_state.get('daytime_end')
    
    if daytime_start is None: daytime_start = 6
    if daytime_end is None: daytime_end = 18

    # Determine if filtering should be used
    use_filtering = (data_mode == "Filtered Data")
    
    # Import the averaging function that supports filtering
    from modules.visualizations import calculate_monthly_hourly_averages
    
    # First row: Power graphs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Avg Power & Irradiance")
        fig = plot_monthly_hourly_power_irradiance(
            analysis_df, str(selected_month), export_dir, show_plot=True,
            filter_anomalous=use_filtering,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold,
            daytime_start=daytime_start,
            daytime_end=daytime_end
        )
        if fig:
            st.pyplot(fig)
        else:
            st.info("Insufficient data for this graph.")
    
        if 'SoC_pct' in analysis_df.columns:
            st.markdown("#### Avg Power, Irradiance & SoC")
            fig = plot_monthly_hourly_power_irradiance_soc(
                analysis_df, str(selected_month), export_dir, show_plot=True,
                filter_anomalous=use_filtering,
                irradiance_threshold=irradiance_threshold,
                power_threshold=power_threshold,
                soc_low_threshold=soc_low_threshold,
                daytime_start=daytime_start,
                daytime_end=daytime_end
            )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Battery SoC data not available.")
    
    # Second row: Voltage and Current graphs
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        if 'Voltage_V' in analysis_df.columns:
            st.markdown("#### Avg Voltage & Irradiance")
            fig = plot_monthly_hourly_voltage_irradiance(
                analysis_df, str(selected_month), export_dir, show_plot=True,
                filter_anomalous=use_filtering,
                irradiance_threshold=irradiance_threshold,
                power_threshold=power_threshold,
                soc_low_threshold=soc_low_threshold
            )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Voltage data not available.")
    
    with col4:
        if 'Current_A' in analysis_df.columns:
            st.markdown("#### Avg Current & Irradiance")
            fig = plot_monthly_hourly_current_irradiance(
                analysis_df, str(selected_month), export_dir, show_plot=True,
                filter_anomalous=use_filtering,
                irradiance_threshold=irradiance_threshold,
                power_threshold=power_threshold,
                soc_low_threshold=soc_low_threshold
            )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Current data not available.")
    
    # Show comparison section if filtering is enabled
    if use_filtering:
        st.markdown("---")
        st.markdown("### 📊 Filtered Data Analysis")
        
        # Calculate filtered hourly averages to show stats
        hourly_avg_filtered, filter_info = calculate_monthly_hourly_averages(
            analysis_df, str(selected_month),
            filter_anomalous=True,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold
        )
        
        # Show filter summary
        if filter_info.get('rows_excluded', 0) > 0:
            st.info(f"""
            📋 **Filtering Summary for {selected_month}**: Excluded **{filter_info['rows_excluded']:,}** of **{filter_info['rows_total']:,}** data points ({filter_info['exclusion_pct']:.1f}%)
            
            *Filter criteria: Irradiance > {irradiance_threshold} W/m², Power ≤ {power_threshold} W, SoC < {soc_low_threshold}%*
            """)
        else:
            st.success("No anomalous data points found for this month.")
        
        # Show filtered power graphs
        if len(hourly_avg_filtered) > 0 and 'Power_W' in hourly_avg_filtered.columns:
            col5, col6 = st.columns(2)
            
            with col5:
                st.markdown("#### Avg Power & Irradiance (Filtered)")
                # Create a simple comparison plot
                import matplotlib.pyplot as plt
                
                hourly_avg_all, _ = calculate_monthly_hourly_averages(analysis_df, str(selected_month))
                
                if len(hourly_avg_all) > 0:
                    fig, ax = plt.subplots(figsize=(14, 7))
                    ax.plot(hourly_avg_all['Hour'], hourly_avg_all['Power_W'], 
                           'b-', linewidth=2, label='All Data', marker='o')
                    ax.plot(hourly_avg_filtered['Hour'], hourly_avg_filtered['Power_W'], 
                           'g-', linewidth=2, label='Filtered', marker='s')
                    ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
                    ax.set_ylabel('Average Power (W)', fontsize=12, fontweight='bold')
                    ax.set_title(f'Power Comparison - {selected_month}', fontsize=14, fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)
                    plt.close(fig)
            
            with col6:
                # Show difference statistics
                st.markdown("#### Difference Summary")
                if len(hourly_avg_all) > 0:
                    avg_power_all = hourly_avg_all['Power_W'].mean()
                    avg_power_filtered = hourly_avg_filtered['Power_W'].mean()
                    power_diff = avg_power_filtered - avg_power_all
                    power_diff_pct = (power_diff / avg_power_all * 100) if avg_power_all > 0 else 0
                    
                    st.metric("Avg Power (All Data)", f"{avg_power_all:.1f} W")
                    st.metric("Avg Power (Filtered)", f"{avg_power_filtered:.1f} W", 
                             delta=f"{power_diff_pct:+.1f}%")


def display_custom_range_graphs(analysis_df: pd.DataFrame, export_dir: str):
    """Display custom date range hourly-averaged graphs with date selection."""
    
    st.subheader("📆 Custom Range Performance Graphs (Hourly Averages)")
    
    if 'Date' not in analysis_df.columns:
        st.warning("Date information not available in the data.")
        return
    
    unique_dates = sorted(analysis_df['Date'].unique())
    
    if len(unique_dates) == 0:
        st.warning("No dates found in the data.")
        return
    
    min_date = unique_dates[0]
    max_date = unique_dates[-1]
    
    # Selection mode toggle
    selection_mode = st.radio(
        "Selection Mode",
        options=["Date Range", "Specific Dates"],
        horizontal=True,
        help="Choose whether to select a continuous date range or pick specific individual dates"
    )
    
    selected_dates = []
    
    if selection_mode == "Date Range":
        st.info("Select a **start and end date** to see hourly averages across all days in that range.")
        
        col_start, col_end = st.columns(2)
        
        with col_start:
            start_date = st.date_input(
                "Start Date",
                value=min_date,
                min_value=min_date,
                max_value=max_date,
                key="custom_range_start"
            )
        
        with col_end:
            end_date = st.date_input(
                "End Date",
                value=max_date,
                min_value=min_date,
                max_value=max_date,
                key="custom_range_end"
            )
        
        if start_date > end_date:
            st.error("Start date must be before or equal to end date.")
            return
        
        days_in_range = (end_date - start_date).days + 1
        st.caption(f"📅 Selected range: **{days_in_range} days** ({start_date} to {end_date})")
        
        # For date range, we use the existing range functions
        use_range_mode = True
        
    else:  # Specific Dates
        st.info("Select **specific dates** (hold Ctrl/Cmd to select multiple) to see hourly averages across just those days.")
        
        # Format dates nicely for display
        date_options = [str(d) for d in unique_dates]
        
        selected_date_strs = st.multiselect(
            "Select Dates",
            options=date_options,
            default=date_options[:min(5, len(date_options))],  # Default to first 5 dates
            help="Pick any combination of dates - they don't need to be consecutive"
        )
        
        if len(selected_date_strs) == 0:
            st.warning("Please select at least one date.")
            return
        
        selected_dates = selected_date_strs
        st.caption(f"📅 Selected: **{len(selected_dates)} days**")
        use_range_mode = False
    
    # Data mode selection
    st.markdown("---")
    col_mode, col_info = st.columns([1, 2])
    
    with col_mode:
        data_mode = st.radio(
            "Data Mode",
            options=["All Data", "Filtered Data"],
            horizontal=True,
            key="custom_range_data_mode",
            help="Filtered Data excludes anomalous timestamps (high irradiance, zero power)"
        )
    
    # Get filtering thresholds from session state
    # Get filtering thresholds from session state
    irradiance_threshold = st.session_state.get('irradiance_filter_threshold', 50.0)
    power_threshold = st.session_state.get('power_filter_threshold', 0.0)
    soc_low_threshold = st.session_state.get('soc_low_threshold', 20)
    
    # Get daytime settings (default to 6-18 if not set or dynamic mode enabled but no weather data yet)
    daytime_start = st.session_state.get('daytime_start')
    daytime_end = st.session_state.get('daytime_end')
    
    if daytime_start is None: daytime_start = 6
    if daytime_end is None: daytime_end = 18
    
    # Determine if filtering should be used
    use_filtering = (data_mode == "Filtered Data")
    
    with col_info:
        if use_filtering:
            st.info(f"📋 Filter: Irradiance > {irradiance_threshold} W/m², Power ≤ {power_threshold} W, SoC < {soc_low_threshold}%")
        
        # Show daytime definition info
        if st.session_state.get('use_dynamic_sunrise', False):
            st.caption(f"🌅 Dynamic Daytime: Using weather data (fallback: {daytime_start}:00 - {daytime_end}:00)")
        else:
            st.caption(f"🌅 Daytime: {daytime_start}:00 - {daytime_end}:00 (Fixed)")
    
    # Import visualization function
    from modules.visualizations import calculate_selected_dates_hourly_averages
    
    st.markdown("---")
    
    # First row: Power graphs
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Avg Power & Irradiance")
        if use_range_mode:
            fig = plot_custom_range_hourly_power_irradiance(
                analysis_df, str(start_date), str(end_date), export_dir, show_plot=True,
                filter_anomalous=use_filtering,
                irradiance_threshold=irradiance_threshold,
                power_threshold=power_threshold,
                soc_low_threshold=soc_low_threshold,
                daytime_start=daytime_start,
                daytime_end=daytime_end
            )
        else:
            fig = plot_selected_dates_hourly_power_irradiance(
                analysis_df, selected_dates, export_dir, show_plot=True,
                filter_anomalous=use_filtering,
                irradiance_threshold=irradiance_threshold,
                power_threshold=power_threshold,
                soc_low_threshold=soc_low_threshold,
                daytime_start=daytime_start,
                daytime_end=daytime_end
            )
        if fig:
            st.pyplot(fig)
        else:
            st.info("Insufficient data for this graph.")
    
    with col2:
        if 'SoC_pct' in analysis_df.columns:
            st.markdown("#### Avg Power, Irradiance & SoC")
            if use_range_mode:
                fig = plot_custom_range_hourly_power_irradiance_soc(
                    analysis_df, str(start_date), str(end_date), export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            else:
                fig = plot_selected_dates_hourly_power_irradiance_soc(
                    analysis_df, selected_dates, export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Battery SoC data not available.")
    
    # Second row: Voltage and Current graphs
    st.markdown("---")
    col3, col4 = st.columns(2)
    
    with col3:
        if 'Voltage_V' in analysis_df.columns:
            st.markdown("#### Avg Voltage & Irradiance")
            if use_range_mode:
                fig = plot_custom_range_hourly_voltage_irradiance(
                    analysis_df, str(start_date), str(end_date), export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            else:
                fig = plot_selected_dates_hourly_voltage_irradiance(
                    analysis_df, selected_dates, export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Voltage data not available.")
    
    with col4:
        if 'Current_A' in analysis_df.columns:
            st.markdown("#### Avg Current & Irradiance")
            if use_range_mode:
                fig = plot_custom_range_hourly_current_irradiance(
                    analysis_df, str(start_date), str(end_date), export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            else:
                fig = plot_selected_dates_hourly_current_irradiance(
                    analysis_df, selected_dates, export_dir, show_plot=True,
                    filter_anomalous=use_filtering,
                    irradiance_threshold=irradiance_threshold,
                    power_threshold=power_threshold,
                    soc_low_threshold=soc_low_threshold,
                    daytime_start=daytime_start,
                    daytime_end=daytime_end
                )
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this graph.")
        else:
            st.info("Current data not available.")
    
    # Show filtered data comparison if selected
    if data_mode == "Filtered Data":
        st.markdown("---")
        st.markdown("### 📊 Filtered Data Analysis")
        
        # Get dates for filtering
        if use_range_mode:
            # Filter analysis_df to the date range
            range_df = analysis_df[
                (analysis_df['Date'] >= start_date) & 
                (analysis_df['Date'] <= end_date)
            ].copy()
            dates_for_filter = list(range_df['Date'].unique())
        else:
            dates_for_filter = selected_dates
        
        # Calculate filtered and unfiltered hourly averages
        hourly_avg_all, _ = calculate_selected_dates_hourly_averages(
            analysis_df, dates_for_filter, 
            filter_anomalous=False
        )
        hourly_avg_filtered, filter_info = calculate_selected_dates_hourly_averages(
            analysis_df, dates_for_filter,
            filter_anomalous=True,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold
        )
        
        # Show filter summary
        if filter_info.get('rows_excluded', 0) > 0:
            st.info(f"""
            📋 **Filtering Summary**: Excluded **{filter_info['rows_excluded']:,}** of **{filter_info['rows_total']:,}** data points ({filter_info['exclusion_pct']:.1f}%)
            """)
        else:
            st.success("✅ No anomalous data points found in selected dates.")
        
        # Show comparison
        if len(hourly_avg_filtered) > 0 and 'Power_W' in hourly_avg_filtered.columns and len(hourly_avg_all) > 0:
            col5, col6 = st.columns(2)
            
            with col5:
                st.markdown("#### Power Comparison (All vs Filtered)")
                import matplotlib.pyplot as plt
                
                fig, ax = plt.subplots(figsize=(14, 7))
                ax.plot(hourly_avg_all['Hour'], hourly_avg_all['Power_W'], 
                       'b-', linewidth=2, label='All Data', marker='o')
                ax.plot(hourly_avg_filtered['Hour'], hourly_avg_filtered['Power_W'], 
                       'g-', linewidth=2, label='Filtered', marker='s')
                ax.set_xlabel('Hour of Day', fontsize=12, fontweight='bold')
                ax.set_ylabel('Average Power (W)', fontsize=12, fontweight='bold')
                ax.set_title('Hourly Power Comparison', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                st.pyplot(fig)
                plt.close(fig)
            
            with col6:
                st.markdown("#### Difference Summary")
                avg_power_all = hourly_avg_all['Power_W'].mean()
                avg_power_filtered = hourly_avg_filtered['Power_W'].mean()
                power_diff = avg_power_filtered - avg_power_all
                power_diff_pct = (power_diff / avg_power_all * 100) if avg_power_all > 0 else 0
                
                st.metric("Avg Power (All Data)", f"{avg_power_all:.1f} W")
                st.metric("Avg Power (Filtered)", f"{avg_power_filtered:.1f} W", 
                         delta=f"{power_diff_pct:+.1f}%")
                
                if 'Irradiance_Wm2' in hourly_avg_all.columns and 'Irradiance_Wm2' in hourly_avg_filtered.columns:
                    avg_irr_all = hourly_avg_all['Irradiance_Wm2'].mean()
                    avg_irr_filtered = hourly_avg_filtered['Irradiance_Wm2'].mean()
                    st.metric("Avg Irradiance (All)", f"{avg_irr_all:.1f} W/m²")
                    st.metric("Avg Irradiance (Filtered)", f"{avg_irr_filtered:.1f} W/m²")


def display_pr_yield_graphs(analysis_df, daily_metrics, monthly_metrics, export_dir):
    """Display PR and Yield analysis graphs."""
    
    st.subheader("📊 Performance Ratio & Yield Analysis")
    
    # Data mode selection
    data_mode = st.radio(
        "Data Mode",
        options=["All Data", "Filtered Data", "Both (Comparison)"],
        horizontal=True,
        help="All Data: Include all timestamps. Filtered Data: Exclude anomalous timestamps (high irradiance but zero power). Both: Show side-by-side comparison."
    )
    
    # Get filtering thresholds from session state
    irradiance_threshold = st.session_state.get('irradiance_filter_threshold', 50.0)
    power_threshold = st.session_state.get('power_filter_threshold', 0.0)
    soc_low_threshold = st.session_state.get('soc_low_threshold', 20)
    soc_threshold = st.session_state.get('soc_threshold', 95)
    nominal_power = st.session_state.get('nominal_power', 5.0)
    temp_coeff = st.session_state.get('temp_coeff', -0.004)
    
    # Retrieve daytime settings
    daytime_start = st.session_state.get('daytime_start', 6) or 6
    daytime_end = st.session_state.get('daytime_end', 18) or 18
    
    # Calculate filtered metrics if needed
    if data_mode in ["Filtered Data", "Both (Comparison)"]:
        # Calculate filtered metrics
        filtered_daily_metrics = calculate_daily_metrics(
            analysis_df, nominal_power, temp_coeff,
            filter_anomalous=True,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold,
            soc_high_threshold=soc_threshold,
            daytime_start=daytime_start,
            daytime_end=daytime_end
        )
        filtered_monthly_metrics = calculate_monthly_metrics(
            analysis_df, nominal_power, temp_coeff,
            filter_anomalous=True,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold,
            soc_high_threshold=soc_threshold,
            daytime_start=daytime_start,
            daytime_end=daytime_end
        )
        
        # Calculate filter summary
        total_anomalous = daily_metrics['Anomalous_Points'].sum() if 'Anomalous_Points' in daily_metrics.columns else 0
        total_points = daily_metrics['Data_Points'].sum() if 'Data_Points' in daily_metrics.columns else 1
        exclusion_pct = (total_anomalous / total_points * 100) if total_points > 0 else 0
        
        st.info(f"""
        📋 **Filtering Summary**: Excluded **{int(total_anomalous):,}** of **{int(total_points):,}** data points ({exclusion_pct:.1f}%)
        
        *Filter criteria: Irradiance > {irradiance_threshold} W/m², Power ≤ {power_threshold} W, SoC < {soc_low_threshold}%*
        """)
    
    if data_mode == "All Data":
        # Show all-data graphs
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Performance Ratio Trend")
            fig = plot_pr_trend(daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for PR trend.")
        
        with col2:
            st.markdown("#### Specific Yield Over Time")
            fig = plot_specific_yield_trend(daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for Specific Yield.")
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Expected vs Actual Yield")
            fig = plot_expected_vs_actual(daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for comparison.")
        
        with col4:
            if len(monthly_metrics) > 0:
                st.markdown("#### Monthly Summary")
                fig = plot_monthly_summary(monthly_metrics, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("Insufficient data for monthly summary.")
    
    elif data_mode == "Filtered Data":
        # Show filtered-data graphs
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### Performance Ratio Trend (Filtered)")
            fig = plot_pr_trend(filtered_daily_metrics, export_dir, title_suffix=" (Filtered)", show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for PR trend.")
        
        with col2:
            st.markdown("#### Specific Yield Over Time (Filtered)")
            fig = plot_specific_yield_trend(filtered_daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for Specific Yield.")
        
        st.markdown("---")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("#### Expected vs Actual Yield (Filtered)")
            fig = plot_expected_vs_actual(filtered_daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for comparison.")
        
        with col4:
            if len(filtered_monthly_metrics) > 0:
                st.markdown("#### Monthly Summary (Filtered)")
                fig = plot_monthly_summary(filtered_monthly_metrics, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("Insufficient data for monthly summary.")
    
    else:  # Both (Comparison)
        # Show comparison - All Data on left, Filtered on right
        st.markdown("### All Data vs Filtered Data Comparison")
        
        # PR comparison
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### PR Trend (All Data)")
            all_avg_pr = daily_metrics['PR_pct'].mean() if 'PR_pct' in daily_metrics.columns else 0
            st.caption(f"Average PR: **{all_avg_pr:.1f}%**")
            fig = plot_pr_trend(daily_metrics, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
        
        with col2:
            st.markdown("#### PR Trend (Filtered)")
            filtered_avg_pr = filtered_daily_metrics['PR_pct'].mean() if 'PR_pct' in filtered_daily_metrics.columns else 0
            pr_diff = filtered_avg_pr - all_avg_pr
            st.caption(f"Average PR: **{filtered_avg_pr:.1f}%** ({'+' if pr_diff >= 0 else ''}{pr_diff:.1f}%)")
            fig = plot_pr_trend(filtered_daily_metrics, export_dir, title_suffix=" (Filtered)", show_plot=True)
            if fig:
                st.pyplot(fig)
        
        st.markdown("---")
        
        # Monthly summary comparison
        col3, col4 = st.columns(2)
        with col3:
            if len(monthly_metrics) > 0:
                st.markdown("#### Monthly Summary (All Data)")
                fig = plot_monthly_summary(monthly_metrics, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
        
        with col4:
            if len(filtered_monthly_metrics) > 0:
                st.markdown("#### Monthly Summary (Filtered)")
                fig = plot_monthly_summary(filtered_monthly_metrics, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)


def display_temperature_graphs(analysis_df, export_dir):
    """Display temperature effect analysis."""
    
    st.subheader("🌡️ Temperature Effect Analysis")
    
    if 'Temperature_C' not in analysis_df.columns:
        st.warning("Temperature data not available.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Overall Temperature Effect")
        fig = plot_temperature_effect_scatter(analysis_df, export_dir, show_plot=True)
        if fig:
            st.pyplot(fig)
        else:
            st.info("Insufficient data for temperature analysis.")
    
    with col2:
        # Daily temperature effect
        if 'Date' in analysis_df.columns:
            unique_dates = sorted(analysis_df['Date'].unique())
            selected_date = st.selectbox(
                "Select Date for Daily Analysis",
                options=unique_dates,
                format_func=lambda x: str(x),
                key="temp_date"
            )
            
            st.markdown("#### Daily Temperature Effect")
            fig = plot_daily_temperature_effect(analysis_df, str(selected_date), export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Insufficient data for this date.")


def display_calendar_view(analysis_df, daily_metrics):
    """Display calendar view with color-coded daily metrics and anomaly detection."""
    
    st.subheader("📅 Calendar View - Daily Performance")
    
    if len(daily_metrics) == 0:
        st.warning("No daily metrics available.")
        return
    
    # Get filtering thresholds from session state
    irradiance_threshold = st.session_state.get('irradiance_filter_threshold', 50.0)
    power_threshold = st.session_state.get('power_filter_threshold', 0.0)
    soc_low_threshold = st.session_state.get('soc_low_threshold', 20)
    soc_threshold = st.session_state.get('soc_threshold', 95)
    nominal_power = st.session_state.get('nominal_power', 5.0)
    temp_coeff = st.session_state.get('temp_coeff', -0.004)
    
    # Anomaly Summary Cards
    st.markdown("### 📊 Recent Performance")
    fig = plot_daily_summary_cards(daily_metrics, show_plot=True)
    if fig:
        st.pyplot(fig)
    
    st.markdown("---")
    
    # Anomaly Summary Statistics
    anomaly_summary = get_anomaly_summary(daily_metrics)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📆 Total Days", anomaly_summary['total_days'])
    with col2:
        st.metric("✅ Normal Days", anomaly_summary['normal_days'], 
                  delta=None, 
                  delta_color="off")
    with col3:
        st.metric("⚠️ Warning Days", anomaly_summary['warning_days'],
                  delta=f"-{anomaly_summary['warning_days']}" if anomaly_summary['warning_days'] > 0 else "0",
                  delta_color="inverse")
    with col4:
        st.metric("🔴 Critical Days", anomaly_summary['critical_days'],
                  delta=f"-{anomaly_summary['critical_days']}" if anomaly_summary['critical_days'] > 0 else "0",
                  delta_color="inverse")
    
    st.markdown("---")
    
    # Calendar Views
    st.markdown("### 📆 Calendar Heatmaps")
    
    col_view, col_filter = st.columns([2, 1])
    
    with col_view:
        calendar_type = st.radio(
            "Select Calendar View",
            options=['energy', 'pr', 'anomaly'],
            format_func=lambda x: {
                'energy': '⚡ Daily Energy (kWh)',
                'pr': '📊 Performance Ratio (%)',
                'anomaly': '🔍 Anomaly Status'
            }[x],
            horizontal=True,
            key="calendar_view_type"
        )
    
    with col_filter:
        # Show data mode only when PR is selected
        if calendar_type == 'pr':
            data_mode = st.radio(
                "Data Mode",
                options=["All Data", "Filtered Data"],
                horizontal=True,
                key="calendar_data_mode",
                help="Filtered Data excludes anomalous timestamps (high irradiance, zero power)"
            )
        else:
            data_mode = "All Data"
    
    # Use filtered metrics if PR view and Filtered Data selected
    metrics_to_use = daily_metrics
    if calendar_type == 'pr' and data_mode == "Filtered Data":
        # Recalculate with filtering
        filtered_metrics = calculate_daily_metrics(
            analysis_df, nominal_power, temp_coeff,
            filter_anomalous=True,
            irradiance_threshold=irradiance_threshold,
            power_threshold=power_threshold,
            soc_low_threshold=soc_low_threshold,
            soc_high_threshold=soc_threshold
        )
        metrics_to_use = filtered_metrics
        
        # Show filter info
        total_anomalous = daily_metrics['Anomalous_Points'].sum() if 'Anomalous_Points' in daily_metrics.columns else 0
        total_points = daily_metrics['Data_Points'].sum() if 'Data_Points' in daily_metrics.columns else 1
        exclusion_pct = (total_anomalous / total_points * 100) if total_points > 0 else 0
        st.info(f"📋 **Filtered**: Excluded {int(total_anomalous):,} data points ({exclusion_pct:.1f}%) | Thresholds: Irradiance > {irradiance_threshold} W/m², Power ≤ {power_threshold} W")
    
    fig = plot_calendar_heatmap(metrics_to_use, metric=calendar_type, show_plot=True)
    if fig:
        st.pyplot(fig)
    else:
        st.info("Insufficient data for calendar view.")
    
    # Anomaly Details Table
    if anomaly_summary['anomalies']:
        st.markdown("---")
        st.markdown("### ⚠️ Detected Anomalies")
        
        anomaly_data = []
        for a in anomaly_summary['anomalies']:
            anomaly_data.append({
                'Date': str(a['date']),
                'Severity': '🔴 Critical' if a['type'] == 'critical' else '⚠️ Warning',
                'Details': a['details']
            })
        
        import pandas as pd
        anomaly_df = pd.DataFrame(anomaly_data)
        st.dataframe(anomaly_df, use_container_width=True, hide_index=True)
    else:
        st.success("✅ No anomalies detected in the data!")


def display_export_section(analysis_df, daily_metrics, monthly_metrics, export_dir):
    """Display export options and generate all graphs."""
    
    st.subheader("💾 Export Options")
    
    tab_graphs, tab_data = st.tabs(["📊 Graph Export", "📝 Data Export"])
    
    with tab_graphs:
        st.markdown("### Export Graphs")
        st.markdown("Generate and download charts as high-resolution PNG images.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Date Range Filter
            if 'Date' in daily_metrics.columns:
                min_date = daily_metrics['Date'].min()
                max_date = daily_metrics['Date'].max()
                
                date_range = st.date_input(
                    "📅 Select Date Range",
                    value=(min_date, max_date),
                    min_value=min_date,
                    max_value=max_date,
                    help="Filter charts to this date range"
                )
            else:
                date_range = None
                st.warning("No date information available")
        
        with col2:
            # Graph Type Selection
            graph_types = [
                'Daily: Power & Irradiance',
                'Daily: Power, Irradiance & SoC',
                'Daily: Voltage & Irradiance',
                'Daily: Current & Irradiance',
                'Daily: Temperature Effect',
                'PR Trend',
                'Specific Yield Trend',
                'Expected vs Actual',
                'Monthly Summary',
                'Overall Temperature Effect'
            ]
            
            selected_graphs = st.multiselect(
                "📈 Select Graphs to Generate",
                options=graph_types,
                default=graph_types,
                help="Choose which types of charts to include in the export"
            )
            
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        
        with c1:
            if st.button("🗑️ Clean Export Directory", use_container_width=True):
                clean_export_directory(export_dir)
                st.success("Export directory cleaned!")
        
        with c2:
            if st.button("📥 Generate Selected Graphs", type="primary", use_container_width=True):
                if not date_range or len(date_range) != 2:
                    st.error("Please select a valid date range (Start - End)")
                elif not selected_graphs:
                    st.error("Please select at least one graph type")
                else:
                    with st.spinner("Generating graphs..."):
                        # Clean first
                        clean_export_directory(export_dir)
                        
                        # Generate filtered graphs
                        saved_files = generate_custom_export_graphs(
                            analysis_df,
                            daily_metrics,
                            monthly_metrics,
                            export_dir,
                            date_range,
                            selected_graphs
                        )
                        
                        st.success(f"✅ Generated {len(saved_files)} graphs!")
                        
                        # List files
                        files = list_exported_files(export_dir)
                        st.markdown(get_export_summary(files))
                        
                        # Create ZIP
                        if len(saved_files) > 0:
                            zip_path = create_zip_archive(saved_files, export_dir)
                            
                            with open(zip_path, 'rb') as f:
                                st.download_button(
                                    label="📦 Download Graphs as ZIP",
                                    data=f,
                                    file_name=os.path.basename(zip_path),
                                    mime="application/zip",
                                    use_container_width=True
                                )
    
    with tab_data:
        st.markdown("### Export Data (CSV)")
        st.markdown("Select columns to include in your data export.")
        
        col_selector, col_download = st.columns([2, 1])
        
        with col_selector:
            # Column selector for Main Data
            all_columns = sorted(analysis_df.columns.tolist())
            selected_columns = st.multiselect(
                "Select Columns to Export",
                options=all_columns,
                default=all_columns,
                help="Choose columns to include in the CSV file"
            )
            
        with col_download:
            st.markdown("<br>", unsafe_allow_html=True) # Spacing
            if selected_columns:
                export_df = analysis_df[selected_columns]
                csv_data = export_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Custom CSV",
                    data=csv_data,
                    file_name="solar_data_custom.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.warning("Select at least one column")
        
        st.markdown("---")
        st.markdown("#### Quick Downloads")
        
        q1, q2, q3 = st.columns(3)
        
        with q1:
            csv_full = analysis_df.to_csv(index=False)
            st.download_button(
                label="📥 Full Dataset (CSV)",
                data=csv_full,
                file_name="solar_data_full.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with q2:
            csv_daily = daily_metrics.to_csv(index=False)
            st.download_button(
                label="📥 Daily Metrics (CSV)",
                data=csv_daily,
                file_name="daily_metrics.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with q3:
            if len(monthly_metrics) > 0:
                csv_monthly = monthly_metrics.to_csv(index=False)
                st.download_button(
                    label="📥 Monthly Metrics (CSV)",
                    data=csv_monthly,
                    file_name="monthly_metrics.csv",
                    mime="text/csv",
                    use_container_width=True
                )
    
    # Show existing exports (for graphs only)
    st.markdown("---")
    st.subheader("📂 Exported Files (Graphs)")
    
    files = list_exported_files(export_dir)
    
    if len(files['daily']) + len(files['monthly']) == 0:
        st.info("No exported files yet. Generate graphs above.")
    else:
        # Simplified list view
        with st.expander("View File List", expanded=False):
            if files['daily']:
                st.markdown("**Daily Graphs:**")
                for f in files['daily']:
                    st.text(os.path.basename(f))
            
            if files['monthly']:
                st.markdown("**Monthly Graphs:**")
                for f in files['monthly']:
                    st.text(os.path.basename(f))


def display_anomaly_analysis(analysis_df: pd.DataFrame, vmpp: float, impp: float):
    """Display anomaly detection analysis with time series and summary tables."""
    
    st.header("🔍 Anomaly Analysis")
    st.caption(f"Using Vmpp = {vmpp}V, Impp = {impp}A (configure in sidebar)")
    
    # Get all anomalies
    all_anomalies = get_all_anomalies(analysis_df, vmpp, impp)
    
    # Summary metrics
    st.subheader("📊 Anomaly Summary")
    
    if len(all_anomalies) == 0:
        st.success("✅ No anomalies detected in the data!")
        return
    
    # Create summary cards
    cols = st.columns(5)
    anomaly_types = [
        "Power Dip (High Irr, Not Battery)",
        "Voltage Clipping",
        "Current Limiting",
        "Voltage Anomaly",
        "Current Anomaly"
    ]
    
    for i, anomaly_type in enumerate(anomaly_types):
        count = len(all_anomalies.get(anomaly_type, pd.DataFrame()))
        with cols[i]:
            st.metric(
                label=anomaly_type.split("(")[0].strip(),
                value=count,
                delta="⚠️" if count > 0 else "✅"
            )
    
    st.markdown("---")
    
    # Anomaly type selector
    st.subheader("🔎 Detailed Anomaly View")
    
    available_anomalies = list(all_anomalies.keys())
    
    if len(available_anomalies) == 0:
        st.info("No anomalies detected to display.")
        return
    
    selected_anomaly = st.selectbox(
        "Select Anomaly Type",
        available_anomalies,
        help="Choose an anomaly type to view detailed information"
    )
    
    if selected_anomaly:
        anomaly_df = all_anomalies[selected_anomaly]
        
        # Time series plot with anomaly markers
        st.subheader(f"📈 Time Series: {selected_anomaly}")
        
        import matplotlib.pyplot as plt
        
        fig, ax = plt.subplots(figsize=(14, 5))
        
        # Plot base data
        if 'Power_W' in analysis_df.columns:
            ax.plot(analysis_df['Timestamp'], analysis_df['Power_W']/1000, 
                   color='#3498DB', alpha=0.5, linewidth=0.5, label='Power (kW)')
        
        # Mark anomaly points
        if 'Timestamp' in anomaly_df.columns:
            if 'Power_W' in anomaly_df.columns:
                ax.scatter(anomaly_df['Timestamp'], anomaly_df['Power_W']/1000,
                          color='red', s=20, zorder=5, label=f'{selected_anomaly} ({len(anomaly_df)} points)')
            elif 'Voltage_V' in anomaly_df.columns:
                ax.scatter(anomaly_df['Timestamp'], anomaly_df['Voltage_V'],
                          color='red', s=20, zorder=5, label=f'{selected_anomaly} ({len(anomaly_df)} points)')
        
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Value')
        ax.set_title(f'{selected_anomaly} Detection')
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        fig.tight_layout()
        
        st.pyplot(fig)
        plt.close()
        
        # Summary table
        st.subheader(f"📋 Anomaly Details ({len(anomaly_df)} events)")
        
        # Select relevant columns for display
        display_cols = ['Timestamp']
        if 'Power_W' in anomaly_df.columns:
            display_cols.append('Power_W')
        if 'Voltage_V' in anomaly_df.columns:
            display_cols.append('Voltage_V')
        if 'Current_A' in anomaly_df.columns:
            display_cols.append('Current_A')
        if 'Irradiance_Wm2' in anomaly_df.columns:
            display_cols.append('Irradiance_Wm2')
        if 'SoC_pct' in anomaly_df.columns:
            display_cols.append('SoC_pct')
        if 'Power_Ratio' in anomaly_df.columns:
            display_cols.append('Power_Ratio')
        if 'Voltage_Ratio' in anomaly_df.columns:
            display_cols.append('Voltage_Ratio')
        if 'Current_Ratio' in anomaly_df.columns:
            display_cols.append('Current_Ratio')
        
        available_cols = [c for c in display_cols if c in anomaly_df.columns]
        
        st.dataframe(
            anomaly_df[available_cols].head(100),
            use_container_width=True
        )
        
        if len(anomaly_df) > 100:
            st.caption(f"Showing first 100 of {len(anomaly_df)} anomalies")
        
        # Download button for anomaly data
        csv = anomaly_df.to_csv(index=False)
        st.download_button(
            label=f"📥 Download {selected_anomaly} Data",
            data=csv,
            file_name=f"anomalies_{selected_anomaly.replace(' ', '_').lower()}.csv",
            mime="text/csv"
        )


def display_data_quality(analysis_df: pd.DataFrame):
    """Display data quality analysis and checks."""
    
    st.header("📋 Data Quality Analysis")
    
    # Get comprehensive quality report
    quality_report = get_data_quality_report(analysis_df)
    
    # Quality Score Card
    st.subheader("📊 Overall Data Quality")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        score = quality_report.get('quality_score', 0)
        grade = quality_report.get('quality_grade', 'N/A')
        st.metric("Quality Score", f"{score:.1f}/100", grade)
    
    with col2:
        completeness = quality_report.get('completeness', {}).get('overall_completeness_pct', 0)
        st.metric("Completeness", f"{completeness:.1f}%")
    
    with col3:
        suspicious = quality_report.get('validation', {}).get('suspicious_count', 0)
        st.metric("Suspicious Readings", suspicious)
    
    with col4:
        duplicates = quality_report.get('duplicates', {}).get('duplicate_count', 0)
        st.metric("Duplicate Rows", duplicates)
    
    st.markdown("---")
    
    # Data Completeness Section
    with st.expander("📈 Data Completeness", expanded=True):
        completeness_info = quality_report.get('completeness', {})
        
        if 'error' not in completeness_info:
            # Show detected interval
            detected_interval = completeness_info.get('detected_interval_minutes', 'Auto')
            daytime_only = completeness_info.get('daytime_only', True)
            
            if detected_interval != 'Auto':
                if detected_interval >= 60:
                    interval_str = f"{detected_interval/60:.0f} hour(s)"
                else:
                    interval_str = f"{detected_interval:.0f} minute(s)"
                st.info(f"🔍 **Detected Data Frequency:** {interval_str} | **Analysis Period:** {'Daytime only (6 AM - 6 PM)' if daytime_only else '24 hours'}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Expected Data Points:** {completeness_info.get('expected_points', 'N/A')}")
                st.write(f"**Actual Data Points:** {completeness_info.get('actual_points', 'N/A')}")
                st.write(f"**Completeness:** {completeness_info.get('overall_completeness_pct', 0):.1f}%")
            
            with col2:
                data_range = completeness_info.get('data_range', {})
                if data_range:
                    st.write(f"**Start:** {data_range.get('start', 'N/A')}")
                    st.write(f"**End:** {data_range.get('end', 'N/A')}")
                    st.write(f"**Duration:** {data_range.get('duration_hours', 0):.1f} hours")
            
            # Missing periods
            missing_periods = completeness_info.get('missing_periods', [])
            if len(missing_periods) > 0:
                st.warning(f"⚠️ Found {len(missing_periods)} data gaps")
                gaps_df = pd.DataFrame(missing_periods)
                st.dataframe(gaps_df, use_container_width=True)
            else:
                st.success("✅ No significant data gaps detected")
    
    # Data Validation Section
    with st.expander("🔍 Data Validation", expanded=False):
        validation_info = quality_report.get('validation', {})
        
        # Column statistics
        col_stats = validation_info.get('column_stats', {})
        if col_stats:
            st.write("**Column Statistics:**")
            stats_data = []
            for col, stats in col_stats.items():
                stats_data.append({
                    'Column': col,
                    'Min': f"{stats.get('min', 'N/A'):.2f}" if isinstance(stats.get('min'), (int, float)) else 'N/A',
                    'Max': f"{stats.get('max', 'N/A'):.2f}" if isinstance(stats.get('max'), (int, float)) else 'N/A',
                    'Mean': f"{stats.get('mean', 'N/A'):.2f}" if isinstance(stats.get('mean'), (int, float)) else 'N/A',
                    'Null Count': stats.get('null_count', 0),
                    'Out of Range': stats.get('out_of_range_count', 0),
                    'Valid Range': str(stats.get('valid_range', 'N/A'))
                })
            st.dataframe(pd.DataFrame(stats_data), use_container_width=True)
        
        # Suspicious readings
        suspicious_readings = validation_info.get('suspicious_readings', [])
        if len(suspicious_readings) > 0:
            st.warning(f"⚠️ Found {len(suspicious_readings)} suspicious readings")
            st.dataframe(pd.DataFrame(suspicious_readings).head(50), use_container_width=True)
        else:
            st.success("✅ All readings within expected ranges")
    
    # Duplicate Detection Section
    with st.expander("📑 Duplicate Detection", expanded=False):
        duplicates_info = quality_report.get('duplicates', {})
        
        if duplicates_info.get('has_duplicates', False):
            st.warning(f"⚠️ Found {duplicates_info.get('duplicate_count', 0)} duplicate rows")
            st.write(f"**Unique duplicate timestamps:** {duplicates_info.get('unique_duplicate_timestamps', 0)}")
            
            duplicate_groups = duplicates_info.get('duplicate_groups', [])
            if duplicate_groups:
                st.dataframe(pd.DataFrame(duplicate_groups[:20]), use_container_width=True)
        else:
            st.success("✅ No duplicate timestamps detected")
    
    # Operating Hours Summary (from daily metrics if available)
    with st.expander("⏱️ Operating Hours", expanded=False):
        if 'Power_W' in analysis_df.columns:
            from modules.calculations import calculate_operating_hours
            total_hours = calculate_operating_hours(analysis_df)
            st.metric("Total Operating Hours", f"{total_hours:.1f} hrs")
        else:
            st.info("Operating hours require Power data")


def display_power_anomalies(analysis_df: pd.DataFrame, export_dir: str):
    """Display power anomaly detection and analysis."""
    
    st.subheader("⚠️ Power Anomaly Detection")
    st.info("""
    **Detects unexpected low power output** when irradiance is sufficient.
    
    If your data includes **Battery SoC**, periods of high SoC (battery full) are 
    automatically excluded — power curtailment due to full battery is *not* an anomaly.
    """)
    
    # Check required columns
    if 'Power_W' not in analysis_df.columns:
        st.warning("⚠️ Power data is required for anomaly detection.")
        return
    
    if 'Irradiance_Wm2' not in analysis_df.columns:
        st.warning("⚠️ Irradiance data is required for anomaly detection.")
        return
    
    # Threshold settings
    st.markdown("### ⚙️ Detection Settings")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        power_threshold = st.number_input(
            "Power Threshold (W)",
            min_value=0.0,
            max_value=100.0,
            value=10.0,
            step=1.0,
            help="Data points with power below this value are flagged as potential anomalies"
        )
    
    with col2:
        irradiance_threshold = st.number_input(
            "Min Irradiance (W/m²)",
            min_value=0.0,
            max_value=500.0,
            value=50.0,
            step=10.0,
            help="Only flag anomalies when irradiance is above this threshold"
        )
    
    with col3:
        has_soc = 'SoC_pct' in analysis_df.columns
        if has_soc:
            soc_threshold = st.number_input(
                "SoC Exclusion Threshold (%)",
                min_value=50.0,
                max_value=100.0,
                value=float(st.session_state.get('soc_threshold', 95.0)),
                step=1.0,
                help="Exclude periods when battery SoC is above this value (not anomalies)"
            )
        else:
            soc_threshold = 95.0
            st.info("📊 No SoC data - all low-power periods will be flagged")
    
    # Detect anomalies
    anomalies = detect_power_anomalies(
        analysis_df,
        power_threshold=power_threshold,
        irradiance_threshold=irradiance_threshold,
        soc_threshold=soc_threshold
    )
    
    st.markdown("---")
    
    # Summary metrics
    st.markdown("### 📊 Summary")
    
    total_points = len(analysis_df)
    anomaly_count = len(anomalies)
    anomaly_pct = (anomaly_count / total_points * 100) if total_points > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Data Points", f"{total_points:,}")
    
    with col2:
        st.metric("Anomalies Detected", f"{anomaly_count:,}")
    
    with col3:
        st.metric("Anomaly Rate", f"{anomaly_pct:.2f}%")
    
    with col4:
        if anomaly_count > 0:
            avg_irr_during_anomaly = anomalies['Irradiance_Wm2'].mean()
            st.metric("Avg Irradiance (Anomalies)", f"{avg_irr_during_anomaly:.0f} W/m²")
        else:
            st.metric("Status", "✅ No Anomalies")
    
    if anomaly_count == 0:
        st.success("🎉 **No power anomalies detected!** Your system appears to be operating normally.")
        return
    
    st.markdown("---")
    
    # Visualizations
    st.markdown("### 📈 Visualizations")
    
    viz_tab1, viz_tab2 = st.tabs(["Scatter Plot", "Timeline"])
    
    with viz_tab1:
        st.markdown("**Power vs Irradiance** - Anomalies highlighted in red")
        fig_scatter = plot_power_anomaly_scatter(analysis_df, anomalies, show_plot=True)
        if fig_scatter:
            st.pyplot(fig_scatter)
    
    with viz_tab2:
        st.markdown("**Daily Anomaly Count** - When did anomalies occur?")
        fig_timeline = plot_power_anomaly_timeline(anomalies, show_plot=True)
        if fig_timeline:
            st.pyplot(fig_timeline)
        else:
            st.info("Timeline requires Timestamp data.")
    
    st.markdown("---")
    
    # Data Table
    st.markdown("### 📋 Anomaly Data")
    
    with st.expander(f"View All {anomaly_count} Anomaly Points", expanded=False):
        # Select relevant columns for display
        display_cols = ['Timestamp', 'Power_W', 'Irradiance_Wm2']
        if 'Voltage_V' in anomalies.columns:
            display_cols.append('Voltage_V')
        if 'Current_A' in anomalies.columns:
            display_cols.append('Current_A')
        if 'SoC_pct' in anomalies.columns:
            display_cols.append('SoC_pct')
        if 'Temperature_C' in anomalies.columns:
            display_cols.append('Temperature_C')
        
        available_cols = [c for c in display_cols if c in anomalies.columns]
        st.dataframe(anomalies[available_cols], use_container_width=True, height=400)
        
        # Download button
        csv_data = anomalies[available_cols].to_csv(index=False)
        st.download_button(
            label="📥 Download Anomalies CSV",
            data=csv_data,
            file_name="power_anomalies.csv",
            mime="text/csv"
        )


def display_custom_metrics(analysis_df: pd.DataFrame, column_mapping: dict, export_dir: str):
    """Display analysis for custom/extra columns in the user's data."""
    
    st.subheader("📈 Custom Metrics Analysis")
    st.info("""
    Analyze any **extra columns** in your data that aren't part of the standard set 
    (voltage, current, irradiance, temperature, SoC).
    """)
    
    # Get extra columns
    extra_cols = get_extra_columns(analysis_df, column_mapping)
    
    if len(extra_cols) == 0:
        st.warning("⚠️ No extra numeric columns found in your data.")
        st.markdown("""
        **Standard columns detected:**
        - Timestamp, Voltage, Current, Irradiance, Temperature, SoC, Power
        
        If you have additional metrics you'd like to analyze, ensure they are:
        1. Numeric values (not text)
        2. Not matching standard column patterns
        """)
        return
    
    st.success(f"✅ Found **{len(extra_cols)}** extra column(s) available for analysis.")
    
    # Column selection
    selected_col = st.selectbox(
        "Select Column to Analyze",
        options=extra_cols,
        key="custom_metric_select"
    )
    
    if selected_col is None:
        return
    
    # Get column data
    col_data = analysis_df[selected_col].dropna()
    
    if len(col_data) == 0:
        st.warning(f"⚠️ No valid data in column '{selected_col}'")
        return
    
    st.markdown("---")
    
    # Statistics
    st.markdown("### 📊 Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Min", f"{col_data.min():.2f}")
    with col2:
        st.metric("Max", f"{col_data.max():.2f}")
    with col3:
        st.metric("Mean", f"{col_data.mean():.2f}")
    with col4:
        st.metric("Std Dev", f"{col_data.std():.2f}")
    
    st.markdown("---")
    
    # Visualizations
    st.markdown("### 📈 Visualizations")
    
    # Check what time periods are available
    has_hour = 'Hour' in analysis_df.columns
    has_date = 'Date' in analysis_df.columns
    has_month = 'Month' in analysis_df.columns
    
    viz_tabs = ["Daily Hourly Pattern"]
    if has_date:
        viz_tabs.append("Daily Trend")
    if has_month:
        viz_tabs.append("Monthly Averages")
    
    tabs = st.tabs(viz_tabs)
    
    tab_idx = 0
    
    # Daily Hourly Pattern (0-23 hours)
    with tabs[tab_idx]:
        st.markdown(f"#### Hourly Pattern of {selected_col}")
        if has_hour:
            hourly_avg = analysis_df.groupby('Hour')[selected_col].mean().reset_index()
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(hourly_avg['Hour'], hourly_avg[selected_col], 
                   color='#3498DB', linewidth=2, marker='o', markersize=5)
            ax.fill_between(hourly_avg['Hour'], hourly_avg[selected_col], 
                           alpha=0.2, color='#3498DB')
            ax.set_xlabel('Hour of Day', fontsize=11)
            ax.set_ylabel(selected_col, fontsize=11)
            ax.set_title(f'Average {selected_col} by Hour', fontsize=13, fontweight='bold')
            ax.set_xlim(0, 23)
            ax.set_xticks(range(0, 24, 2))
            ax.grid(True, alpha=0.3)
            st.pyplot(fig)
            plt.close(fig)
        else:
            st.info("Hour data not available for hourly pattern analysis.")
        tab_idx += 1
    
    # Daily Trend
    if has_date and tab_idx < len(tabs):
        with tabs[tab_idx]:
            st.markdown(f"#### Daily Average of {selected_col}")
            daily_avg = analysis_df.groupby('Date')[selected_col].mean().reset_index()
            
            fig, ax = plt.subplots(figsize=(12, 5))
            ax.plot(range(len(daily_avg)), daily_avg[selected_col], 
                   color='#2ECC71', linewidth=1.5, marker='o', markersize=3)
            ax.fill_between(range(len(daily_avg)), daily_avg[selected_col], 
                           alpha=0.2, color='#2ECC71')
            ax.set_xlabel('Date', fontsize=11)
            ax.set_ylabel(selected_col, fontsize=11)
            ax.set_title(f'Daily Average {selected_col}', fontsize=13, fontweight='bold')
            
            # X-axis labels
            if len(daily_avg) <= 15:
                ax.set_xticks(range(len(daily_avg)))
                ax.set_xticklabels([str(d) for d in daily_avg['Date']], rotation=45, ha='right')
            else:
                step = max(1, len(daily_avg) // 10)
                ax.set_xticks(range(0, len(daily_avg), step))
                ax.set_xticklabels([str(d) for d in daily_avg['Date'].iloc[::step]], rotation=45, ha='right')
            
            ax.grid(True, alpha=0.3)
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
            tab_idx += 1
    
    # Monthly Averages
    if has_month and tab_idx < len(tabs):
        with tabs[tab_idx]:
            st.markdown(f"#### Monthly Average of {selected_col}")
            monthly_avg = analysis_df.groupby('Month')[selected_col].mean().reset_index()
            monthly_avg['Month_str'] = monthly_avg['Month'].astype(str)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            bars = ax.bar(range(len(monthly_avg)), monthly_avg[selected_col], 
                         color='#9B59B6', alpha=0.8, edgecolor='#7D3C98')
            ax.set_xlabel('Month', fontsize=11)
            ax.set_ylabel(selected_col, fontsize=11)
            ax.set_title(f'Monthly Average {selected_col}', fontsize=13, fontweight='bold')
            ax.set_xticks(range(len(monthly_avg)))
            ax.set_xticklabels(monthly_avg['Month_str'], rotation=45, ha='right')
            ax.grid(True, alpha=0.3, axis='y')
            
            # Add value labels
            for bar in bars:
                height = bar.get_height()
                ax.annotate(f'{height:.1f}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=9)
            
            plt.tight_layout()
            st.pyplot(fig)
            plt.close(fig)
    
    st.markdown("---")
    
    # Data Table
    st.markdown("### 📋 Raw Data")
    with st.expander(f"View {selected_col} Data", expanded=False):
        display_cols = ['Timestamp', selected_col]
        if 'Date' in analysis_df.columns:
            display_cols.insert(1, 'Date')
        if 'Hour' in analysis_df.columns:
            display_cols.insert(2, 'Hour')
        
        available_display_cols = [c for c in display_cols if c in analysis_df.columns]
        st.dataframe(analysis_df[available_display_cols].dropna(subset=[selected_col]), 
                    use_container_width=True, height=400)


def display_weather_analysis(export_dir: str):
    """Display standalone weather analysis tab for site selection and analysis."""
    
    st.subheader("🌤️ Weather Analysis")
    st.info("**Standalone Weather Analysis** - Fetch historical weather data for any location to analyze solar potential. This is independent of your uploaded solar data.")
    
    # Initialize session state for weather data
    if 'weather_hourly_df' not in st.session_state:
        st.session_state.weather_hourly_df = None
    if 'weather_daily_df' not in st.session_state:
        st.session_state.weather_daily_df = None
    if 'weather_location' not in st.session_state:
        st.session_state.weather_location = None
    
    # Location Input Section
    st.markdown("### 📍 Location")
    
    col_loc1, col_loc2 = st.columns([2, 1])
    
    with col_loc1:
        location_mode = st.radio(
            "Input Method",
            options=["Coordinates", "Google Maps URL"],
            horizontal=True,
            key="weather_location_mode"
        )
    
    weather_lat, weather_lon = 0.0, 0.0
    
    if location_mode == "Google Maps URL":
        map_url = st.text_input(
            "Paste Google Maps URL",
            placeholder="https://www.google.com/maps/@22.3964,114.1095,15z",
            key="weather_map_url"
        )
        if map_url:
            parsed_lat, parsed_lon = extract_coordinates_from_url(map_url)
            if parsed_lat is not None:
                weather_lat, weather_lon = parsed_lat, parsed_lon
                st.success(f"📍 Extracted: {weather_lat:.4f}, {weather_lon:.4f}")
            else:
                st.warning("Could not extract coordinates from URL")
    
    col_lat, col_lon = st.columns(2)
    with col_lat:
        weather_lat = st.number_input(
            "Latitude",
            value=weather_lat,
            min_value=-90.0,
            max_value=90.0,
            format="%.4f",
            key="weather_lat"
        )
    with col_lon:
        weather_lon = st.number_input(
            "Longitude",
            value=weather_lon,
            min_value=-180.0,
            max_value=180.0,
            format="%.4f",
            key="weather_lon"
        )
    
    st.markdown("### 📅 Date Range")
    
    col_range1, col_range2, col_range3 = st.columns([1, 1, 1])
    
    from datetime import datetime, timedelta
    
    with col_range1:
        range_mode = st.selectbox(
            "Quick Select",
            options=["Last 7 Days", "Last 30 Days", "Last 3 Months", "Last 6 Months", "Last Year", "Custom Range"],
            key="weather_range_mode"
        )
    
    # Calculate default dates based on selection
    today = datetime.now().date()
    
    if range_mode == "Last 7 Days":
        default_start = today - timedelta(days=7)
        default_end = today - timedelta(days=1)  # Yesterday (API might not have today's data)
    elif range_mode == "Last 30 Days":
        default_start = today - timedelta(days=30)
        default_end = today - timedelta(days=1)
    elif range_mode == "Last 3 Months":
        default_start = today - timedelta(days=90)
        default_end = today - timedelta(days=1)
    elif range_mode == "Last 6 Months":
        default_start = today - timedelta(days=180)
        default_end = today - timedelta(days=1)
    elif range_mode == "Last Year":
        default_start = today - timedelta(days=365)
        default_end = today - timedelta(days=1)
    else:
        default_start = today - timedelta(days=30)
        default_end = today - timedelta(days=1)
    
    with col_range2:
        start_date = st.date_input(
            "Start Date",
            value=default_start,
            max_value=today - timedelta(days=1),
            key="weather_start_date"
        )
    
    with col_range3:
        end_date = st.date_input(
            "End Date",
            value=default_end,
            min_value=start_date,
            max_value=today - timedelta(days=1),
            key="weather_end_date"
        )
    
    days_selected = (end_date - start_date).days + 1
    st.caption(f"📅 Selected period: **{days_selected} days** ({start_date} to {end_date})")
    
    # Fetch button
    if st.button("☁️ Fetch Weather Data", type="primary", use_container_width=True, key="fetch_weather_btn"):
        if weather_lat == 0.0 and weather_lon == 0.0:
            st.error("Please enter valid coordinates")
        else:
            with st.spinner("Fetching weather data from Open-Meteo..."):
                hourly_df, daily_df = fetch_standalone_weather_data(
                    weather_lat,
                    weather_lon,
                    datetime.combine(start_date, datetime.min.time()),
                    datetime.combine(end_date, datetime.min.time())
                )
                
                if hourly_df is not None and daily_df is not None:
                    st.session_state.weather_hourly_df = hourly_df
                    st.session_state.weather_daily_df = daily_df
                    st.session_state.weather_location = (weather_lat, weather_lon)
                    st.success(f"✅ Fetched {len(hourly_df)} hourly records and {len(daily_df)} daily records")
                    st.rerun()
                else:
                    st.error("Failed to fetch weather data. Please check your coordinates and date range.")
    
    # Display data if available
    if st.session_state.weather_hourly_df is not None and st.session_state.weather_daily_df is not None:
        hourly_df = st.session_state.weather_hourly_df
        daily_df = st.session_state.weather_daily_df
        
        st.markdown("---")
        
        # Summary Metrics
        st.markdown("### 📊 Summary")
        
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            avg_irr = hourly_df['Irradiance_Wm2'].mean()
            st.metric("Avg Irradiance", f"{avg_irr:.0f} W/m²")
        
        with col2:
            max_irr = hourly_df['Irradiance_Wm2'].max()
            st.metric("Peak Irradiance", f"{max_irr:.0f} W/m²")
        
        with col3:
            avg_temp = hourly_df['Temperature_C'].mean()
            st.metric("Avg Temperature", f"{avg_temp:.1f}°C")
        
        with col4:
            if 'Total_Irradiance_kWhm2' in daily_df.columns:
                total_irr = daily_df['Total_Irradiance_kWhm2'].sum()
                st.metric("Total Irradiance", f"{total_irr:.1f} kWh/m²")
        
        with col5:
            if 'Daylight_Hours' in daily_df.columns:
                avg_daylight = daily_df['Daylight_Hours'].mean()
                st.metric("Avg Daylight", f"{avg_daylight:.1f} hrs")
        
        st.markdown("---")
        
        # View Selection
        view_mode = st.radio(
            "View Mode",
            options=["Daily Analysis", "Monthly Averages", "Data Tables"],
            horizontal=True,
            key="weather_view_mode"
        )
        
        if view_mode == "Daily Analysis":
            st.markdown("### 📈 Daily Analysis")
            
            # Date selection
            unique_dates = sorted(hourly_df['Date'].unique())
            date_options = [str(d) for d in unique_dates]
            
            selected_date = st.selectbox(
                "Select Date",
                options=date_options,
                index=0,
                key="weather_daily_date"
            )
            
            # Get sunrise/sunset for selected date
            selected_daily = daily_df[daily_df['Date'].astype(str) == selected_date]
            
            if not selected_daily.empty:
                row = selected_daily.iloc[0]
                col_sun1, col_sun2, col_sun3, col_sun4 = st.columns(4)
                
                with col_sun1:
                    if pd.notna(row.get('Sunrise')):
                        sunrise_str = row['Sunrise'].strftime('%H:%M')
                        st.metric("🌅 Sunrise", sunrise_str)
                
                with col_sun2:
                    if pd.notna(row.get('Sunset')):
                        sunset_str = row['Sunset'].strftime('%H:%M')
                        st.metric("🌇 Sunset", sunset_str)
                
                with col_sun3:
                    if pd.notna(row.get('Daylight_Hours')):
                        st.metric("☀️ Daylight", f"{row['Daylight_Hours']:.1f} hrs")
                
                with col_sun4:
                    if pd.notna(row.get('Total_Irradiance_kWhm2')):
                        st.metric("⚡ Daily Energy", f"{row['Total_Irradiance_kWhm2']:.2f} kWh/m²")
            
            # Graphs
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("#### Irradiance vs Time")
                fig = plot_weather_daily_irradiance(hourly_df, selected_date, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No data for this date")
            
            with col_g2:
                st.markdown("#### Temperature vs Time")
                fig = plot_weather_daily_temperature(hourly_df, selected_date, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
                else:
                    st.info("No data for this date")
        
        elif view_mode == "Monthly Averages":
            st.markdown("### 📊 Monthly Average Patterns")
            st.info("These graphs show the **average hourly values** across all days in the selected period.")
            
            # Overall averages section
            st.markdown("#### 📈 Overall Period Averages")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("**Avg Hourly Irradiance (All Data)**")
                fig = plot_weather_monthly_avg_irradiance(hourly_df, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
            
            with col_g2:
                st.markdown("**Avg Hourly Temperature (All Data)**")
                fig = plot_weather_monthly_avg_temperature(hourly_df, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
            
            st.markdown("---")
            
            # Per-month selection
            st.markdown("#### 📅 Per-Month Analysis")
            st.caption("Select a specific month to see hourly patterns for just that month.")
            
            # Get available months from data
            hourly_df_copy = hourly_df.copy()
            hourly_df_copy['YearMonth'] = pd.to_datetime(hourly_df_copy['Timestamp']).dt.to_period('M')
            available_months = sorted(hourly_df_copy['YearMonth'].unique())
            month_options = [str(m) for m in available_months]
            
            if len(month_options) > 1:
                selected_month = st.selectbox(
                    "Select Month",
                    options=month_options,
                    index=0,
                    key="weather_month_select"
                )
                
                # Filter data for selected month
                month_data = hourly_df_copy[hourly_df_copy['YearMonth'].astype(str) == selected_month]
                
                if not month_data.empty:
                    # Calculate hourly averages for this month
                    month_hourly_avg = month_data.groupby('Hour').agg({
                        'Irradiance_Wm2': 'mean',
                        'Temperature_C': 'mean'
                    }).reset_index()
                    
                    col_m1, col_m2 = st.columns(2)
                    
                    with col_m1:
                        st.markdown(f"**Irradiance - {selected_month}**")
                        fig, ax = plt.subplots(figsize=(8, 4))
                        ax.plot(month_hourly_avg['Hour'], month_hourly_avg['Irradiance_Wm2'], 
                               color='#FF9800', linewidth=2, marker='o', markersize=4)
                        ax.fill_between(month_hourly_avg['Hour'], month_hourly_avg['Irradiance_Wm2'], 
                                       alpha=0.2, color='#FF9800')
                        ax.set_xlabel('Hour of Day')
                        ax.set_ylabel('Irradiance (W/m²)')
                        ax.set_title(f'Avg Hourly Irradiance - {selected_month}')
                        ax.set_xlim(0, 23)
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        plt.close(fig)
                    
                    with col_m2:
                        st.markdown(f"**Temperature - {selected_month}**")
                        fig, ax = plt.subplots(figsize=(8, 4))
                        ax.plot(month_hourly_avg['Hour'], month_hourly_avg['Temperature_C'], 
                               color='#E91E63', linewidth=2, marker='o', markersize=4)
                        ax.fill_between(month_hourly_avg['Hour'], month_hourly_avg['Temperature_C'], 
                                       alpha=0.2, color='#E91E63')
                        ax.set_xlabel('Hour of Day')
                        ax.set_ylabel('Temperature (°C)')
                        ax.set_title(f'Avg Hourly Temperature - {selected_month}')
                        ax.set_xlim(0, 23)
                        ax.grid(True, alpha=0.3)
                        st.pyplot(fig)
                        plt.close(fig)
            else:
                st.info("📅 Select a date range spanning multiple months to compare monthly patterns.")
            
            st.markdown("---")
            st.markdown("#### Daily Summary")
            st.caption("View temperature range and irradiance for a selected date range")
            
            # Date range selection for daily summary
            col_ds1, col_ds2 = st.columns(2)
            unique_dates = sorted(daily_df['Date'].unique())
            min_summary_date = min(unique_dates)
            max_summary_date = max(unique_dates)
            
            with col_ds1:
                summary_start = st.date_input(
                    "Start Date",
                    value=min_summary_date,
                    min_value=min_summary_date,
                    max_value=max_summary_date,
                    key="weather_summary_start"
                )
            with col_ds2:
                summary_end = st.date_input(
                    "End Date",
                    value=max_summary_date,
                    min_value=min_summary_date,
                    max_value=max_summary_date,
                    key="weather_summary_end"
                )
            
            # Filter daily_df for selected range
            import datetime as dt
            summary_df = daily_df[
                (daily_df['Date'] >= summary_start) & 
                (daily_df['Date'] <= summary_end)
            ].copy()
            
            if len(summary_df) > 0:
                days_selected = len(summary_df)
                st.caption(f"📅 Showing {days_selected} days ({summary_start} to {summary_end})")
                
                fig = plot_weather_daily_summary(summary_df, export_dir, show_plot=True)
                if fig:
                    st.pyplot(fig)
                
                # Add Sunrise/Sunset times graph
                if 'Sunrise' in summary_df.columns and 'Sunset' in summary_df.columns:
                    st.markdown("**☀️ Sunrise & Sunset Times**")
                    
                    fig, ax = plt.subplots(figsize=(12, 5))
                    
                    dates = range(len(summary_df))
                    date_labels = [str(d)[:10] for d in summary_df['Date']]
                    sunrise_hours = summary_df['Sunrise'].dt.hour + summary_df['Sunrise'].dt.minute / 60
                    sunset_hours = summary_df['Sunset'].dt.hour + summary_df['Sunset'].dt.minute / 60
                    
                    # Fill daylight area
                    ax.fill_between(dates, sunrise_hours, sunset_hours, alpha=0.3, color='#FFD700', label='Daylight Hours')
                    
                    # Plot sunrise and sunset lines
                    ax.plot(dates, sunrise_hours, color='#FF9800', linewidth=2.5, label='Sunrise', marker='.', markersize=6)
                    ax.plot(dates, sunset_hours, color='#E91E63', linewidth=2.5, label='Sunset', marker='.', markersize=6)
                    
                    # Format axes - zoom to data range with finer tick marks
                    ax.set_xlabel('Date', fontsize=11)
                    ax.set_ylabel('Time of Day', fontsize=11)
                    ax.set_title('Sunrise & Sunset Times', fontsize=13, fontweight='bold')
                    
                    # Calculate y-axis range based on data with padding
                    min_hour = max(0, int(sunrise_hours.min()) - 1)
                    max_hour = min(24, int(sunset_hours.max()) + 1)
                    ax.set_ylim(min_hour, max_hour)
                    
                    # Set ticks at every hour for precise readings
                    y_ticks = list(range(min_hour, max_hour + 1))
                    ax.set_yticks(y_ticks)
                    ax.set_yticklabels([f'{h:02d}:00' for h in y_ticks])
                    
                    # Set date labels on x-axis
                    if len(dates) <= 15:
                        ax.set_xticks(dates)
                        ax.set_xticklabels(date_labels, rotation=45, ha='right')
                    else:
                        step = max(1, len(dates) // 10)
                        ax.set_xticks(list(dates)[::step])
                        ax.set_xticklabels(date_labels[::step], rotation=45, ha='right')
                    
                    ax.legend(loc='upper right')
                    ax.grid(True, alpha=0.3)
                    ax.set_facecolor('#f8f9fa')
                    plt.tight_layout()
                    st.pyplot(fig)
                    plt.close(fig)
                    
                    # Show summary stats
                    col_sun1, col_sun2, col_sun3 = st.columns(3)
                    with col_sun1:
                        avg_sunrise = f"{int(sunrise_hours.mean())}:{int((sunrise_hours.mean() % 1) * 60):02d}"
                        st.metric("Avg Sunrise", avg_sunrise)
                    with col_sun2:
                        avg_sunset = f"{int(sunset_hours.mean())}:{int((sunset_hours.mean() % 1) * 60):02d}"
                        st.metric("Avg Sunset", avg_sunset)
                    with col_sun3:
                        if 'Daylight_Hours' in summary_df.columns:
                            st.metric("Avg Daylight", f"{summary_df['Daylight_Hours'].mean():.1f} hrs")
            else:
                st.warning("No data in selected date range.")
            
            st.markdown("---")
            st.markdown("#### 📆 Calendar Month Averages")
            st.caption("Compare seasonal patterns across different months (Jan, Feb, Mar, etc.)")
            
            # Time of day selection for calendar month averages
            time_mode = st.selectbox(
                "Time of Day Filter",
                options=["24 Hours (All Day)", "Daytime Only", "Nighttime Only"],
                key="weather_calendar_time_mode",
                help="Daytime: between sunrise and sunset. Nighttime: before sunrise and after sunset. Uses actual sunrise/sunset times from weather data."
            )
            
            # Filter data based on time of day selection
            filtered_hourly = hourly_df.copy()
            
            if time_mode == "Daytime Only" or time_mode == "Nighttime Only":
                # Merge sunrise/sunset from daily_df
                if 'Sunrise' in daily_df.columns and 'Sunset' in daily_df.columns:
                    # Add Date column to hourly if not present
                    if 'Date' not in filtered_hourly.columns:
                        filtered_hourly['Date'] = pd.to_datetime(filtered_hourly['Timestamp']).dt.date
                    
                    daytime_mask = []
                    for idx, row in filtered_hourly.iterrows():
                        date = row['Date']
                        hour = row['Hour']
                        
                        # Get sunrise/sunset for this date
                        daily_row = daily_df[daily_df['Date'] == date]
                        if not daily_row.empty and pd.notna(daily_row.iloc[0].get('Sunrise')) and pd.notna(daily_row.iloc[0].get('Sunset')):
                            sunrise_hour = daily_row.iloc[0]['Sunrise'].hour
                            sunset_hour = daily_row.iloc[0]['Sunset'].hour
                            is_daytime = sunrise_hour <= hour <= sunset_hour
                        else:
                            # Default to 6 AM - 6 PM if no sunrise/sunset data
                            is_daytime = 6 <= hour <= 18
                        daytime_mask.append(is_daytime)
                    
                    if time_mode == "Daytime Only":
                        filtered_hourly = filtered_hourly[daytime_mask].copy()
                        st.caption("🌅 Showing daytime hours only (based on sunrise/sunset times)")
                    else:
                        filtered_hourly = filtered_hourly[~pd.Series(daytime_mask, index=filtered_hourly.index)].copy()
                        st.caption("🌙 Showing nighttime hours only (before sunrise and after sunset)")
                else:
                    # Fallback if no sunrise/sunset data
                    if time_mode == "Daytime Only":
                        filtered_hourly = filtered_hourly[(filtered_hourly['Hour'] >= 6) & (filtered_hourly['Hour'] <= 18)].copy()
                        st.caption("🌅 Showing daytime hours (6 AM - 6 PM, sunrise/sunset data not available)")
                    else:
                        filtered_hourly = filtered_hourly[(filtered_hourly['Hour'] < 6) | (filtered_hourly['Hour'] > 18)].copy()
                        st.caption("🌙 Showing nighttime hours (before 6 AM and after 6 PM)")
            
            fig = plot_weather_calendar_month_averages(filtered_hourly, daily_df, export_dir, show_plot=True)
            if fig:
                st.pyplot(fig)
            else:
                st.info("Select a date range spanning multiple months to see calendar averages.")
        
        else:  # Data Tables
            st.markdown("### 📋 Data Tables")
            
            with st.expander("📊 Hourly Data", expanded=True):
                st.dataframe(hourly_df, use_container_width=True)
            
            with st.expander("📅 Daily Data", expanded=True):
                # Format sunrise/sunset for display
                display_daily = daily_df.copy()
                if 'Sunrise' in display_daily.columns:
                    display_daily['Sunrise'] = display_daily['Sunrise'].dt.strftime('%H:%M')
                if 'Sunset' in display_daily.columns:
                    display_daily['Sunset'] = display_daily['Sunset'].dt.strftime('%H:%M')
                st.dataframe(display_daily, use_container_width=True)


if __name__ == "__main__":
    main()

