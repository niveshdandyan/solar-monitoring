#!/usr/bin/env python3
"""
Sample Data Generator for Multi-Site Comparison Testing
Generates realistic solar monitoring data for 5 different sites.

Usage:
    python generate_sample_data.py

Output:
    Creates 5 CSV files in the 'sample_data/' directory:
    - site_dubai_commercial.csv      (100 kWp commercial rooftop)
    - site_hongkong_residential.csv  (5 kWp residential)
    - site_singapore_industrial.csv  (250 kWp industrial)
    - site_tokyo_office.csv          (30 kWp office building)
    - site_sydney_farm.csv           (500 kWp solar farm)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Random seed for reproducibility
np.random.seed(42)


def generate_irradiance_profile(hour: int, cloud_factor: float = 1.0, peak_hour: float = 12.0) -> float:
    """
    Generate realistic irradiance based on time of day.
    
    Args:
        hour: Hour of day (0-23)
        cloud_factor: 0.0-1.0, where 1.0 is clear sky
        peak_hour: Hour of peak irradiance (varies by location)
    
    Returns:
        Irradiance in W/m²
    """
    if hour < 6 or hour > 18:
        return 0.0
    
    # Bell curve centered on peak_hour
    sigma = 3.5  # Width of the curve
    base_irradiance = 1000 * np.exp(-((hour - peak_hour) ** 2) / (2 * sigma ** 2))
    
    # Apply cloud factor with some randomness
    cloud_effect = cloud_factor * (0.85 + 0.15 * np.random.random())
    
    # Add some realistic noise
    noise = np.random.normal(0, 20)
    
    irradiance = max(0, base_irradiance * cloud_effect + noise)
    
    return round(irradiance, 1)


def generate_temperature(hour: int, base_temp: float, irradiance: float) -> float:
    """
    Generate realistic cell temperature based on ambient and irradiance.
    
    Args:
        hour: Hour of day
        base_temp: Base ambient temperature for the location
        irradiance: Current irradiance
    
    Returns:
        Cell temperature in °C
    """
    # Ambient temperature variation throughout the day
    ambient_variation = 5 * np.sin((hour - 6) * np.pi / 12) if 6 <= hour <= 18 else -3
    ambient = base_temp + ambient_variation + np.random.normal(0, 1)
    
    # Cell temperature is typically 25-35°C above ambient when irradiance is high
    cell_rise = (irradiance / 1000) * (25 + np.random.normal(0, 3))
    
    return round(ambient + cell_rise, 1)


def generate_site_data(
    site_name: str,
    nominal_power_kw: float,
    start_date: str,
    end_date: str,
    base_temp: float = 25.0,
    peak_hour: float = 12.0,
    avg_cloud_factor: float = 0.85,
    system_efficiency: float = 0.95,  # Base system efficiency (affects PR)
    degradation_rate: float = 0.0,    # Annual degradation
    interval_minutes: int = 15
) -> pd.DataFrame:
    """
    Generate realistic solar monitoring data for a site.
    
    Args:
        site_name: Name for logging
        nominal_power_kw: System nominal power in kW (kWp)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        base_temp: Average ambient temperature
        peak_hour: Hour of peak irradiance
        avg_cloud_factor: Average cloudiness (1.0 = clear)
        system_efficiency: System efficiency factor (affects PR)
        degradation_rate: Annual degradation rate
        interval_minutes: Data logging interval
    
    Returns:
        DataFrame with solar monitoring data
    """
    print(f"Generating data for {site_name}...")
    
    # Generate date range
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Generate timestamps at specified interval
    timestamps = []
    current = start
    while current <= end:
        timestamps.append(current)
        current += timedelta(minutes=interval_minutes)
    
    data = []
    
    for ts in timestamps:
        hour = ts.hour + ts.minute / 60
        
        # Daily weather variation (some days are cloudier)
        day_of_year = ts.timetuple().tm_yday
        daily_cloud = avg_cloud_factor + 0.15 * np.sin(day_of_year * 2 * np.pi / 365) + np.random.normal(0, 0.1)
        daily_cloud = np.clip(daily_cloud, 0.3, 1.0)
        
        # Generate irradiance
        irradiance = generate_irradiance_profile(hour, daily_cloud, peak_hour)
        
        # Generate temperature
        temperature = generate_temperature(int(hour), base_temp, irradiance)
        
        # Calculate expected power
        # P = P_stc * (G/1000) * (1 + gamma * (T - 25))
        temp_coeff = -0.004  # -0.4%/°C
        temp_factor = 1 + temp_coeff * (temperature - 25)
        expected_power = nominal_power_kw * 1000 * (irradiance / 1000) * temp_factor
        
        # Apply system efficiency and some random variation
        efficiency_variation = system_efficiency * (0.95 + 0.10 * np.random.random())
        actual_power = expected_power * efficiency_variation
        
        # Add some random issues (inverter trips, shading events, etc.)
        if np.random.random() < 0.005 and irradiance > 100:  # 0.5% chance of anomaly
            actual_power = actual_power * np.random.uniform(0, 0.3)  # Partial or full loss
        
        # Night time - power should be 0
        if irradiance < 10:
            actual_power = 0
        
        # Calculate voltage and current (simplified model)
        # Voltage is relatively stable, current varies with power
        if actual_power > 0:
            voltage = 35 + np.random.normal(0, 1) + (temperature - 25) * (-0.1)  # Voltage drops with temp
            current = actual_power / voltage if voltage > 0 else 0
        else:
            voltage = 0
            current = 0
        
        # SoC simulation (battery system)
        # Simple model: charges during day, discharges at night
        if 8 <= hour <= 16:
            soc = min(100, 60 + (hour - 8) * 5 + np.random.normal(0, 2))
        elif hour < 8:
            soc = max(30, 95 - (8 - hour) * 8 + np.random.normal(0, 2))
        else:
            soc = max(30, 100 - (hour - 16) * 10 + np.random.normal(0, 2))
        
        soc = np.clip(soc, 0, 100)
        
        data.append({
            'Timestamp': ts.strftime('%Y-%m-%d %H:%M:%S'),
            'Power (W)': round(max(0, actual_power), 2),
            'Voltage (V)': round(max(0, voltage), 2),
            'Current (A)': round(max(0, current), 2),
            'Irradiance (W/m2)': round(irradiance, 1),
            'Temperature (C)': round(temperature, 1),
            'SoC (%)': round(soc, 1)
        })
    
    df = pd.DataFrame(data)
    print(f"  Generated {len(df):,} records from {start_date} to {end_date}")
    
    return df


def main():
    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), 'sample_data')
    os.makedirs(output_dir, exist_ok=True)
    
    # Define date range (2 months)
    start_date = '2025-11-01'
    end_date = '2025-12-31'
    
    # Define 5 different sites with varying characteristics
    sites = [
        {
            'filename': 'site_dubai_commercial.csv',
            'name': 'Dubai Commercial Rooftop',
            'nominal_power_kw': 100.0,
            'base_temp': 32.0,          # Hot climate
            'peak_hour': 12.5,
            'avg_cloud_factor': 0.92,    # Very sunny
            'system_efficiency': 0.88,   # Good but affected by heat/dust
            'interval_minutes': 15
        },
        {
            'filename': 'site_hongkong_residential.csv',
            'name': 'Hong Kong Residential',
            'nominal_power_kw': 5.0,
            'base_temp': 22.0,           # Subtropical
            'peak_hour': 12.0,
            'avg_cloud_factor': 0.75,    # More clouds
            'system_efficiency': 0.82,   # Some shading issues
            'interval_minutes': 5        # Higher resolution data
        },
        {
            'filename': 'site_singapore_industrial.csv',
            'name': 'Singapore Industrial',
            'nominal_power_kw': 250.0,
            'base_temp': 28.0,           # Tropical
            'peak_hour': 12.0,
            'avg_cloud_factor': 0.70,    # Tropical clouds/rain
            'system_efficiency': 0.92,   # Well-maintained industrial
            'interval_minutes': 15
        },
        {
            'filename': 'site_tokyo_office.csv',
            'name': 'Tokyo Office Building',
            'nominal_power_kw': 30.0,
            'base_temp': 18.0,           # Temperate
            'peak_hour': 12.0,
            'avg_cloud_factor': 0.78,    # Variable weather
            'system_efficiency': 0.90,   # Good maintenance
            'interval_minutes': 10
        },
        {
            'filename': 'site_sydney_farm.csv',
            'name': 'Sydney Solar Farm',
            'nominal_power_kw': 500.0,
            'base_temp': 24.0,           # Temperate/warm
            'peak_hour': 12.5,
            'avg_cloud_factor': 0.88,    # Sunny climate
            'system_efficiency': 0.94,   # Excellent maintenance
            'interval_minutes': 15
        }
    ]
    
    print("=" * 60)
    print("Multi-Site Sample Data Generator")
    print("=" * 60)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)
    print()
    
    for site in sites:
        df = generate_site_data(
            site_name=site['name'],
            nominal_power_kw=site['nominal_power_kw'],
            start_date=start_date,
            end_date=end_date,
            base_temp=site['base_temp'],
            peak_hour=site['peak_hour'],
            avg_cloud_factor=site['avg_cloud_factor'],
            system_efficiency=site['system_efficiency'],
            interval_minutes=site['interval_minutes']
        )
        
        # Save to CSV
        filepath = os.path.join(output_dir, site['filename'])
        df.to_csv(filepath, index=False)
        print(f"  Saved: {filepath}")
        print()
    
    print("=" * 60)
    print("Summary of Generated Sites:")
    print("=" * 60)
    print(f"{'Site Name':<30} {'Power':<12} {'Efficiency':<12} {'Climate'}")
    print("-" * 60)
    for site in sites:
        print(f"{site['name']:<30} {site['nominal_power_kw']:<12.1f} {site['system_efficiency']*100:<11.0f}% "
              f"{'Hot' if site['base_temp'] > 28 else 'Tropical' if site['base_temp'] > 25 else 'Temperate'}")
    print()
    print("✅ All sample data files generated successfully!")
    print(f"\nFiles are located in: {output_dir}")
    print("\nTo test in the Multi-Site Comparison:")
    print("  1. Click '🏢 Multi-Site' in the sidebar")
    print("  2. Upload each CSV file one at a time")
    print("  3. Set the Nominal Power (kWp) for each site")
    print("  4. View the comparison!")


if __name__ == '__main__':
    main()
