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
            'Operating_Hours': calculate_operating_hours(day_with_power),
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
            'Total_Operating_Hours': calculate_operating_hours(month_with_power),
            'Avg_Operating_Hours': calculate_operating_hours(month_with_power) / month_df['Date'].nunique() if 'Date' in month_df.columns and month_df['Date'].nunique() > 0 else 0,
            'Days_with_Data': month_df['Date'].nunique() if 'Date' in month_df.columns else None,
            'Data_Points': len(month_df),
            'High_SoC_Points': (month_df['SoC_pct'] >= 95).sum() if 'SoC_pct' in month_df.columns else 0
        }
        monthly_metrics.append(metrics)
    
    return pd.DataFrame(monthly_metrics)


# =============================================================================
# OPERATING HOURS FUNCTIONS
# =============================================================================

def calculate_operating_hours(df: pd.DataFrame, power_threshold: float = 0.0) -> float:
    """
    Calculate operating hours where Power > threshold.
    Counts the number of data points with power generation and converts to hours.
    
    Args:
        df: DataFrame with Timestamp and Power_W columns
        power_threshold: Minimum power to count as operating (default 0W)
    
    Returns:
        Operating hours (float)
    """
    if 'Power_W' not in df.columns or 'Timestamp' not in df.columns:
        return 0.0
    
    # Filter to power > threshold
    operating_df = df[df['Power_W'] > power_threshold].copy()
    
    if len(operating_df) < 2:
        return 0.0
    
    # Sort by timestamp
    operating_df = operating_df.sort_values('Timestamp')
    
    # Detect the data interval (median time between points)
    time_diffs = operating_df['Timestamp'].diff().dt.total_seconds() / 3600
    valid_diffs = time_diffs[(time_diffs > 0) & (time_diffs < 2)]  # Filter out unreasonable gaps
    
    if len(valid_diffs) > 0:
        interval_hours = valid_diffs.median()
    else:
        interval_hours = 1.0  # Default to 1 hour
    
    # Total operating hours = number of operating points × interval
    total_operating_hours = len(operating_df) * interval_hours
    
    return total_operating_hours


# =============================================================================
# ANOMALY DETECTION FUNCTIONS
# =============================================================================

def detect_power_dip_anomalies(
    df: pd.DataFrame, 
    irradiance_threshold: float = 500.0,
    power_ratio_threshold: float = 0.5,
    soc_threshold: float = 95.0
) -> pd.DataFrame:
    """
    Detect power dips during high irradiance when battery is NOT fully charged.
    This indicates shading, module issues, or inverter problems.
    
    Args:
        df: DataFrame with Power_W, Irradiance_Wm2, and optionally SoC_pct
        irradiance_threshold: Minimum irradiance to consider "high" (W/m²)
        power_ratio_threshold: Power/Expected ratio below which is anomaly
        soc_threshold: SoC below which battery is not the cause
    
    Returns:
        DataFrame with detected anomalies
    """
    if 'Power_W' not in df.columns or 'Irradiance_Wm2' not in df.columns:
        return pd.DataFrame()
    
    result = df.copy()
    
    # High irradiance condition
    high_irr = result['Irradiance_Wm2'] >= irradiance_threshold
    
    # Calculate expected power ratio (simplified: proportional to irradiance)
    max_power = result['Power_W'].max()
    max_irr = result['Irradiance_Wm2'].max()
    
    if max_power <= 0 or max_irr <= 0:
        return pd.DataFrame()
    
    # Expected power based on irradiance ratio
    expected_power = (result['Irradiance_Wm2'] / max_irr) * max_power
    power_ratio = result['Power_W'] / expected_power.replace(0, np.nan)
    
    # Low power condition
    low_power = power_ratio < power_ratio_threshold
    
    # Battery not full condition
    if 'SoC_pct' in result.columns:
        battery_not_full = result['SoC_pct'] < soc_threshold
    else:
        battery_not_full = True  # Assume true if no SoC data
    
    # Combine conditions
    anomaly_mask = high_irr & low_power & battery_not_full
    
    anomalies = result[anomaly_mask].copy()
    anomalies['Anomaly_Type'] = 'Power Dip (High Irr, Not Battery)'
    anomalies['Expected_Power_W'] = expected_power[anomaly_mask]
    anomalies['Power_Ratio'] = power_ratio[anomaly_mask]
    
    return anomalies


def detect_voltage_clipping(
    df: pd.DataFrame,
    voltage_std_threshold: float = 0.5,
    irradiance_std_threshold: float = 50.0,
    window_size: int = 10
) -> pd.DataFrame:
    """
    Detect voltage clipping where voltage stays constant despite irradiance variation.
    
    Args:
        df: DataFrame with Voltage_V and Irradiance_Wm2
        voltage_std_threshold: Max voltage std to consider "constant"
        irradiance_std_threshold: Min irradiance std to consider "varying"
        window_size: Rolling window size for detection
    
    Returns:
        DataFrame with detected clipping periods
    """
    if 'Voltage_V' not in df.columns or 'Irradiance_Wm2' not in df.columns:
        return pd.DataFrame()
    
    result = df.copy()
    
    # Calculate rolling statistics
    voltage_std = result['Voltage_V'].rolling(window=window_size, center=True).std()
    irr_std = result['Irradiance_Wm2'].rolling(window=window_size, center=True).std()
    
    # Clipping: constant voltage despite varying irradiance
    clipping_mask = (voltage_std < voltage_std_threshold) & (irr_std > irradiance_std_threshold)
    
    anomalies = result[clipping_mask].copy()
    anomalies['Anomaly_Type'] = 'Voltage Clipping'
    anomalies['Voltage_Std'] = voltage_std[clipping_mask]
    anomalies['Irradiance_Std'] = irr_std[clipping_mask]
    
    return anomalies


