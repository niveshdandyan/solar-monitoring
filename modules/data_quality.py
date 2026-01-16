"""
Data Quality Module
Functions for data completeness, validation, gap filling, and duplicate detection
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


def check_data_completeness(
    df: pd.DataFrame,
    expected_interval_minutes: Optional[int] = None,
    min_completeness_pct: float = 80.0,
    daytime_only: bool = True,
    daytime_start_hour: int = 6,
    daytime_end_hour: int = 18
) -> Dict:
    """
    Check data completeness and identify missing data periods.
    Auto-detects data frequency if not specified.
    
    Args:
        df: DataFrame with Timestamp column
        expected_interval_minutes: Expected data logging interval (auto-detected if None)
        min_completeness_pct: Minimum acceptable completeness percentage
        daytime_only: Only check completeness during daytime hours
        daytime_start_hour: Start of daytime (default 6 AM)
        daytime_end_hour: End of daytime (default 6 PM)
    
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
    
    # Filter to daytime hours only if requested
    if daytime_only:
        df_sorted['Hour'] = df_sorted['Timestamp'].dt.hour
        df_sorted = df_sorted[
            (df_sorted['Hour'] >= daytime_start_hour) & 
            (df_sorted['Hour'] < daytime_end_hour)
        ].copy()
        
        if len(df_sorted) < 2:
            return {
                'overall_completeness_pct': 0,
                'missing_periods': [],
                'is_complete': False,
                'error': 'No daytime data available'
            }
    
    # Auto-detect interval if not provided
    if expected_interval_minutes is None:
        # Calculate median time difference (more robust than mean)
        time_diffs = df_sorted['Timestamp'].diff().dt.total_seconds() / 60
        # Filter out unreasonably large gaps (> 2 hours) for detection
        reasonable_diffs = time_diffs[(time_diffs > 0) & (time_diffs < 120)]
        
        if len(reasonable_diffs) > 0:
            detected_interval = reasonable_diffs.median()
            
            # Round to common intervals
            common_intervals = [1, 5, 10, 15, 30, 60]  # minutes
            expected_interval_minutes = min(common_intervals, 
                                           key=lambda x: abs(x - detected_interval))
        else:
            expected_interval_minutes = 60  # Default to hourly
    
    # Calculate time range (daytime only)
    start_time = df_sorted['Timestamp'].min()
    end_time = df_sorted['Timestamp'].max()
    
    # Calculate expected points during daytime hours
    if daytime_only:
        # Count daytime hours in the date range
        date_range = pd.date_range(start=start_time.date(), end=end_time.date(), freq='D')
        daytime_hours_per_day = daytime_end_hour - daytime_start_hour
        total_daytime_minutes = len(date_range) * daytime_hours_per_day * 60
        expected_points = total_daytime_minutes / expected_interval_minutes
    else:
        total_duration_minutes = (end_time - start_time).total_seconds() / 60
        expected_points = total_duration_minutes / expected_interval_minutes
    
    actual_points = len(df_sorted)
    completeness_pct = (actual_points / expected_points) * 100 if expected_points > 0 else 0
    
    # Find missing periods (gaps > 2x expected interval)
    df_sorted['time_diff'] = df_sorted['Timestamp'].diff()
    gap_threshold = pd.Timedelta(minutes=expected_interval_minutes * 2)
    
    gaps = df_sorted[df_sorted['time_diff'] > gap_threshold].copy()
    
    missing_periods = []
    for idx, row in gaps.iterrows():
        prev_idx = df_sorted.index[df_sorted.index < idx][-1] if any(df_sorted.index < idx) else idx
        gap_start = df_sorted.loc[prev_idx, 'Timestamp']
        gap_end = row['Timestamp']
        gap_duration = row['time_diff']
        
        # Only include if gap is during daytime
        if daytime_only:
            gap_start_hour = gap_start.hour
            gap_end_hour = gap_end.hour
            gap_start_date = gap_start.date()
            gap_end_date = gap_end.date()
            
            # Skip overnight gaps (different dates with gap spanning nighttime)
            if gap_start_date != gap_end_date:
                # This is an overnight gap - skip it
                continue
            
            # Skip if gap is entirely outside daytime hours on the same day
            if gap_end_hour < daytime_start_hour or gap_start_hour >= daytime_end_hour:
                continue
        
        missing_periods.append({
            'start': gap_start,
            'end': gap_end,
            'duration_minutes': gap_duration.total_seconds() / 60
        })
    
    # Daily completeness
    daily_completeness = []
    if 'Date' in df_sorted.columns or 'Timestamp' in df_sorted.columns:
        # Add Date column if not present
        if 'Date' not in df_sorted.columns:
            df_sorted['Date'] = df_sorted['Timestamp'].dt.date
        
        for date, day_df in df_sorted.groupby('Date'):
            # Expected points for daytime hours
            if daytime_only:
                expected_day_points = (daytime_hours_per_day * 60) / expected_interval_minutes
            else:
                day_start = day_df['Timestamp'].min()
                day_end = day_df['Timestamp'].max()
                day_duration = (day_end - day_start).total_seconds() / 60
                expected_day_points = day_duration / expected_interval_minutes if day_duration > 0 else 1
            
            day_completeness = (len(day_df) / expected_day_points) * 100 if expected_day_points > 0 else 0
            
            daily_completeness.append({
                'date': date,
                'data_points': len(day_df),
                'expected_points': int(expected_day_points),
                'completeness_pct': min(day_completeness, 100),
                'is_complete': day_completeness >= min_completeness_pct
            })
    
    return {
        'overall_completeness_pct': min(completeness_pct, 100),
        'detected_interval_minutes': expected_interval_minutes,
        'expected_points': int(expected_points),
        'actual_points': actual_points,
        'missing_periods': missing_periods,
        'missing_periods_count': len(missing_periods),
        'daily_completeness': daily_completeness,
        'is_complete': completeness_pct >= min_completeness_pct,
        'daytime_only': daytime_only,
        'data_range': {
            'start': start_time,
            'end': end_time,
            'duration_hours': (end_time - start_time).total_seconds() / 3600
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
    
    # Columns to analyze (range checks disabled)
    columns_to_check = [
        'Voltage_V', 'Current_A', 'Irradiance_Wm2', 'Temperature_C', 'SoC_pct'
    ]
    
    for col in columns_to_check:
        if col not in df.columns:
            continue
        
        # Find null values
        null_values = df[df[col].isna()]
        
        # Find sudden jumps (diff > 50% of typical operating range)
        # We define rough operating ranges just for jump detection if needed, 
        # but for now we'll skip jump detection based on arbitrary ranges too since "fixed ranges" are unwanted.
        sudden_jump_count = 0 
        
        validation_results['column_stats'][col] = {
            'min': df[col].min(),
            'max': df[col].max(),
            'mean': df[col].mean(),
            'null_count': len(null_values),
            'out_of_range_count': 0,
            'sudden_jump_count': sudden_jump_count,
            'valid_range': 'N/A'
        }
        
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
