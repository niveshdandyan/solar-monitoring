"""
Multi-Site Comparison Module
Handles processing and comparison of multiple solar installation sites.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import datetime


def process_site_data(
    df: pd.DataFrame,
    site_name: str,
    nominal_power_kwp: float,
    temp_coefficient: float = -0.004
) -> Dict:
    """
    Process a single site's data and return metrics.
    
    Args:
        df: Raw DataFrame from CSV
        site_name: User-defined site name
        nominal_power_kwp: System nominal power in kWp
        temp_coefficient: Temperature coefficient (default -0.4%/°C)
    
    Returns:
        Dictionary containing site data and calculated metrics
    """
    from modules.data_parser import parse_data, prepare_analysis_data
    from modules.calculations import calculate_daily_metrics, calculate_monthly_metrics
    
    # Parse and prepare data
    parsed_df, column_mapping = parse_data(df)
    analysis_df = prepare_analysis_data(parsed_df, column_mapping)
    
    # Calculate metrics
    daily_metrics = calculate_daily_metrics(
        analysis_df, 
        nominal_power_kwp, 
        temp_coefficient
    )
    monthly_metrics = calculate_monthly_metrics(
        analysis_df, 
        nominal_power_kwp, 
        temp_coefficient
    )
    
    # Calculate summary statistics
    summary = calculate_site_summary(
        analysis_df, 
        daily_metrics, 
        nominal_power_kwp
    )
    
    return {
        'name': site_name,
        'nominal_power_kwp': nominal_power_kwp,
        'temp_coefficient': temp_coefficient,
        'analysis_df': analysis_df,
        'daily_metrics': daily_metrics,
        'monthly_metrics': monthly_metrics,
        'column_mapping': column_mapping,
        'summary': summary,
        'date_range': (
            analysis_df['Timestamp'].min().strftime('%Y-%m-%d'),
            analysis_df['Timestamp'].max().strftime('%Y-%m-%d')
        ),
        'data_points': len(analysis_df),
    }


def calculate_site_summary(
    analysis_df: pd.DataFrame,
    daily_metrics: pd.DataFrame,
    nominal_power_kwp: float
) -> Dict:
    """
    Calculate summary metrics for a site.
    
    Returns:
        Dictionary with summary metrics
    """
    total_days = len(daily_metrics)
    
    # Total energy
    total_energy_kwh = daily_metrics['Actual_Energy_kWh'].sum() if 'Actual_Energy_kWh' in daily_metrics.columns else 0
    
    # Average PR
    avg_pr = daily_metrics['Performance_Ratio'].mean() if 'Performance_Ratio' in daily_metrics.columns else 0
    pr_std = daily_metrics['Performance_Ratio'].std() if 'Performance_Ratio' in daily_metrics.columns else 0
    
    # Specific Yield (total)
    total_specific_yield = total_energy_kwh / nominal_power_kwp if nominal_power_kwp > 0 else 0
    
    # Daily Specific Yield (average)
    avg_daily_yield = total_specific_yield / total_days if total_days > 0 else 0
    
    # Average Operating Hours
    avg_operating_hours = daily_metrics['Operating_Hours'].mean() if 'Operating_Hours' in daily_metrics.columns else 0
    
    # Average Irradiance (daytime)
    avg_irradiance = daily_metrics['Avg_Irradiance'].mean() if 'Avg_Irradiance' in daily_metrics.columns else 0
    
    # Average Temperature
    avg_temp = daily_metrics['Avg_Temperature'].mean() if 'Avg_Temperature' in daily_metrics.columns else 0
    
    # Data quality metrics
    has_power = analysis_df['Power_W'].notna().sum() if 'Power_W' in analysis_df.columns else 0
    data_completeness = (has_power / len(analysis_df) * 100) if len(analysis_df) > 0 else 0
    
    # Anomaly detection (if irradiance and power available)
    anomaly_count = 0
    if 'Irradiance_Wm2' in analysis_df.columns and 'Power_W' in analysis_df.columns:
        # High irradiance, low power = anomaly
        anomalies = (analysis_df['Irradiance_Wm2'] > 100) & (analysis_df['Power_W'] <= 0)
        anomaly_count = anomalies.sum()
    anomaly_rate = (anomaly_count / len(analysis_df) * 100) if len(analysis_df) > 0 else 0
    
    return {
        'total_days': total_days,
        'total_energy_kwh': round(total_energy_kwh, 2),
        'avg_pr': round(avg_pr, 2),
        'pr_std': round(pr_std, 2),
        'total_specific_yield': round(total_specific_yield, 2),
        'avg_daily_yield': round(avg_daily_yield, 2),
        'avg_operating_hours': round(avg_operating_hours, 2),
        'avg_irradiance': round(avg_irradiance, 2),
        'avg_temperature': round(avg_temp, 2),
        'data_completeness': round(data_completeness, 2),
        'anomaly_rate': round(anomaly_rate, 2),
        'anomaly_count': anomaly_count,
    }


def find_common_date_range(sites: Dict[str, Dict]) -> Tuple[str, str]:
    """
    Find the overlapping date range across all sites.
    
    Returns:
        Tuple of (start_date, end_date) as strings
    """
    if not sites:
        return None, None
    
    start_dates = []
    end_dates = []
    
    for site_id, site_data in sites.items():
        if 'date_range' in site_data:
            start_dates.append(site_data['date_range'][0])
            end_dates.append(site_data['date_range'][1])
    
    if not start_dates:
        return None, None
    
    # Common range is max of starts to min of ends
    common_start = max(start_dates)
    common_end = min(end_dates)
    
    return common_start, common_end


def create_comparison_dataframe(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None
) -> pd.DataFrame:
    """
    Create a comparison DataFrame with metrics for all sites.
    
    Args:
        sites: Dictionary of site data
        date_range: Optional tuple of (start, end) dates to filter
    
    Returns:
        DataFrame with one row per site and comparison metrics
    """
    rows = []
    
    for site_id, site_data in sites.items():
        daily_metrics = site_data['daily_metrics']
        
        # Filter by date range if specified
        if date_range and date_range[0] and date_range[1]:
            mask = (daily_metrics['Date'] >= date_range[0]) & (daily_metrics['Date'] <= date_range[1])
            filtered_metrics = daily_metrics[mask]
        else:
            filtered_metrics = daily_metrics
        
        if len(filtered_metrics) == 0:
            continue
        
        # Calculate metrics for the period
        total_energy = filtered_metrics['Actual_Energy_kWh'].sum() if 'Actual_Energy_kWh' in filtered_metrics.columns else 0
        avg_pr = filtered_metrics['Performance_Ratio'].mean() if 'Performance_Ratio' in filtered_metrics.columns else 0
        pr_std = filtered_metrics['Performance_Ratio'].std() if 'Performance_Ratio' in filtered_metrics.columns else 0
        
        specific_yield = total_energy / site_data['nominal_power_kwp'] if site_data['nominal_power_kwp'] > 0 else 0
        days = len(filtered_metrics)
        daily_yield = specific_yield / days if days > 0 else 0
        
        avg_operating = filtered_metrics['Operating_Hours'].mean() if 'Operating_Hours' in filtered_metrics.columns else 0
        
        rows.append({
            'site_id': site_id,
            'Site Name': site_data['name'],
            'Nominal Power (kWp)': site_data['nominal_power_kwp'],
            'Days Analyzed': days,
            'Total Energy (kWh)': round(total_energy, 1),
            'Avg Daily Yield (kWh/kWp)': round(daily_yield, 2),
            'Total Yield (kWh/kWp)': round(specific_yield, 1),
            'Avg PR (%)': round(avg_pr, 1),
            'PR Std Dev (%)': round(pr_std, 1),
            'Avg Operating Hours': round(avg_operating, 1),
        })
    
    df = pd.DataFrame(rows)
    
    # Add ranking
    if len(df) > 0 and 'Avg PR (%)' in df.columns:
        df['PR Rank'] = df['Avg PR (%)'].rank(ascending=False).astype(int)
        df['Yield Rank'] = df['Avg Daily Yield (kWh/kWp)'].rank(ascending=False).astype(int)
    
    return df


def get_daily_metrics_for_comparison(
    sites: Dict[str, Dict],
    metric: str = 'Performance_Ratio',
    date_range: Tuple[str, str] = None
) -> pd.DataFrame:
    """
    Get daily values of a metric for all sites for time series comparison.
    
    Args:
        sites: Dictionary of site data
        metric: Column name to extract (e.g., 'Performance_Ratio', 'Actual_Energy_kWh')
        date_range: Optional date filter
    
    Returns:
        DataFrame with Date as index and site names as columns
    """
    all_data = {}
    
    for site_id, site_data in sites.items():
        daily = site_data['daily_metrics'].copy()
        
        if date_range and date_range[0] and date_range[1]:
            mask = (daily['Date'] >= date_range[0]) & (daily['Date'] <= date_range[1])
            daily = daily[mask]
        
        if metric in daily.columns:
            site_series = daily.set_index('Date')[metric]
            all_data[site_data['name']] = site_series
    
    if not all_data:
        return pd.DataFrame()
    
    # Combine all sites
    combined = pd.DataFrame(all_data)
    combined.index = pd.to_datetime(combined.index)
    combined = combined.sort_index()
    
    return combined


def calculate_relative_performance(
    comparison_df: pd.DataFrame,
    reference_site: str,
    metric: str = 'Avg PR (%)'
) -> pd.DataFrame:
    """
    Calculate performance relative to a reference site.
    
    Args:
        comparison_df: Comparison DataFrame
        reference_site: Name of reference site
        metric: Metric to compare
    
    Returns:
        DataFrame with relative performance column added
    """
    df = comparison_df.copy()
    
    ref_value = df[df['Site Name'] == reference_site][metric].values
    if len(ref_value) == 0:
        return df
    
    ref_value = ref_value[0]
    
    df[f'Relative {metric}'] = ((df[metric] - ref_value) / ref_value * 100).round(1)
    
    return df
