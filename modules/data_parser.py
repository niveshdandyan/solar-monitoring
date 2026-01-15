"""
Data Parser Module
Handles CSV/text parsing with smart column detection
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple
import re


# Column name patterns for auto-detection
# Using word boundaries and more specific patterns to avoid false positives
COLUMN_PATTERNS = {
    'timestamp': [
        r'^timestamp$', r'^time$', r'^date$', r'^datetime$', r'date_time', r'^dt$', 
        r'reading_time', r'log_time', r'record_time', r'timestamp'
    ],
    'current': [
        r'\bcurrent\b', r'^i$', r'dc[_\s]?current', r'i[_\s]?dc', r'^amps$', r'^amp$',
        r'current.*\(a\)', r'\(a\)$', r'dc.*current'
    ],
    'voltage': [
        r'\bvoltage\b', r'^v$', r'dc[_\s]?voltage', r'v[_\s]?dc', r'^volts$', r'^volt$',
        r'voltage.*\(v\)', r'\(v\)$', r'voltage.*\(mv\)', r'\(mv\)$'
    ],
    'irradiance': [
        r'irradiance', r'\bghi\b', r'\bpoa\b', r'solar_radiation', r'w/m2', r'w/m²',
        r'radiation', r'insolation', r'\birr\b', r'g\s*\(w/m'
    ],
    'temperature': [
        r'temperature', r'\btemp\b', r'cell[_\s]?temp', r'module[_\s]?temp',
        r't[_\s]?cell', r'tcell', r'panel[_\s]?temp', r'\(c\)$', r'\(°c\)$', r'°c'
    ],
    'soc': [
        r'\bsoc\b', r'battery[_\s]?soc', r'state[_\s]?of[_\s]?charge', r'battery.*%',
        r'charge[_\s]?state', r'batt[_\s]?soc'
    ]
}



def detect_column(df: pd.DataFrame, column_type: str) -> Optional[str]:
    """
    Detect which column in the dataframe matches the specified column type.
    
    Args:
        df: Input dataframe
        column_type: One of 'timestamp', 'current', 'voltage', 'irradiance', 'temperature', 'soc'
    
    Returns:
        Column name if found, None otherwise
    """
    patterns = COLUMN_PATTERNS.get(column_type, [])
    
    for col in df.columns:
        col_lower = col.lower().strip()
        for pattern in patterns:
            if re.search(pattern, col_lower):
                return col
    
    return None


def detect_all_columns(df: pd.DataFrame) -> Dict[str, Optional[str]]:
    """
    Detect all required columns in the dataframe.
    
    Returns:
        Dictionary mapping column type to actual column name (or None if not found)
    """
    detected = {}
    for col_type in COLUMN_PATTERNS.keys():
        detected[col_type] = detect_column(df, col_type)
    return detected


def detect_voltage_unit(df: pd.DataFrame, voltage_col: str) -> str:
    """
    Detect if voltage is in V or mV based on typical values.
    Solar panels typically produce 20-50V, so values > 1000 suggest mV
    """
    if voltage_col is None or voltage_col not in df.columns:
        return 'V'
    
    median_voltage = df[voltage_col].median()
    
    # If median > 500, likely in mV (typical panel voltage 20-50V = 20000-50000 mV)
    if median_voltage > 500:
        return 'mV'
    return 'V'


def parse_data(file_content, file_type: str = 'csv') -> Tuple[pd.DataFrame, Dict[str, Optional[str]], Dict[str, str]]:
    """
    Parse uploaded file and detect columns.
    
    Args:
        file_content: File content (can be uploaded file or string)
        file_type: 'csv' or 'text'
    
    Returns:
        Tuple of (processed_dataframe, column_mapping, messages)
    """
    messages = {}
    
    # Read the data
    try:
        if hasattr(file_content, 'read'):
            df = pd.read_csv(file_content)
        else:
            from io import StringIO
            df = pd.read_csv(StringIO(file_content))
    except Exception as e:
        raise ValueError(f"Error parsing file: {str(e)}")
    
    # Detect columns
    column_mapping = detect_all_columns(df)
    
    # Report detection results
    for col_type, col_name in column_mapping.items():
        if col_name:
            messages[col_type] = f"✅ Detected '{col_name}' as {col_type}"
        else:
            messages[col_type] = f"⚠️ Could not detect {col_type} column"
    
    # Parse timestamp - detect format first
    if column_mapping['timestamp']:
        ts_col = df[column_mapping['timestamp']]
        parsed = None
        
        # Check first value to detect format
        first_val = str(ts_col.iloc[0]).strip()
        
        # Detect if format is YYYY-... (ISO format) or D/M/YYYY or M/D/YYYY
        use_dayfirst = False
        if first_val and len(first_val) >= 8:
            # If starts with 4-digit year, it's ISO format (YYYY-MM-DD)
            if first_val[:4].isdigit() and len(first_val[:4]) == 4 and int(first_val[:4]) > 1900:
                use_dayfirst = False  # ISO format, don't use dayfirst
            # If contains / and doesn't start with year, check if it's D/M/YYYY
            elif '/' in first_val:
                parts = first_val.split()[0].split('/')  # Get date part
                if len(parts) >= 3:
                    # If last part is 4-digit year, and first part could be day (1-31)
                    if len(parts[-1]) == 4 and parts[-1].isdigit():
                        first_num = int(parts[0]) if parts[0].isdigit() else 0
                        # If first number > 12, it must be day (D/M/YYYY format)
                        if first_num > 12:
                            use_dayfirst = True
                        # If first number <= 12, assume D/M/YYYY for non-US format
                        else:
                            use_dayfirst = True  # Assume European format
        
        try:
            if use_dayfirst:
                parsed = pd.to_datetime(ts_col, dayfirst=True)
                messages['date_format'] = "📅 Parsed dates with day-first format (D/M/YYYY)"
            else:
                parsed = pd.to_datetime(ts_col)
                messages['date_format'] = "📅 Parsed dates with standard format (YYYY-MM-DD)"
        except Exception as e:
            # Fallback: try dayfirst if default fails
            try:
                parsed = pd.to_datetime(ts_col, dayfirst=True)
                messages['date_format'] = "📅 Parsed dates with day-first fallback"
            except Exception as e2:
                messages['timestamp_parse'] = f"⚠️ Could not parse timestamp: {str(e)}"
        
        if parsed is not None:
            df['parsed_timestamp'] = parsed
            df = df.sort_values('parsed_timestamp')
    
    # Handle voltage unit conversion
    if column_mapping['voltage']:
        voltage_unit = detect_voltage_unit(df, column_mapping['voltage'])
        if voltage_unit == 'mV':
            messages['voltage_unit'] = f"🔄 Detected mV, converting to V"
            df[column_mapping['voltage']] = df[column_mapping['voltage']] / 1000
        else:
            messages['voltage_unit'] = f"✅ Voltage already in V"
    
    # Detect data frequency
    if 'parsed_timestamp' in df.columns and len(df) > 1:
        time_diffs = df['parsed_timestamp'].diff().dropna()
        median_diff = time_diffs.median()
        
        if median_diff.total_seconds() < 120:  # < 2 minutes
            freq_str = f"{int(median_diff.total_seconds())} seconds"
        elif median_diff.total_seconds() < 7200:  # < 2 hours
            freq_str = f"{int(median_diff.total_seconds() / 60)} minutes"
        else:
            freq_str = f"{median_diff.total_seconds() / 3600:.1f} hours"
        
        messages['frequency'] = f"📊 Data frequency: ~{freq_str}"
    
    return df, column_mapping, messages


def prepare_analysis_data(df: pd.DataFrame, column_mapping: Dict[str, Optional[str]]) -> pd.DataFrame:
    """
    Prepare data for analysis by creating standardized columns.
    """
    analysis_df = df.copy()
    
    # Create standardized columns
    if column_mapping['timestamp'] and 'parsed_timestamp' in df.columns:
        analysis_df['Timestamp'] = df['parsed_timestamp']
        analysis_df['Date'] = analysis_df['Timestamp'].dt.date
        analysis_df['Time'] = analysis_df['Timestamp'].dt.time
        analysis_df['Hour'] = analysis_df['Timestamp'].dt.hour
        analysis_df['Month'] = analysis_df['Timestamp'].dt.to_period('M')
    
    if column_mapping['current']:
        analysis_df['Current_A'] = pd.to_numeric(df[column_mapping['current']], errors='coerce')
    
    if column_mapping['voltage']:
        analysis_df['Voltage_V'] = pd.to_numeric(df[column_mapping['voltage']], errors='coerce')
    
    if column_mapping['irradiance']:
        analysis_df['Irradiance_Wm2'] = pd.to_numeric(df[column_mapping['irradiance']], errors='coerce')
    
    if column_mapping['temperature']:
        analysis_df['Temperature_C'] = pd.to_numeric(df[column_mapping['temperature']], errors='coerce')
    
    if column_mapping['soc']:
        analysis_df['SoC_pct'] = pd.to_numeric(df[column_mapping['soc']], errors='coerce')
    
    return analysis_df


def get_available_columns(column_mapping: Dict[str, Optional[str]]) -> Dict[str, bool]:
    """
    Return which data columns are available for analysis.
    """
    return {
        'has_current': column_mapping['current'] is not None,
        'has_voltage': column_mapping['voltage'] is not None,
        'has_irradiance': column_mapping['irradiance'] is not None,
        'has_temperature': column_mapping['temperature'] is not None,
        'has_soc': column_mapping['soc'] is not None,
        'has_timestamp': column_mapping['timestamp'] is not None,
    }


def get_extra_columns(df: pd.DataFrame, column_mapping: Dict[str, Optional[str]]) -> list:
    """
    Get list of extra columns that are not part of the standard detected columns.
    Only returns numeric columns that can be plotted.
    
    Args:
        df: The dataframe with all columns
        column_mapping: Dictionary of detected standard columns
        
    Returns:
        List of extra column names (numeric only)
    """
    # Get all detected standard columns (values that are not None)
    standard_cols = set()
    for col_type, col_name in column_mapping.items():
        if col_name is not None:
            standard_cols.add(col_name)
    
    # Also exclude common system columns
    exclude_patterns = [
        'parsed_timestamp', 'Timestamp', 'Date', 'Time', 'Hour', 'Month',
        'Power_W', 'Current_A', 'Voltage_V', 'Irradiance_Wm2', 'Temperature_C', 'SoC_pct'
    ]
    
    extra_cols = []
    for col in df.columns:
        # Skip if it's a standard detected column
        if col in standard_cols:
            continue
        # Skip if it matches exclude patterns
        if col in exclude_patterns:
            continue
        # Only include numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            extra_cols.append(col)
    
    return extra_cols
