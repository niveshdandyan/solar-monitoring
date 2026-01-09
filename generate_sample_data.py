"""
Solar Panel Sample Data Generator
Generates realistic 30-day solar panel monitoring data for testing purposes.

System Specifications:
- Nominal Power: 48W
- Vmpp: 47V
- Impp: 1.03A
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

# ============================================================================
# SYSTEM CONFIGURATION - Modify these values to match your system
# ============================================================================

SYSTEM_CONFIG = {
    'nominal_power_w': 48,      # Nominal power at STC (W)
    'vmpp': 47,                 # Voltage at maximum power point (V)
    'impp': 1.03,               # Current at maximum power point (A)
    'voc': 52,                  # Open circuit voltage (V) - estimated
    'isc': 1.15,                # Short circuit current (A) - estimated
    'temp_coeff': -0.004,       # Power temperature coefficient (%/°C as decimal)
}

# Data generation parameters
DATA_CONFIG = {
    'start_date': '2024-03-01',  # Start date for data
    'num_days': 30,               # Number of days to generate
    'interval_minutes': 10,       # Data interval in minutes
    'sunrise_hour': 6,            # Approximate sunrise hour
    'sunset_hour': 18,            # Approximate sunset hour
    'battery_capacity_wh': 150,   # Battery capacity in Wh (smaller for 48W system)
    'base_load_w': 5,             # Base load consumption (W) - lower to allow charging
}

# Weather variation parameters
WEATHER_PROFILES = {
    'sunny': {'irradiance_peak': 1000, 'cloud_factor': 0.95, 'probability': 0.5},
    'partly_cloudy': {'irradiance_peak': 850, 'cloud_factor': 0.7, 'probability': 0.3},
    'cloudy': {'irradiance_peak': 500, 'cloud_factor': 0.4, 'probability': 0.15},
    'rainy': {'irradiance_peak': 200, 'cloud_factor': 0.2, 'probability': 0.05},
}


def get_daily_weather():
    """Randomly select weather profile for a day based on probabilities."""
    rand = random.random()
    cumulative = 0
    for weather, params in WEATHER_PROFILES.items():
        cumulative += params['probability']
        if rand < cumulative:
            return weather, params
    return 'sunny', WEATHER_PROFILES['sunny']


def solar_position_factor(hour: float, sunrise: float = 6, sunset: float = 18) -> float:
    """
    Calculate solar position factor (0-1) based on time of day.
    Uses a sinusoidal model peaking at solar noon.
    """
    if hour < sunrise or hour > sunset:
        return 0.0
    
    # Normalize to 0-π range for sine function
    day_length = sunset - sunrise
    normalized = (hour - sunrise) / day_length * np.pi
    return np.sin(normalized)


def calculate_irradiance(hour: float, weather_params: dict, day_variation: float = 1.0) -> float:
    """
    Calculate irradiance based on time, weather, and daily variation.
    """
    base_factor = solar_position_factor(
        hour, 
        DATA_CONFIG['sunrise_hour'], 
        DATA_CONFIG['sunset_hour']
    )
    
    if base_factor == 0:
        return 0.0
    
    # Apply weather and random cloud variations
    irradiance = weather_params['irradiance_peak'] * base_factor * weather_params['cloud_factor']
    
    # Add some random fluctuation (clouds passing)
    fluctuation = 1 + random.uniform(-0.15, 0.10)
    irradiance *= fluctuation * day_variation
    
    return max(0, irradiance)


def calculate_temperature(hour: float, base_temp: float, irradiance: float) -> float:
    """
    Calculate cell temperature based on ambient temp and irradiance.
    Cell temp = Ambient + (NOCT - 20) * (Irradiance / 800)
    """
    # Ambient temperature varies throughout day
    morning_temp = base_temp - 3
    peak_temp = base_temp + 5
    evening_temp = base_temp
    
    if hour < 6:
        ambient = morning_temp
    elif hour < 14:
        # Warming phase
        progress = (hour - 6) / 8
        ambient = morning_temp + (peak_temp - morning_temp) * progress
    else:
        # Cooling phase
        progress = (hour - 14) / 10
        ambient = peak_temp - (peak_temp - evening_temp) * min(1, progress)
    
    # Cell temperature is higher than ambient due to solar heating
    # NOCT assumption ~45°C
    noct_rise = (45 - 20) * (irradiance / 800) if irradiance > 0 else 0
    cell_temp = ambient + noct_rise
    
    # Add small random variation
    cell_temp += random.uniform(-1, 1)
    
    return round(cell_temp, 1)


def calculate_voltage_current(irradiance: float, temperature: float, config: dict) -> tuple:
    """
    Calculate DC voltage and current based on irradiance and temperature.
    Includes temperature derating and low-light effects.
    """
    if irradiance < 10:
        return 0.0, 0.0
    
    # Current is roughly proportional to irradiance
    irradiance_factor = irradiance / 1000
    current = config['impp'] * irradiance_factor
    
    # Add small random variation
    current *= (1 + random.uniform(-0.05, 0.05))
    current = max(0, min(current, config['isc']))
    
    # Voltage drops slightly at high temperatures and low irradiance
    temp_effect = 1 + config['temp_coeff'] * (temperature - 25)
    
    # Voltage also varies with load/irradiance
    if irradiance_factor > 0.1:
        voltage = config['vmpp'] * temp_effect
    else:
        # At very low irradiance, voltage drops more
        voltage = config['vmpp'] * temp_effect * (irradiance_factor * 5)
    
    # Add small random variation
    voltage *= (1 + random.uniform(-0.02, 0.02))
    voltage = max(0, min(voltage, config['voc']))
    
    return round(voltage, 2), round(current, 3)


def simulate_battery_soc(power_generated: float, soc: float, dt_hours: float, config: dict) -> float:
    """
    Simulate battery State of Charge based on generation and consumption.
    """
    battery_capacity = DATA_CONFIG['battery_capacity_wh']
    base_load = DATA_CONFIG['base_load_w']
    
    # Net power to battery
    net_power = power_generated - base_load
    
    # Energy change in this interval
    energy_change_wh = net_power * dt_hours
    
    # Update SoC
    soc_change = (energy_change_wh / battery_capacity) * 100
    new_soc = soc + soc_change
    
    # Clamp between 0 and 100
    new_soc = max(0, min(100, new_soc))
    
    return round(new_soc, 1)


def generate_sample_data():
    """
    Generate complete sample dataset for solar panel monitoring.
    """
    print("🌞 Solar Panel Sample Data Generator")
    print("=" * 50)
    print(f"System: {SYSTEM_CONFIG['nominal_power_w']}W panel")
    print(f"Vmpp: {SYSTEM_CONFIG['vmpp']}V, Impp: {SYSTEM_CONFIG['impp']}A")
    print(f"Generating {DATA_CONFIG['num_days']} days of data at {DATA_CONFIG['interval_minutes']}min intervals")
    print("=" * 50)
    
    data = []
    
    start_date = datetime.strptime(DATA_CONFIG['start_date'], '%Y-%m-%d')
    interval = timedelta(minutes=DATA_CONFIG['interval_minutes'])
    dt_hours = DATA_CONFIG['interval_minutes'] / 60
    
    # Initial battery SoC
    current_soc = 50.0
    
    # Generate data for each day
    for day in range(DATA_CONFIG['num_days']):
        current_date = start_date + timedelta(days=day)
        weather_type, weather_params = get_daily_weather()
        
        # Daily variation factor (some days are better than others)
        day_variation = random.uniform(0.85, 1.15)
        
        # Random base temperature for the day (20-35°C range)
        base_temp = random.uniform(22, 32)
        
        print(f"Day {day + 1}: {current_date.strftime('%Y-%m-%d')} - {weather_type.upper()}, Base Temp: {base_temp:.1f}°C")
        
        # Generate data points for each interval
        current_time = datetime.combine(current_date, datetime.min.time())
        end_of_day = current_time + timedelta(days=1)
        
        while current_time < end_of_day:
            hour = current_time.hour + current_time.minute / 60
            
            # Calculate all parameters
            irradiance = calculate_irradiance(hour, weather_params, day_variation)
            temperature = calculate_temperature(hour, base_temp, irradiance)
            voltage, current = calculate_voltage_current(irradiance, temperature, SYSTEM_CONFIG)
            
            # Calculate power
            power = voltage * current
            
            # When SoC >= 95%, system may curtail (reduce) power generation
            if current_soc >= 95 and power > 5:
                # Battery full - curtail generation (common in off-grid systems)
                curtail_factor = max(0.1, (100 - current_soc) / 5)
                current *= curtail_factor
                power = voltage * current
            
            # Simulate battery SoC
            current_soc = simulate_battery_soc(power, current_soc, dt_hours, SYSTEM_CONFIG)
            
            # Store data point
            data.append({
                'Timestamp': current_time.strftime('%Y-%m-%d %H:%M'),
                'DC Current (A)': round(current, 3),
                'DC Voltage (V)': round(voltage, 2),
                'Irradiance (W/m2)': round(irradiance, 1),
                'Cell Temperature (C)': round(temperature, 1),
                'Battery SoC (%)': round(current_soc, 1)
            })
            
            current_time += interval
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    return df


def save_data(df: pd.DataFrame, output_dir: str = None):
    """
    Save generated data to CSV file.
    """
    if output_dir is None:
        output_dir = os.path.dirname(os.path.abspath(__file__))
    
    output_path = os.path.join(output_dir, 'sample_data', 'generated_30day_data.csv')
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"\n✅ Data saved to: {output_path}")
    print(f"   Total rows: {len(df)}")
    print(f"   Date range: {df['Timestamp'].iloc[0]} to {df['Timestamp'].iloc[-1]}")
    
    return output_path


def print_summary(df: pd.DataFrame):
    """
    Print summary statistics of generated data.
    """
    print("\n" + "=" * 50)
    print("📊 DATA SUMMARY")
    print("=" * 50)
    
    # Calculate power
    df['Power_W'] = df['DC Current (A)'] * df['DC Voltage (V)']
    
    # Daytime data only (irradiance > 50)
    daytime = df[df['Irradiance (W/m2)'] > 50]
    
    print(f"\n📈 Irradiance:")
    print(f"   Max: {df['Irradiance (W/m2)'].max():.1f} W/m²")
    print(f"   Daytime Avg: {daytime['Irradiance (W/m2)'].mean():.1f} W/m²")
    
    print(f"\n🌡️ Temperature:")
    print(f"   Min: {df['Cell Temperature (C)'].min():.1f}°C")
    print(f"   Max: {df['Cell Temperature (C)'].max():.1f}°C")
    print(f"   Avg: {df['Cell Temperature (C)'].mean():.1f}°C")
    
    print(f"\n⚡ Power Generation:")
    print(f"   Max Power: {df['Power_W'].max():.2f} W")
    print(f"   Daytime Avg: {daytime['Power_W'].mean():.2f} W")
    
    print(f"\n🔋 Battery SoC:")
    print(f"   Min: {df['Battery SoC (%)'].min():.1f}%")
    print(f"   Max: {df['Battery SoC (%)'].max():.1f}%")
    
    # Count high SoC periods
    high_soc = len(df[df['Battery SoC (%)'] >= 95])
    print(f"   High SoC (≥95%) periods: {high_soc} ({100*high_soc/len(df):.1f}%)")
    
    print("\n" + "=" * 50)


if __name__ == "__main__":
    # Set random seed for reproducibility (comment out for different data each run)
    random.seed(42)
    np.random.seed(42)
    
    # Generate data
    df = generate_sample_data()
    
    # Print summary
    print_summary(df)
    
    # Save to CSV
    output_path = save_data(df)
    
    print("\n🎉 Sample data generation complete!")
    print(f"   You can now upload this file to the Solar Monitoring app.")
