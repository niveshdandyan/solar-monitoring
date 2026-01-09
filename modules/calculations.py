"""
Calculations Module
Power, Performance Ratio, Specific Yield, and Expected Power calculations
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


def calculate_power(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate measured power from current and voltage.
    P = I × V (in Watts)
    """
    result = df.copy()
    
    if 'Current_A' in df.columns and 'Voltage_V' in df.columns:
        result['Power_W'] = df['Current_A'] * df['Voltage_V']
        result['Power_kW'] = result['Power_W'] / 1000
    
    return result


def calculate_expected_power(
    df: pd.DataFrame,
    nominal_power_kw: float,
    temp_coefficient: float  # as decimal, e.g., -0.004 for -0.4%/°C
) -> pd.DataFrame:
    """
    Calculate expected power based on irradiance and temperature.
    
    P_expected = P_stc × (G / 1000) × [1 + γ × (T_cell - 25)]
    
    Args:
        df: DataFrame with Irradiance_Wm2 and Temperature_C columns
        nominal_power_kw: System nominal power at STC (kW)
        temp_coefficient: Power temperature coefficient (e.g., -0.004 for -0.4%/°C)
    """
    result = df.copy()
    nominal_power_w = nominal_power_kw * 1000
    
    if 'Irradiance_Wm2' in df.columns:
        # Start with irradiance-based expected power
        result['Expected_Power_W'] = nominal_power_w * (df['Irradiance_Wm2'] / 1000)
        
        # Apply temperature correction if temperature data available
        if 'Temperature_C' in df.columns:
            temp_factor = 1 + temp_coefficient * (df['Temperature_C'] - 25)
            result['Expected_Power_W'] = result['Expected_Power_W'] * temp_factor
            result['Temp_Factor'] = temp_factor
        
        result['Expected_Power_kW'] = result['Expected_Power_W'] / 1000
    
    return result


def calculate_energy(df: pd.DataFrame, power_col: str = 'Power_W') -> float:
    """
    Calculate total energy from power readings.
    Uses trapezoidal integration based on timestamps.
    
    Returns energy in Wh
    """
    if power_col not in df.columns or 'Timestamp' not in df.columns:
        return 0.0
    
    # Sort by timestamp
    df_sorted = df.sort_values('Timestamp').copy()
    
    # Calculate time differences in hours
    time_diff_hours = df_sorted['Timestamp'].diff().dt.total_seconds() / 3600
    
    # Use trapezoidal rule: average of consecutive power values × time
    avg_power = (df_sorted[power_col] + df_sorted[power_col].shift(1)) / 2
    
    # Sum energy
    energy_wh = (avg_power * time_diff_hours).sum()
    
    return energy_wh


def filter_for_pr_calculation(df: pd.DataFrame, soc_threshold: float = 95.0) -> pd.DataFrame:
    """
    Filter data for Performance Ratio calculation.
    Excludes rows where SoC >= threshold (battery full, system may be curtailed).
    
    Args:
        df: Input dataframe
        soc_threshold: SoC percentage above which to exclude data (default 95%)
    
    Returns:
        Filtered dataframe
    """
    if 'SoC_pct' in df.columns:
        return df[df['SoC_pct'] < soc_threshold].copy()
    return df.copy()


def calculate_performance_ratio(
    df: pd.DataFrame,
    nominal_power_kw: float,
    temp_coefficient: float,
    filter_high_soc: bool = True,
    soc_threshold: float = 95.0
) -> Dict:
    """
    Calculate Performance Ratio.
    
    PR = (Actual Energy / Expected Energy) × 100%
    
    Args:
        df: DataFrame with power and irradiance data
        nominal_power_kw: System nominal power at STC (kW)
        temp_coefficient: Power temperature coefficient
        filter_high_soc: Whether to exclude high SoC data points
        soc_threshold: SoC threshold for filtering
    
    Returns:
        Dictionary with PR value and calculation details
    """
    # Filter data if needed
    if filter_high_soc and 'SoC_pct' in df.columns:
        calc_df = filter_for_pr_calculation(df, soc_threshold)
        rows_excluded = len(df) - len(calc_df)
    else:
        calc_df = df.copy()
        rows_excluded = 0
    
    # Need actual power at minimum
    if 'Power_W' not in calc_df.columns:
        return {
            'pr_value': None,
            'error': 'Missing required column (Power_W)'
        }
    
    # Calculate expected power if irradiance is available
    if 'Irradiance_Wm2' in calc_df.columns and 'Expected_Power_W' not in calc_df.columns:
        calc_df = calculate_expected_power(calc_df, nominal_power_kw, temp_coefficient)
    
    # If no expected power available (no irradiance), cannot calculate PR
    if 'Expected_Power_W' not in calc_df.columns:
        return {
            'pr_value': None,
            'actual_energy_wh': calculate_energy(calc_df, 'Power_W'),
            'actual_energy_kwh': calculate_energy(calc_df, 'Power_W') / 1000,
            'expected_energy_wh': None,
            'expected_energy_kwh': None,
            'rows_used': len(calc_df),
            'rows_excluded_high_soc': rows_excluded,
            'soc_threshold': soc_threshold if filter_high_soc else None,
            'info': 'Irradiance not available - cannot calculate PR or expected energy'
        }
    
    # Calculate energies
    actual_energy_wh = calculate_energy(calc_df, 'Power_W')
    expected_energy_wh = calculate_energy(calc_df, 'Expected_Power_W')
    
    # Calculate PR
    if expected_energy_wh > 0:
        pr_value = (actual_energy_wh / expected_energy_wh) * 100
    else:
        pr_value = None
    
    return {
        'pr_value': pr_value,
        'actual_energy_wh': actual_energy_wh,
        'actual_energy_kwh': actual_energy_wh / 1000,
        'expected_energy_wh': expected_energy_wh,
        'expected_energy_kwh': expected_energy_wh / 1000,
        'rows_used': len(calc_df),
        'rows_excluded_high_soc': rows_excluded,
        'soc_threshold': soc_threshold if filter_high_soc else None
    }


