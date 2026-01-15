# 🔧 Developer Guide

**Solar Panel Monitoring System - Technical Documentation**

Version 1.0 | For Developers & Customizers

---

## 📋 Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Project Structure](#3-project-structure)
4. [Module Reference](#4-module-reference)
5. [Data Flow](#5-data-flow)
6. [Column Detection System](#6-column-detection-system)
7. [Calculations Module](#7-calculations-module)
8. [Visualizations Module](#8-visualizations-module)
9. [Data Quality Module](#9-data-quality-module)
10. [Weather API Module](#10-weather-api-module)
11. [Customization Guide](#11-customization-guide)
12. [Adding New Tabs](#12-adding-new-tabs)
13. [Adding New Column Types](#13-adding-new-column-types)
14. [Adding New Graphs](#14-adding-new-graphs)
15. [Deployment](#15-deployment)

---

## 1. System Overview

The Solar Panel Monitoring System is a **Streamlit-based web application** for analyzing solar panel performance data. It provides:

- CSV data parsing with auto-detection of column types
- Power, Performance Ratio (PR), and Specific Yield calculations
- Daily, monthly, and custom date range visualizations
- Data quality analysis (completeness, duplicates, range validation)
- Weather data integration via Open-Meteo API
- Export functionality for graphs and data

### Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Frontend/Backend | Streamlit | Web UI and server |
| Data Processing | Pandas, NumPy | DataFrame operations |
| Visualization | Matplotlib, Seaborn | Charts and graphs |
| Weather API | Open-Meteo | Historical weather data |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE (Streamlit)                   │
│                              app.py                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │   Sidebar   │  │    Tabs     │  │  Metrics    │  │   Graphs    │ │
│  │  (Config)   │  │ (10 views)  │  │  (Cards)    │  │  (Charts)   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘ │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
                              │
           ┌──────────────────┼───────────────────────┐
           ▼                  ▼                       ▼
┌─────────────────┐  ┌─────────────────┐    ┌─────────────────┐
│  data_parser.py │  │ calculations.py │    │ visualizations  │
│  ─────────────  │  │  ─────────────  │    │      .py        │
│  • parse_data() │  │  • power calc   │    │  ─────────────  │
│  • detect cols  │  │  • PR calc      │    │  • 40+ plotting │
│  • prepare data │  │  • yield calc   │    │    functions    │
└─────────────────┘  │  • daily/monthly│    └─────────────────┘
                     │    metrics      │
                     └─────────────────┘
                              │
           ┌──────────────────┼───────────────────────┐
           ▼                  ▼                       ▼
┌─────────────────┐  ┌─────────────────┐    ┌─────────────────┐
│ data_quality.py │  │  weather_api.py │    │    export.py    │
│  ─────────────  │  │  ─────────────  │    │  ─────────────  │
│  • completeness │  │  • Open-Meteo   │    │  • ZIP creation │
│  • validation   │  │  • coord parse  │    │  • CSV export   │
│  • duplicates   │  │  • data merge   │    └─────────────────┘
└─────────────────┘  └─────────────────┘
```

---

## 3. Project Structure

```
solar-monitoring/
├── app.py                      # Main Streamlit application (~2100 lines)
├── requirements.txt            # Python dependencies
├── generate_sample_data.py     # Sample data generator
│
├── modules/                    # Core functionality
│   ├── __init__.py
│   ├── data_parser.py          # CSV parsing & column detection
│   ├── calculations.py         # Power, PR, yield calculations
│   ├── data_quality.py         # Validation & completeness checks
│   ├── visualizations.py       # Graph generation (~2200 lines)
│   ├── weather_api.py          # Open-Meteo API integration
│   ├── weather_visualizations.py # Weather-specific graphs
│   └── export.py               # File export utilities
│
├── sample_data/                # Sample CSV files
│   └── generated_30day_data.csv
│
├── exports/                    # Generated files (gitignored)
│
├── docs/                       # Documentation assets
│   └── images/
│
├── USER_GUIDE.html             # End-user documentation
├── USER_GUIDE.md               # Markdown version
├── DEVELOPER_GUIDE.html        # Technical documentation (this document)
├── DEVELOPER_GUIDE.md          # Markdown version
└── README.md                   # Project overview
```

---

## 4. Module Reference

| Module | Lines | Functions | Purpose |
|--------|-------|-----------|---------|
| `data_parser.py` | ~285 | 8 | CSV parsing, column auto-detection, data preparation |
| `calculations.py` | ~430 | 13 | Power, PR, yield, metrics, operating hours |
| `data_quality.py` | ~425 | 7 | Completeness, validation, gap filling, duplicates |
| `visualizations.py` | ~2200 | 40+ | All chart generation for solar data |
| `weather_api.py` | ~300 | 5 | Open-Meteo API, coordinate parsing |
| `weather_visualizations.py` | ~450 | 7 | Weather-specific charts |
| `export.py` | ~120 | 5 | ZIP and CSV export utilities |

---

## 5. Data Flow

### 5.1 CSV Upload to Display

1. **User uploads CSV** via `st.file_uploader()` or pastes text
2. **parse_data()** reads CSV, auto-detects columns
3. **prepare_analysis_data()** standardizes column names, adds derived columns
4. **calculate_daily_metrics()** aggregates by date
5. **calculate_monthly_metrics()** aggregates by month
6. **Data stored in `st.session_state`** for persistence
7. **display_*() functions** render tabs with visualizations

### 5.2 Session State Keys

```python
st.session_state.data_loaded       # bool: True if data is loaded
st.session_state.analysis_df       # DataFrame: Processed data
st.session_state.column_mapping    # dict: Original → Standardized column names
st.session_state.daily_metrics     # DataFrame: Daily aggregates
st.session_state.monthly_metrics   # DataFrame: Monthly aggregates
st.session_state.nominal_power     # float: System kWp
st.session_state.temp_coeff        # float: Temperature coefficient
st.session_state.soc_threshold     # float: SoC threshold for PR
st.session_state.view_mode         # str: 'data_analysis' or 'weather_analysis'
```

---

## 6. Column Detection System

The system uses regex patterns to automatically detect column types from uploaded CSV files.

**Module:** `modules/data_parser.py`

### 6.1 Pattern Definitions

```python
COLUMN_PATTERNS = {
    'timestamp': [
        r'^timestamp$', r'^time$', r'^date$', r'^datetime$', 
        r'date_time', r'^dt$', r'reading_time', r'log_time'
    ],
    'current': [
        r'\bcurrent\b', r'^i$', r'dc[_\s]?current', r'^amps$',
        r'current.*\(a\)', r'\(a\)$'
    ],
    'voltage': [
        r'\bvoltage\b', r'^v$', r'dc[_\s]?voltage', r'^volts$',
        r'voltage.*\(v\)', r'\(v\)$', r'\(mv\)$'
    ],
    'irradiance': [
        r'irradiance', r'\bghi\b', r'\bpoa\b', r'solar_radiation',
        r'w/m2', r'w/m²', r'radiation'
    ],
    'temperature': [
        r'temperature', r'\btemp\b', r'cell[_\s]?temp', 
        r't[_\s]?cell', r'\(c\)$', r'°c'
    ],
    'soc': [
        r'\bsoc\b', r'battery[_\s]?soc', r'state[_\s]?of[_\s]?charge',
        r'battery.*%', r'charge[_\s]?state'
    ]
}
```

### 6.2 Adding New Column Types

To add a new column type (e.g., "humidity"):

```python
# 1. Add to COLUMN_PATTERNS in data_parser.py
COLUMN_PATTERNS['humidity'] = [
    r'\bhumidity\b', r'rh', r'relative[_\s]?humidity', r'%rh'
]

# 2. Update detect_all_columns() to include it
# (already loops through all keys in COLUMN_PATTERNS)

# 3. Update prepare_analysis_data() to handle standardization
if column_mapping['humidity']:
    result_df['Humidity_pct'] = df[column_mapping['humidity']]
```

---

## 7. Calculations Module

**Module:** `modules/calculations.py`

### 7.1 Core Functions

#### calculate_power(df)

Calculates measured power from current and voltage.

```python
# Formula: P = I × V (Watts)
df['Power_W'] = df['Current_A'] * df['Voltage_V']
```

#### calculate_expected_power(df, nominal_power_kw, temp_coefficient)

Calculates theoretical expected power based on irradiance and temperature.

```python
# Formula: P_expected = P_stc × (G / 1000) × [1 + γ × (T_cell - 25)]
# Where:
#   P_stc = Nominal power at STC (kW)
#   G = Irradiance (W/m²)
#   γ = Temperature coefficient (e.g., -0.004 for -0.4%/°C)
#   T_cell = Cell temperature (°C)
```

#### calculate_performance_ratio(df, nominal_power_kw, temp_coefficient)

Calculates Performance Ratio (PR) with optional SoC filtering.

```python
# Formula: PR = (Actual Energy / Expected Energy) × 100%
# 
# Returns dict with:
#   - 'pr': Performance Ratio percentage
#   - 'actual_energy_kwh': Total measured energy
#   - 'expected_energy_kwh': Total theoretical energy
#   - 'points_used': Number of data points
#   - 'points_excluded': Points excluded (high SoC)
```

#### calculate_daily_metrics(df, nominal_power_kw, temp_coefficient)

Aggregates data by date. Returns DataFrame with columns:

| Column | Description |
|--------|-------------|
| Date | Date of readings |
| Actual_Energy_kWh | Total energy generated |
| Expected_Energy_kWh | Theoretical energy |
| Performance_Ratio | Daily PR (%) |
| Avg_Irradiance | Average irradiance |
| Avg_Temperature | Average temperature |
| Operating_Hours | Hours with power > 0 |

#### calculate_monthly_metrics(df, nominal_power_kw, temp_coefficient)

Aggregates data by month. Similar structure to daily metrics plus:

- `Days_With_Data`: Number of days with readings
- `Avg_Daily_Energy_kWh`: Average daily energy for the month

---

## 8. Visualizations Module

**Module:** `modules/visualizations.py`

This is the largest module (~2200 lines) containing 40+ plotting functions.

### 8.1 Function Naming Convention

| Prefix | Purpose | Example |
|--------|---------|---------|
| `plot_daily_*` | Single day graphs | `plot_daily_power_irradiance()` |
| `plot_monthly_*` | Monthly aggregates | `plot_monthly_energy_bar()` |
| `plot_custom_*` | Custom date ranges | `plot_custom_range_power()` |
| `generate_*` | Batch generation | `generate_all_daily_graphs()` |

### 8.2 Standard Function Signature

```python
def plot_daily_power_irradiance(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot power and irradiance for a specific date.
    
    Args:
        df: DataFrame with 'Hour', 'Power_W', 'Irradiance_Wm2'
        date: Date string (YYYY-MM-DD)
        output_dir: Directory to save PNG
        show_plot: If True, return figure for Streamlit display
        
    Returns:
        Figure object if show_plot=True, else None
    """
```

### 8.3 Adding a New Graph

```python
# 1. Add function to visualizations.py
def plot_custom_my_metric(
    df: pd.DataFrame,
    output_dir: str,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Your plotting logic here
    ax.plot(df['Hour'], df['MyMetric'], color='#3498DB')
    ax.set_xlabel('Hour')
    ax.set_ylabel('My Metric')
    ax.set_title('My Custom Graph')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if output_dir:
        filepath = os.path.join(output_dir, "my_metric.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


# 2. Import in app.py
from modules.visualizations import plot_custom_my_metric

# 3. Call in appropriate display function
fig = plot_custom_my_metric(analysis_df, EXPORT_DIR, show_plot=True)
if fig:
    st.pyplot(fig)
```

---

## 9. Data Quality Module

**Module:** `modules/data_quality.py`

### 9.1 Key Functions

#### check_data_completeness()

```python
check_data_completeness(
    df: pd.DataFrame,
    expected_interval_minutes: Optional[int] = None,  # Auto-detected if None
    min_completeness_pct: float = 80.0,
    daytime_only: bool = True,
    daytime_start_hour: int = 6,
    daytime_end_hour: int = 18
) -> Dict
```

**Returns:**
- `completeness_pct`: Percentage of expected readings present
- `missing_periods`: List of gaps with start/end times
- `detected_interval`: Auto-detected data frequency

#### validate_data_ranges()

```python
validate_data_ranges(
    df: pd.DataFrame,
    voltage_range: Tuple[float, float] = (0, 60),
    current_range: Tuple[float, float] = (0, 15),
    irradiance_range: Tuple[float, float] = (0, 1400),
    temperature_range: Tuple[float, float] = (-10, 80),
    soc_range: Tuple[float, float] = (0, 100)
) -> Dict
```

Checks if values fall within physically realistic ranges.

#### get_data_quality_report()

Combines all checks into a comprehensive report dictionary.

---

## 10. Weather API Module

**Module:** `modules/weather_api.py`

### 10.1 Open-Meteo Integration

Uses the free Open-Meteo Historical Weather API. No API key required.

```python
# API Endpoint
BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

# Parameters requested
params = {
    "latitude": lat,
    "longitude": lon,
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "hourly": "temperature_2m,shortwave_radiation,direct_radiation,diffuse_radiation",
    "daily": "sunrise,sunset,temperature_2m_max,temperature_2m_min,shortwave_radiation_sum",
    "timezone": "auto"
}
```

### 10.2 Data Returned

| Hourly | Daily |
|--------|-------|
| Temperature_C | Sunrise/Sunset |
| Irradiance_Wm2 (GHI) | Temp_Max_C / Temp_Min_C |
| Direct_Irradiance_Wm2 | Total_Irradiance_kWhm2 |
| Diffuse_Irradiance_Wm2 | Daylight_Hours |

### 10.3 Coordinate Parsing

```python
extract_coordinates_from_url(url: str) -> Tuple[Optional[float], Optional[float]]

# Supports:
# - Google Maps URLs: @22.2793566,114.1628124,17z
# - Direct coordinates in URL params
```

---

## 11. Customization Guide

### 11.1 Changing Default Values

Edit these values in `app.py`:

```python
# Sidebar defaults (in main() function)
nominal_power = st.number_input(
    "Nominal Power (kWp)",
    min_value=0.1,
    max_value=100.0,
    value=0.3,          # <-- Change default
    step=0.1
)

temp_coeff = st.number_input(
    "Temperature Coefficient (%/°C)",
    min_value=-1.0,
    max_value=0.0,
    value=-0.4,         # <-- Change default
    step=0.01
)
```

### 11.2 Changing Colors

Global color scheme in `visualizations.py`:

```python
# Common colors used throughout
COLORS = {
    'power': '#FF6B6B',      # Red
    'irradiance': '#FFD93D', # Yellow/Orange
    'temperature': '#6BCB77', # Green
    'voltage': '#4D96FF',    # Blue
    'current': '#9B59B6',    # Purple
    'soc': '#1ABC9C',        # Teal
    'pr': '#3498DB',         # Light Blue
}
```

### 11.3 Changing Export Settings

```python
# In visualizations.py, change DPI for higher quality exports
fig.savefig(filepath, dpi=150, bbox_inches='tight')
#                     ^^^^^^^^ Increase to 300 for print quality
```

---

## 12. Adding New Tabs

### Step-by-Step Guide

#### Step 1: Update Tab List in app.py

```python
# Find the st.tabs() call in display_analysis_results()
tab1, tab2, tab3, ..., tabN, tabNEW = st.tabs([
    "📈 Daily Graphs",
    "📊 Monthly Graphs",
    ...
    "📈 Custom Metrics",
    "🆕 My New Tab",      # <-- Add your tab
    "💾 Export All"
])
```

#### Step 2: Create Display Function

```python
def display_my_new_tab(analysis_df: pd.DataFrame, export_dir: str):
    """Display my new feature."""
    
    st.subheader("🆕 My New Feature")
    st.info("Description of what this tab does.")
    
    # Your UI components here
    selected_option = st.selectbox("Choose an option", ["A", "B", "C"])
    
    # Your visualizations
    fig, ax = plt.subplots(figsize=(10, 5))
    # ... plotting code ...
    st.pyplot(fig)
    plt.close(fig)
    
    # Data table
    with st.expander("View Data"):
        st.dataframe(analysis_df.head(100))
```

#### Step 3: Call Display Function

```python
with tabNEW:
    display_my_new_tab(analysis_df, EXPORT_DIR)
```

---

## 13. Adding New Column Types

#### Step 1: Add Pattern to data_parser.py

```python
COLUMN_PATTERNS['wind_speed'] = [
    r'\bwind\b', r'wind[_\s]?speed', r'ws', r'm/s'
]
```

#### Step 2: Update prepare_analysis_data()

```python
# In prepare_analysis_data() function
if column_mapping.get('wind_speed'):
    result_df['Wind_Speed_ms'] = df[column_mapping['wind_speed']]
```

#### Step 3: Update get_available_columns()

```python
return {
    ...
    'has_wind_speed': column_mapping.get('wind_speed') is not None,
}
```

---

## 14. Adding New Graphs

### Template for New Visualization

```python
def plot_my_custom_chart(
    df: pd.DataFrame,
    date: str = None,
    output_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a custom chart.
    
    Args:
        df: Input DataFrame
        date: Optional date filter (YYYY-MM-DD)
        output_dir: Directory to save PNG
        show_plot: Return figure for Streamlit
        
    Returns:
        Figure if show_plot=True
    """
    if df is None or df.empty:
        return None
    
    # Filter by date if provided
    if date:
        plot_df = df[df['Date'] == date].copy()
    else:
        plot_df = df.copy()
    
    if plot_df.empty:
        return None
    
    # Create figure
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Plot data
    ax.plot(
        plot_df['X_Column'],
        plot_df['Y_Column'],
        color='#3498DB',
        linewidth=2,
        marker='o',
        markersize=4,
        label='My Data'
    )
    
    # Styling
    ax.set_xlabel('X Label', fontsize=11)
    ax.set_ylabel('Y Label', fontsize=11)
    ax.set_title('My Chart Title', fontsize=13, fontweight='bold')
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    
    # Save to file
    if output_dir:
        filepath = os.path.join(output_dir, "my_custom_chart.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    # Return or close
    if show_plot:
        return fig
    
    plt.close(fig)
    return None
```

---

## 15. Deployment

### 15.1 Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py

# Run with specific port
streamlit run app.py --server.port 8080
```

### 15.2 requirements.txt

```
streamlit>=1.28.0
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.6.0
seaborn>=0.12.0
requests>=2.28.0
```

### 15.3 Streamlit Cloud Deployment

1. Push code to GitHub
2. Go to [streamlit.io/cloud](https://streamlit.io/cloud)
3. Connect your GitHub repository
4. Set `app.py` as the main file
5. Deploy!

> **💡 Tip:** For Streamlit Cloud, make sure all required packages are in `requirements.txt` and avoid any system-level dependencies.

### 15.4 Docker Deployment

**Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.headless=true"]
```

**Build and run:**

```bash
# Build
docker build -t solar-monitoring .

# Run
docker run -p 8501:8501 solar-monitoring
```

---

## Footer

🌞 Solar Panel Monitoring System - Developer Guide  
Version 1.0 | January 2026