def detect_current_limiting(
    df: pd.DataFrame,
    current_std_threshold: float = 0.2,
    irradiance_min: float = 600.0,
    window_size: int = 10
) -> pd.DataFrame:
    """
    Detect current limiting where current plateaus despite high irradiance.
    
    Args:
        df: DataFrame with Current_A and Irradiance_Wm2
        current_std_threshold: Max current std to consider "plateau"
        irradiance_min: Minimum irradiance for detection
        window_size: Rolling window size
    
    Returns:
        DataFrame with detected limiting periods
    """
    if 'Current_A' not in df.columns or 'Irradiance_Wm2' not in df.columns:
        return pd.DataFrame()
    
    result = df.copy()
    
    # High irradiance condition
    high_irr = result['Irradiance_Wm2'] >= irradiance_min
    
    # Calculate rolling current std
    current_std = result['Current_A'].rolling(window=window_size, center=True).std()
    
    # Limiting: constant current during high irradiance
    limiting_mask = (current_std < current_std_threshold) & high_irr
    
    anomalies = result[limiting_mask].copy()
    anomalies['Anomaly_Type'] = 'Current Limiting'
    anomalies['Current_Std'] = current_std[limiting_mask]
    
    return anomalies


def detect_voltage_anomaly(
    df: pd.DataFrame,
    vmpp: float,
    low_threshold: float = 0.8,
    high_threshold: float = 1.1
) -> pd.DataFrame:
    """
    Detect voltage anomalies outside 80-110% of Vmpp.
    
    Args:
        df: DataFrame with Voltage_V
        vmpp: Maximum power point voltage
        low_threshold: Low ratio (default 0.8 = 80%)
        high_threshold: High ratio (default 1.1 = 110%)
    
    Returns:
        DataFrame with detected anomalies
    """
    if 'Voltage_V' not in df.columns or vmpp <= 0:
        return pd.DataFrame()
    
    result = df.copy()
    
    voltage_ratio = result['Voltage_V'] / vmpp
    
    # Anomaly: outside 80-110% range (during operating hours)
    operating = result['Voltage_V'] > 0 if 'Power_W' not in result.columns else result['Power_W'] > 0
    anomaly_mask = operating & ((voltage_ratio < low_threshold) | (voltage_ratio > high_threshold))
    
    anomalies = result[anomaly_mask].copy()
    anomalies['Anomaly_Type'] = 'Voltage Anomaly'
    anomalies['Voltage_Ratio'] = voltage_ratio[anomaly_mask]
    anomalies['Vmpp'] = vmpp
    
    return anomalies


def detect_current_anomaly(
    df: pd.DataFrame,
    impp: float,
    high_threshold: float = 1.1
) -> pd.DataFrame:
    """
    Detect current anomalies where I > 110% of Impp.
    
    Args:
        df: DataFrame with Current_A
        impp: Maximum power point current
        high_threshold: High ratio (default 1.1 = 110%)
    
    Returns:
        DataFrame with detected anomalies
    """
    if 'Current_A' not in df.columns or impp <= 0:
        return pd.DataFrame()
    
    result = df.copy()
    
    current_ratio = result['Current_A'] / impp
    
    # Anomaly: current > 110% of Impp
    anomaly_mask = current_ratio > high_threshold
    
    anomalies = result[anomaly_mask].copy()
    anomalies['Anomaly_Type'] = 'Current Anomaly'
    anomalies['Current_Ratio'] = current_ratio[anomaly_mask]
    anomalies['Impp'] = impp
    
    return anomalies


def get_all_anomalies(
    df: pd.DataFrame,
    vmpp: float = 30.0,
    impp: float = 8.0
) -> Dict[str, pd.DataFrame]:
    """
    Detect all types of anomalies and return as dictionary.
    
    Args:
        df: DataFrame with all sensor columns
        vmpp: Maximum power point voltage
        impp: Maximum power point current
    
    Returns:
        Dictionary with anomaly type as key, DataFrame as value
    """
    anomalies = {}
    
    # Power dip anomalies
    power_dips = detect_power_dip_anomalies(df)
    if len(power_dips) > 0:
        anomalies['Power Dip (High Irr, Not Battery)'] = power_dips
    
    # Voltage clipping
    voltage_clipping = detect_voltage_clipping(df)
    if len(voltage_clipping) > 0:
        anomalies['Voltage Clipping'] = voltage_clipping
    
    # Current limiting
    current_limiting = detect_current_limiting(df)
    if len(current_limiting) > 0:
        anomalies['Current Limiting'] = current_limiting
    
    # Voltage anomaly
    voltage_anomaly = detect_voltage_anomaly(df, vmpp)
    if len(voltage_anomaly) > 0:
        anomalies['Voltage Anomaly'] = voltage_anomaly
    
    # Current anomaly
    current_anomaly = detect_current_anomaly(df, impp)
    if len(current_anomaly) > 0:
        anomalies['Current Anomaly'] = current_anomaly
    
    return anomalies

