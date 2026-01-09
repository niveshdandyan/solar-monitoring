"""
🌞 Solar Panel Monitoring System
A comprehensive analysis and visualization tool for solar panel performance.
"""

import streamlit as st
import pandas as pd
import numpy as np
import os
from datetime import datetime

# Import custom modules
from modules.data_parser import (
    parse_data, 
    prepare_analysis_data, 
    detect_all_columns,
    get_available_columns
)
from modules.calculations import (
    calculate_power,
    calculate_expected_power,
    calculate_daily_metrics,
    calculate_monthly_metrics,
    calculate_performance_ratio,
    get_all_anomalies,
    detect_power_dip_anomalies,
    detect_voltage_clipping,
    detect_current_limiting,
    detect_voltage_anomaly,
    detect_current_anomaly
)
from modules.visualizations import (
    plot_daily_power_irradiance,
    plot_daily_power_irradiance_soc,
    plot_daily_temperature_effect,
    plot_daily_voltage_irradiance,
    plot_daily_current_irradiance,
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
    get_anomaly_summary
)
from modules.export import (
    get_export_directory,
    list_exported_files,
    create_zip_archive,
    clean_export_directory,
    get_export_summary,
    export_dataframe_to_csv
)
from modules.data_quality import (
    check_data_completeness,
    validate_data_ranges,
    fill_data_gaps,
    detect_duplicates,
    get_data_quality_report
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

# Initialize session state
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

# Get export directory
EXPORT_DIR = get_export_directory(os.path.join(os.path.dirname(__file__), "exports"))


def main():
    # Header
    st.markdown('<h1 class="main-header">🌞 Solar Panel Monitoring System</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Comprehensive Performance Analysis & Visualization</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ System Configuration")
        
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
        st.subheader("⚡ MPP Settings")
        st.caption("For anomaly detection")
        
        vmpp = st.number_input(
            "Vmpp (V)",
            min_value=1.0,
            max_value=100.0,
            value=30.0,
            step=0.5,
            help="Maximum Power Point Voltage - used for voltage anomaly detection (outside 80-110%)"
        )
        
        impp = st.number_input(
            "Impp (A)",
            min_value=0.1,
            max_value=50.0,
            value=8.0,
            step=0.1,
            help="Maximum Power Point Current - used for current anomaly detection (>110%)"
        )
        
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
                    daily_metrics = calculate_daily_metrics(
                        analysis_df, 
                        nominal_power, 
                        temp_coeff_decimal
                    )
                    monthly_metrics = calculate_monthly_metrics(
                        analysis_df, 
                        nominal_power, 
                        temp_coeff_decimal
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
                    
                    st.success("✅ Data processed successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error processing data: {str(e)}")
                    st.exception(e)
    
    # Display results if data is loaded
    if st.session_state.data_loaded:
        display_analysis_results()


def display_analysis_results():
    """Display all analysis results and visualizations."""
    
    analysis_df = st.session_state.analysis_df
    daily_metrics = st.session_state.daily_metrics
    monthly_metrics = st.session_state.monthly_metrics
    nominal_power = st.session_state.nominal_power
    temp_coeff = st.session_state.temp_coeff
    soc_threshold = st.session_state.soc_threshold
    
    # Overview metrics
    st.subheader("📊 Performance Overview")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
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
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📈 Daily Graphs", 
        "📊 PR & Yield Analysis", 
        "🌡️ Temperature Effects",
        "📅 Calendar View",
        "🔍 Anomaly Analysis",
        "📋 Data Quality",
        "💾 Export All"
    ])
    
    with tab1:
        display_daily_graphs(analysis_df, EXPORT_DIR)
    
    with tab2:
        display_pr_yield_graphs(analysis_df, daily_metrics, monthly_metrics, EXPORT_DIR)
    
    with tab3:
        display_temperature_graphs(analysis_df, EXPORT_DIR)
    
    with tab4:
        display_calendar_view(daily_metrics)
    
    with tab5:
        display_anomaly_analysis(analysis_df, vmpp, impp)
    
    with tab6:
        display_data_quality(analysis_df)
    
    with tab7:
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


def display_pr_yield_graphs(analysis_df, daily_metrics, monthly_metrics, export_dir):
    """Display PR and Yield analysis graphs."""
    
    st.subheader("📊 Performance Ratio & Yield Analysis")
    
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


def display_calendar_view(daily_metrics):
    """Display calendar view with color-coded daily metrics and anomaly detection."""
    
    st.subheader("📅 Calendar View - Daily Performance")
    
    if len(daily_metrics) == 0:
        st.warning("No daily metrics available.")
        return
    
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
    
    calendar_type = st.radio(
        "Select Calendar View",
        options=['energy', 'pr', 'anomaly'],
        format_func=lambda x: {
            'energy': '⚡ Daily Energy (kWh)',
            'pr': '📊 Performance Ratio (%)',
            'anomaly': '🔍 Anomaly Status'
        }[x],
        horizontal=True
    )
    
    fig = plot_calendar_heatmap(daily_metrics, metric=calendar_type, show_plot=True)
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
    
    st.subheader("💾 Export All Graphs")
    
    st.markdown("""
    Generate and download all graphs as high-resolution PNG images.
    
    **Graph Resolution:** 1400×700 pixels (150 DPI)  
    **Filename Format:** `YYYY-MM-DD_Graph_Type.png`
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🗑️ Clean Export Directory", use_container_width=True):
            clean_export_directory(export_dir)
            st.success("Export directory cleaned!")
    
    with col2:
        if st.button("📥 Generate All Graphs", type="primary", use_container_width=True):
            with st.spinner("Generating all graphs..."):
                # Clean first
                clean_export_directory(export_dir)
                
                # Generate daily graphs
                daily_files = generate_all_daily_graphs(analysis_df, export_dir)
                
                # Generate monthly graphs
                monthly_files = generate_all_monthly_graphs(
                    analysis_df, 
                    daily_metrics, 
                    monthly_metrics, 
                    export_dir
                )
                
                all_files = daily_files + monthly_files
                
                st.success(f"✅ Generated {len(all_files)} graphs!")
                
                # List files
                files = list_exported_files(export_dir)
                st.markdown(get_export_summary(files))
                
                # Create ZIP
                if len(all_files) > 0:
                    zip_path = create_zip_archive(all_files, export_dir)
                    
                    with open(zip_path, 'rb') as f:
                        st.download_button(
                            label="📦 Download All as ZIP",
                            data=f,
                            file_name=os.path.basename(zip_path),
                            mime="application/zip",
                            use_container_width=True
                        )
    
    # Show existing exports
    st.markdown("---")
    st.subheader("📂 Exported Files")
    
    files = list_exported_files(export_dir)
    
    if len(files['daily']) + len(files['monthly']) == 0:
        st.info("No exported files yet. Click 'Generate All Graphs' to create them.")
    else:
        tab1, tab2 = st.tabs(["Daily Graphs", "Monthly Graphs"])
        
        with tab1:
            if files['daily']:
                for f in files['daily']:
                    st.text(os.path.basename(f))
            else:
                st.info("No daily graphs exported yet.")
        
        with tab2:
            if files['monthly']:
                for f in files['monthly']:
                    st.text(os.path.basename(f))
            else:
                st.info("No monthly graphs exported yet.")
    
    # Export data as CSV
    st.markdown("---")
    st.subheader("📊 Export Data")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = analysis_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Processed Data (CSV)",
            data=csv_data,
            file_name="solar_data_processed.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        csv_daily = daily_metrics.to_csv(index=False)
        st.download_button(
            label="📥 Download Daily Metrics (CSV)",
            data=csv_daily,
            file_name="daily_metrics.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with col3:
        if len(monthly_metrics) > 0:
            csv_monthly = monthly_metrics.to_csv(index=False)
            st.download_button(
                label="📥 Download Monthly Metrics (CSV)",
                data=csv_monthly,
                file_name="monthly_metrics.csv",
                mime="text/csv",
                use_container_width=True
            )


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


if __name__ == "__main__":
    main()

