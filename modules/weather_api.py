"""
Weather API Module
Handles fetching and processing weather data from Open-Meteo API.
"""

import pandas as pd
import numpy as np
import requests
import re
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict

def extract_coordinates_from_url(url: str) -> Tuple[Optional[float], Optional[float]]:
    """
    Extract latitude and longitude from a Google Maps URL.
    
    Args:
        url: Google Maps URL string
        
    Returns:
        Tuple of (latitude, longitude) or (None, None) if not found
    """
    if not url:
        return None, None
        
    # Pattern 1: @lat,long
    # Example: https://www.google.com/maps/@22.396428,114.109497,15z
    match = re.search(r'@(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return lat, lon
        except ValueError:
            pass
            
    # Pattern 2: q=lat,long or ll=lat,long
    # Example: https://maps.google.com/?q=22.396428,114.109497
    match = re.search(r'[?&](?:q|ll)=(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return lat, lon
        except ValueError:
            pass
            
    # Pattern 3: /place/lat,long or /dir/lat,long
    # Example: https://www.google.com/maps/place/22.396428,114.109497
    match = re.search(r'/(?:place|dir|search)/(-?\d+\.\d+),(-?\d+\.\d+)', url)
    if match:
        try:
            lat = float(match.group(1))
            lon = float(match.group(2))
            return lat, lon
        except ValueError:
            pass
            
    return None, None

def fetch_weather_data(
    lat: float, 
    lon: float, 
    start_date: datetime, 
    end_date: datetime
) -> Optional[pd.DataFrame]:
    """
    Fetch historical weather data from Open-Meteo API.
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start datetime
        end_date: End datetime (inclusive)
        
    Returns:
        DataFrame with weather data or None if failed
    """
    try:
        # Open-Meteo uses YYYY-MM-DD format
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        # API URL
        url = "https://archive-api.open-meteo.com/v1/archive"
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_str,
            "end_date": end_str,
            "hourly": "temperature_2m,shortwave_radiation,direct_radiation,diffuse_radiation",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract hourly data
        hourly = data.get('hourly', {})
        
        if not hourly:
            return None
            
        # Create DataFrame
        weather_df = pd.DataFrame({
            'Timestamp': pd.to_datetime(hourly['time']),
            'Weather_Temperature_C': hourly['temperature_2m'],
            'Weather_Irradiance_Wm2': hourly['shortwave_radiation'], # GHI
            'Weather_Direct_Irradiance_Wm2': hourly['direct_radiation'],
            'Weather_Diffuse_Irradiance_Wm2': hourly['diffuse_radiation']
        })
        
        return weather_df
        
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def resample_weather_data(weather_df: pd.DataFrame, target_index: pd.DatetimeIndex) -> pd.DataFrame:
    """
    Resample/Interpolate weather data to match target timestamp index.
    
    Args:
        weather_df: DataFrame with hourly weather data
        target_index: DatetimeIndex of the user's solar data
        
    Returns:
        DataFrame containing weather data aligned with target_index
    """
    if weather_df is None or weather_df.empty:
        return pd.DataFrame()
        
    # Ensure weather_df is indexed by timestamp
    w_df = weather_df.copy()
    w_df = w_df.set_index('Timestamp')
    
    # Remove duplicates if any
    w_df = w_df[~w_df.index.duplicated(keep='first')]
    
    # Reindex to target index
    # method='time' ensures linear interpolation based on time
    # This handles both upsampling (hourly -> 10min) and downsampling alignment
    
    # First, combine indices to ensure we have endpoints for interpolation
    combined_index = w_df.index.union(target_index).sort_values()
    
    # Reindex to combined, interpolate locally
    w_interp = w_df.reindex(combined_index)
    w_interp = w_interp.interpolate(method='time', limit_direction='both')
    
    # Select only the target timestamps
    aligned_df = w_interp.reindex(target_index)
    
    # Reset index to make Timestamp a column again
    aligned_df = aligned_df.reset_index().rename(columns={'index': 'Timestamp'})
    
    return aligned_df

def merge_weather_with_solar(
    solar_df: pd.DataFrame, 
    weather_df: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """
    Merge weather data with solar data.
    
    Args:
        solar_df: Existing solar data DataFrame
        weather_df: Fetched weather DataFrame (hourly)
        
    Returns:
        Tuple of (merged_df, messages_dict)
    """
    if solar_df is None or weather_df is None:
        return solar_df, {"error": "Invalid input data"}
        
    messages = {}
    
    # Ensure solar_df has Timestamp
    if 'Timestamp' not in solar_df.columns:
        return solar_df, {"error": "Solar data missing Timestamp column"}
        
    # Create target index from solar data
    target_index = pd.DatetimeIndex(solar_df['Timestamp'])
    
    # Resample weather data to match solar data frequency
    aligned_weather = resample_weather_data(weather_df, target_index)
    
    # Merge based on Timestamp
    # We use left join to keep all solar data rows
    merged_df = pd.merge(
        solar_df, 
        aligned_weather, 
        on='Timestamp', 
        how='left'
    )
    
    # Check what was added
    added_cols = [col for col in aligned_weather.columns if col != 'Timestamp']
    messages['success'] = f"✅ Merged {len(added_cols)} weather columns"
    
    # Fill gaps if original data was missing
    if 'Irradiance_Wm2' not in merged_df.columns and 'Weather_Irradiance_Wm2' in merged_df.columns:
        merged_df['Irradiance_Wm2'] = merged_df['Weather_Irradiance_Wm2']
        messages['irradiance'] = "✅ Filled missing Irradiance from weather data"
    
    if 'Temperature_C' not in merged_df.columns and 'Weather_Temperature_C' in merged_df.columns:
        merged_df['Temperature_C'] = merged_df['Weather_Temperature_C']
        messages['temperature'] = "✅ Filled missing Temperature from weather data"
        
    return merged_df, messages