def calculate_specific_yield(energy_kwh: float, installed_capacity_kwp: float) -> float:
    """
    Calculate Specific Yield.
    
    Specific Yield = Energy Generated (kWh) / Installed Capacity (kWp)
    
    Returns kWh/kWp
    """
    if installed_capacity_kwp > 0:
        return energy_kwh / installed_capacity_kwp
    return 0.0


def calculate_daily_metrics(
    df: pd.DataFrame,
    nominal_power_kw: float,
    temp_coefficient: float
) -> pd.DataFrame:
    """
    Calculate daily aggregated metrics.
    """
    if 'Date' not in df.columns:
        return pd.DataFrame()
    
    daily_metrics = []
    
    for date, day_df in df.groupby('Date'):
        # Calculate energies (include all data)
        day_with_power = day_df.copy()
        if 'Power_W' not in day_with_power.columns:
            day_with_power = calculate_power(day_with_power)
        day_with_power = calculate_expected_power(day_with_power, nominal_power_kw, temp_coefficient)
        
        actual_energy_wh = calculate_energy(day_with_power, 'Power_W')
        expected_energy_wh = calculate_energy(day_with_power, 'Expected_Power_W')
        
        # Calculate PR (excluding high SoC)
        pr_result = calculate_performance_ratio(
            day_with_power, nominal_power_kw, temp_coefficient,
            filter_high_soc=True, soc_threshold=95.0
        )
        
        metrics = {
            'Date': date,
            'Actual_Energy_kWh': actual_energy_wh / 1000,
            'Expected_Energy_kWh': expected_energy_wh / 1000,
            'PR_pct': pr_result['pr_value'],
            'Specific_Yield_kWhkWp': calculate_specific_yield(actual_energy_wh / 1000, nominal_power_kw),
            'Avg_Irradiance': day_df[day_df['Hour'].between(6, 18)]['Irradiance_Wm2'].mean() if 'Irradiance_Wm2' in day_df.columns and 'Hour' in day_df.columns else (day_df['Irradiance_Wm2'].mean() if 'Irradiance_Wm2' in day_df.columns else None),
            'Avg_Temperature': day_df[day_df['Hour'].between(6, 18)]['Temperature_C'].mean() if 'Temperature_C' in day_df.columns and 'Hour' in day_df.columns else (day_df['Temperature_C'].mean() if 'Temperature_C' in day_df.columns else None),
            'Max_Power_kW': day_with_power['Power_kW'].max() if 'Power_kW' in day_with_power.columns else None,
            'Data_Points': len(day_df),
            'High_SoC_Points': (day_df['SoC_pct'] >= 95).sum() if 'SoC_pct' in day_df.columns else 0
        }
        daily_metrics.append(metrics)
    
    return pd.DataFrame(daily_metrics)


def calculate_monthly_metrics(
    df: pd.DataFrame,
    nominal_power_kw: float,
    temp_coefficient: float
) -> pd.DataFrame:
    """
    Calculate monthly aggregated metrics.
    """
    if 'Month' not in df.columns:
        return pd.DataFrame()
    
    monthly_metrics = []
    
    for month, month_df in df.groupby('Month'):
        # Calculate energies
        month_with_power = month_df.copy()
        if 'Power_W' not in month_with_power.columns:
            month_with_power = calculate_power(month_with_power)
        month_with_power = calculate_expected_power(month_with_power, nominal_power_kw, temp_coefficient)
        
        actual_energy_wh = calculate_energy(month_with_power, 'Power_W')
        expected_energy_wh = calculate_energy(month_with_power, 'Expected_Power_W')
        
        # Calculate PR (excluding high SoC)
        pr_result = calculate_performance_ratio(
            month_with_power, nominal_power_kw, temp_coefficient,
            filter_high_soc=True, soc_threshold=95.0
        )
        
        metrics = {
            'Month': str(month),
            'Actual_Energy_kWh': actual_energy_wh / 1000,
            'Expected_Energy_kWh': expected_energy_wh / 1000,
            'PR_pct': pr_result['pr_value'],
            'Specific_Yield_kWhkWp': calculate_specific_yield(actual_energy_wh / 1000, nominal_power_kw),
            'Avg_Irradiance': month_df[month_df['Hour'].between(6, 18)]['Irradiance_Wm2'].mean() if 'Irradiance_Wm2' in month_df.columns and 'Hour' in month_df.columns else (month_df['Irradiance_Wm2'].mean() if 'Irradiance_Wm2' in month_df.columns else None),
            'Avg_Temperature': month_df[month_df['Hour'].between(6, 18)]['Temperature_C'].mean() if 'Temperature_C' in month_df.columns and 'Hour' in month_df.columns else (month_df['Temperature_C'].mean() if 'Temperature_C' in month_df.columns else None),
            'Max_Power_kW': month_with_power['Power_kW'].max() if 'Power_kW' in month_with_power.columns else None,
            'Days_with_Data': month_df['Date'].nunique() if 'Date' in month_df.columns else None,
            'Data_Points': len(month_df),
            'High_SoC_Points': (month_df['SoC_pct'] >= 95).sum() if 'SoC_pct' in month_df.columns else 0
        }
        monthly_metrics.append(metrics)
    
    return pd.DataFrame(monthly_metrics)
