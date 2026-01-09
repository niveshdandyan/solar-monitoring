"""
Data Quality Module
Functions for data completeness, validation, gap filling, and duplicate detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def check_data_completeness(
    df: pd.DataFrame,
    expected_interval_minutes: int = 5,
    min_completeness_pct: float = 80.0
) -> Dict:
    """
    Check data completeness and identify missing data periods.
    
    Args:
        df: DataFrame with Timestamp column
        expected_interval_minutes: Expected data logging interval
        min_completeness_pct: Minimum acceptable completeness percentage
    
    Returns:
        Dictionary with completeness metrics and missing periods
    """
    if 'Timestamp' not in df.columns or len(df) < 2:
        return {
            'overall_completeness_pct': 0,
            'missing_periods': [],
            'is_complete': False,
            'error': 'Insufficient data'
        }
    
    df_sorted = df.sort_values('Timestamp').copy()
    
    # Calculate time range
    start_time = df_sorted['Timestamp'].min()
    end_time = df_sorted['Timestamp'].max()
    total_duration_minutes = (end_time - start_time).total_seconds() / 60
    
    # Expected vs actual data points
    expected_points = total_duration_minutes / expected_interval_minutes
    actual_points = len(df_sorted)
    
    completeness_pct = (actual_points / expected_points) * 100 if expected_points > 0 else 0
    
    # Find missing periods (gaps > 2x expected interval)
    df_sorted['time_diff'] = df_sorted['Timestamp'].diff()
    gap_threshold = pd.Timedelta(minutes=expected_interval_minutes * 2)
    
    gaps = df_sorted[df_sorted['time_diff'] > gap_threshold].copy()
    
    missing_periods = []
    for idx, row in gaps.iterrows():
        gap_start = df_sorted.loc[idx - 1, 'Timestamp'] if idx > 0 else row['Timestamp']
        gap_end = row['Timestamp']
        gap_duration = row['time_diff']
        
        missing_periods.append({
            'start': gap_start,
            'end': gap_end,
            'duration_minutes': gap_duration.total_seconds() / 60
        })
    
    # Daily completeness
    daily_completeness = []
    if 'Date' in df_sorted.columns:
        for date, day_df in df_sorted.groupby('Date'):
            day_start = day_df['Timestamp'].min()
            day_end = day_df['Timestamp'].max()
            day_duration = (day_end - day_start).total_seconds() / 60
            expected_day_points = day_duration / expected_interval_minutes if day_duration > 0 else 1
            day_completeness = (len(day_df) / expected_day_points) * 100
            
            daily_completeness.append({
                'date': date,
                'data_points': len(day_df),
                'completeness_pct': min(day_completeness, 100),
                'is_complete': day_completeness >= min_completeness_pct
            })
    
    return {
        'overall_completeness_pct': min(completeness_pct, 100),
        'expected_points': int(expected_points),
        'actual_points': actual_points,
        'missing_periods': missing_periods,
        'missing_periods_count': len(missing_periods),
        'daily_completeness': daily_completeness,
        'is_complete': completeness_pct >= min_completeness_pct,
        'data_range': {
            'start': start_time,
            'end': end_time,
            'duration_hours': total_duration_minutes / 60
        }
    }


def validate_data_ranges(
    df: pd.DataFrame,
    voltage_range: Tuple[float, float] = (0, 60),
    current_range: Tuple[float, float] = (0, 15),
    irradiance_range: Tuple[float, float] = (0, 1400),
    temperature_range: Tuple[float, float] = (-10, 80),
    soc_range: Tuple[float, float] = (0, 100)
) -> Dict:
    """
    Validate data is within expected ranges and flag suspicious readings.
    
    Args:
        df: DataFrame with sensor columns
        voltage_range: Valid voltage range (min, max) in V
        current_range: Valid current range (min, max) in A
        irradiance_range: Valid irradiance range (min, max) in W/m²
        temperature_range: Valid temperature range (min, max) in °C
        soc_range: Valid SoC range (min, max) in %
    
    Returns:
        Dictionary with validation results and suspicious readings
    """
    validation_results = {
        'total_rows': len(df),
        'suspicious_readings': [],
        'column_stats': {}
    }
    
    # Validation rules
    rules = {
        'Voltage_V': voltage_range,
        'Current_A': current_range,
        'Irradiance_Wm2': irradiance_range,
        'Temperature_C': temperature_range,
        'SoC_pct': soc_range
    }
    
    for col, (min_val, max_val) in rules.items():
        if col not in df.columns:
            continue
        
        # Find out-of-range values
        out_of_range = df[(df[col] < min_val) | (df[col] > max_val)]
        
        # Find null values
        null_values = df[df[col].isna()]
        
        # Find sudden jumps (diff > 50% of range)
        range_size = max_val - min_val
        df_sorted = df.sort_values('Timestamp') if 'Timestamp' in df.columns else df
        diff = df_sorted[col].diff().abs()
        sudden_jumps = df_sorted[diff > range_size * 0.5]
        
        validation_results['column_stats'][col] = {
            'min': df[col].min(),
            'max': df[col].max(),
            'mean': df[col].mean(),
            'null_count': len(null_values),
            'out_of_range_count': len(out_of_range),
            'sudden_jump_count': len(sudden_jumps),
            'valid_range': (min_val, max_val)
        }
        
        # Add suspicious readings
        for idx in out_of_range.index:
            validation_results['suspicious_readings'].append({
                'timestamp': df.loc[idx, 'Timestamp'] if 'Timestamp' in df.columns else idx,
                'column': col,
                'value': df.loc[idx, col],
                'reason': 'Out of range',
                'valid_range': f"{min_val} - {max_val}"
            })
    
    validation_results['suspicious_count'] = len(validation_results['suspicious_readings'])
    validation_results['is_valid'] = validation_results['suspicious_count'] == 0
    
    return validation_results


def fill_data_gaps(
    df: pd.DataFrame,
    max_gap_points: int = 5,
    method: str = 'linear',
    columns_to_fill: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, Dict]:
    """
    Fill small data gaps using interpolation.
    
    Args:
        df: DataFrame with Timestamp and data columns
        max_gap_points: Maximum consecutive missing points to fill
        method: Interpolation method ('linear', 'polynomial', 'time')
        columns_to_fill: Specific columns to interpolate (None = all numeric)
    
    Returns:
        Tuple of (filled DataFrame, info dict)
    """
    if 'Timestamp' not in df.columns:
        return df, {'error': 'No Timestamp column'}
    
    result = df.sort_values('Timestamp').copy()
    
    # Determine columns to fill
    if columns_to_fill is None:
        columns_to_fill = result.select_dtypes(include=[np.number]).columns.tolist()
    
    fill_info = {
        'method': method,
        'columns_filled': [],
        'points_filled': 0
    }
    
    for col in columns_to_fill:
        if col not in result.columns:
            continue
        
        # Count missing before
        missing_before = result[col].isna().sum()
        
        # Create mask for small gaps
        is_null = result[col].isna()
        gap_groups = (is_null != is_null.shift()).cumsum()
        gap_sizes = is_null.groupby(gap_groups).transform('sum')
        
        # Only fill small gaps
        fill_mask = is_null & (gap_sizes <= max_gap_points)
        
        if fill_mask.any():
            if method == 'time' and 'Timestamp' in result.columns:
                result[col] = result[col].interpolate(method='time', limit=max_gap_points)
            else:
                result[col] = result[col].interpolate(method=method, limit=max_gap_points)
            
            # Mark interpolated rows
            if 'is_interpolated' not in result.columns:
                result['is_interpolated'] = False
            result.loc[fill_mask, 'is_interpolated'] = True
            
            missing_after = result[col].isna().sum()
            points_filled = missing_before - missing_after
            
            fill_info['columns_filled'].append({
                'column': col,
                'points_filled': points_filled
            })
            fill_info['points_filled'] += points_filled
    
    return result, fill_info


def detect_duplicates(df: pd.DataFrame) -> Dict:
    """
    Detect duplicate timestamps in the data.
    
    Args:
        df: DataFrame with Timestamp column
    
    Returns:
        Dictionary with duplicate info and affected rows
    """
    if 'Timestamp' not in df.columns:
        return {'error': 'No Timestamp column', 'duplicates': []}
    
    # Find duplicate timestamps
    duplicated_mask = df['Timestamp'].duplicated(keep=False)
    duplicates = df[duplicated_mask].copy()
    
    # Group by timestamp to see duplicate groups
    duplicate_groups = []
    if len(duplicates) > 0:
        for ts, group in duplicates.groupby('Timestamp'):
            duplicate_groups.append({
                'timestamp': ts,
                'count': len(group),
                'row_indices': group.index.tolist()
            })
    
    return {
        'has_duplicates': len(duplicates) > 0,
        'duplicate_count': len(duplicates),
        'unique_duplicate_timestamps': len(duplicate_groups),
        'duplicate_groups': duplicate_groups,
        'duplicate_rows': duplicates
    }


def remove_duplicates(
    df: pd.DataFrame,
    keep: str = 'first',
    columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, int]:
    """
    Remove duplicate rows.
    
    Args:
        df: DataFrame
        keep: Which duplicate to keep ('first', 'last', or False for none)
        columns: Columns to consider for duplicates (None = Timestamp only)
    
    Returns:
        Tuple of (cleaned DataFrame, count of removed rows)
    """
    if columns is None:
        columns = ['Timestamp'] if 'Timestamp' in df.columns else None
    
    original_count = len(df)
    result = df.drop_duplicates(subset=columns, keep=keep)
    removed_count = original_count - len(result)
    
    return result, removed_count


def get_data_quality_report(df: pd.DataFrame) -> Dict:
    """
    Generate comprehensive data quality report.
    
    Args:
        df: DataFrame with sensor data
    
    Returns:
        Complete data quality report dictionary
    """
    report = {
        'total_rows': len(df),
        'date_range': None,
        'completeness': check_data_completeness(df),
        'validation': validate_data_ranges(df),
        'duplicates': detect_duplicates(df)
    }
    
    if 'Timestamp' in df.columns:
        report['date_range'] = {
            'start': df['Timestamp'].min(),
            'end': df['Timestamp'].max()
        }
    
    # Overall quality score
    completeness_score = report['completeness'].get('overall_completeness_pct', 0)
    validation_score = 100 - (report['validation'].get('suspicious_count', 0) / max(len(df), 1) * 100)
    duplicate_score = 100 - (report['duplicates'].get('duplicate_count', 0) / max(len(df), 1) * 100)
    
    report['quality_score'] = (completeness_score + validation_score + duplicate_score) / 3
    report['quality_grade'] = (
        'A' if report['quality_score'] >= 90 else
        'B' if report['quality_score'] >= 80 else
        'C' if report['quality_score'] >= 70 else
        'D' if report['quality_score'] >= 60 else 'F'
    )
    
    return report
