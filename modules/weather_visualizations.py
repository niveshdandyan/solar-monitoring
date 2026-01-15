"""
Weather Visualizations Module
Creates graphs for the standalone Weather Analysis tab.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Optional, List
import os


def plot_weather_daily_irradiance(
    hourly_df: pd.DataFrame,
    selected_date: str,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot hourly irradiance for a selected day.
    
    Args:
        hourly_df: DataFrame with hourly weather data
        selected_date: Date string (YYYY-MM-DD)
        export_dir: Optional directory to save the plot
        show_plot: If True, return the figure for display
        
    Returns:
        Figure object if show_plot is True, else None
    """
    if hourly_df is None or hourly_df.empty:
        return None
    
    # Filter for selected date
    date_data = hourly_df[hourly_df['Date'].astype(str) == selected_date].copy()
    
    if date_data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    # Plot GHI
    ax.plot(
        date_data['Hour'], 
        date_data['Irradiance_Wm2'], 
        color='#FF9800', 
        linewidth=2, 
        label='GHI (Total)',
        marker='o',
        markersize=4
    )
    
    # Plot Direct if available
    if 'Direct_Irradiance_Wm2' in date_data.columns:
        ax.plot(
            date_data['Hour'], 
            date_data['Direct_Irradiance_Wm2'], 
            color='#F44336', 
            linewidth=1.5, 
            label='Direct',
            linestyle='--'
        )
    
    # Plot Diffuse if available
    if 'Diffuse_Irradiance_Wm2' in date_data.columns:
        ax.plot(
            date_data['Hour'], 
            date_data['Diffuse_Irradiance_Wm2'], 
            color='#2196F3', 
            linewidth=1.5, 
            label='Diffuse',
            linestyle=':'
        )
    
    ax.set_xlabel('Hour of Day', fontsize=11)
    ax.set_ylabel('Irradiance (W/m²)', fontsize=11)
    ax.set_title(f'Solar Irradiance - {selected_date}', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, f"weather_irradiance_{selected_date}.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_weather_daily_temperature(
    hourly_df: pd.DataFrame,
    selected_date: str,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot hourly temperature for a selected day.
    """
    if hourly_df is None or hourly_df.empty:
        return None
    
    date_data = hourly_df[hourly_df['Date'].astype(str) == selected_date].copy()
    
    if date_data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(
        date_data['Hour'], 
        date_data['Temperature_C'], 
        color='#E91E63', 
        linewidth=2, 
        label='Temperature',
        marker='o',
        markersize=4
    )
    
    ax.fill_between(
        date_data['Hour'],
        date_data['Temperature_C'],
        alpha=0.2,
        color='#E91E63'
    )
    
    ax.set_xlabel('Hour of Day', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.set_title(f'Temperature Profile - {selected_date}', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, f"weather_temperature_{selected_date}.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_weather_monthly_avg_irradiance(
    hourly_df: pd.DataFrame,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot monthly average hourly irradiance pattern.
    """
    if hourly_df is None or hourly_df.empty:
        return None
    
    # Group by hour and calculate mean
    hourly_avg = hourly_df.groupby('Hour').agg({
        'Irradiance_Wm2': 'mean',
        'Direct_Irradiance_Wm2': 'mean',
        'Diffuse_Irradiance_Wm2': 'mean'
    }).reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(
        hourly_avg['Hour'], 
        hourly_avg['Irradiance_Wm2'], 
        color='#FF9800', 
        linewidth=2.5, 
        label='Avg GHI',
        marker='o',
        markersize=5
    )
    
    if 'Direct_Irradiance_Wm2' in hourly_avg.columns:
        ax.plot(
            hourly_avg['Hour'], 
            hourly_avg['Direct_Irradiance_Wm2'], 
            color='#F44336', 
            linewidth=1.5, 
            label='Avg Direct',
            linestyle='--'
        )
    
    if 'Diffuse_Irradiance_Wm2' in hourly_avg.columns:
        ax.plot(
            hourly_avg['Hour'], 
            hourly_avg['Diffuse_Irradiance_Wm2'], 
            color='#2196F3', 
            linewidth=1.5, 
            label='Avg Diffuse',
            linestyle=':'
        )
    
    ax.fill_between(
        hourly_avg['Hour'],
        hourly_avg['Irradiance_Wm2'],
        alpha=0.15,
        color='#FF9800'
    )
    
    ax.set_xlabel('Hour of Day', fontsize=11)
    ax.set_ylabel('Irradiance (W/m²)', fontsize=11)
    ax.set_title('Average Hourly Irradiance Pattern', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, "weather_avg_irradiance.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_weather_monthly_avg_temperature(
    hourly_df: pd.DataFrame,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot monthly average hourly temperature pattern.
    """
    if hourly_df is None or hourly_df.empty:
        return None
    
    hourly_avg = hourly_df.groupby('Hour')['Temperature_C'].mean().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    ax.plot(
        hourly_avg['Hour'], 
        hourly_avg['Temperature_C'], 
        color='#E91E63', 
        linewidth=2.5, 
        label='Avg Temperature',
        marker='o',
        markersize=5
    )
    
    ax.fill_between(
        hourly_avg['Hour'],
        hourly_avg['Temperature_C'],
        alpha=0.15,
        color='#E91E63'
    )
    
    ax.set_xlabel('Hour of Day', fontsize=11)
    ax.set_ylabel('Temperature (°C)', fontsize=11)
    ax.set_title('Average Hourly Temperature Pattern', fontsize=13, fontweight='bold')
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, "weather_avg_temperature.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_weather_daily_summary(
    daily_df: pd.DataFrame,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot daily summary with max/min temperatures and total irradiance.
    """
    if daily_df is None or daily_df.empty:
        return None
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    dates = range(len(daily_df))
    date_labels = [str(d)[:10] for d in daily_df['Date']]
    
    # Temperature subplot
    ax1.fill_between(dates, daily_df['Temp_Min_C'], daily_df['Temp_Max_C'], 
                     alpha=0.3, color='#E91E63', label='Temp Range')
    ax1.plot(dates, daily_df['Temp_Max_C'], color='#F44336', linewidth=1.5, 
             label='Max Temp', marker='^', markersize=4)
    ax1.plot(dates, daily_df['Temp_Min_C'], color='#2196F3', linewidth=1.5, 
             label='Min Temp', marker='v', markersize=4)
    ax1.set_ylabel('Temperature (°C)', fontsize=11)
    ax1.set_title('Daily Temperature Range', fontsize=12, fontweight='bold')
    ax1.legend(loc='upper right')
    ax1.grid(True, alpha=0.3)
    ax1.set_facecolor('#f8f9fa')
    
    # Irradiance subplot
    if 'Total_Irradiance_kWhm2' in daily_df.columns:
        ax2.bar(dates, daily_df['Total_Irradiance_kWhm2'], color='#FF9800', alpha=0.7,
                label='Daily Irradiance')
        ax2.set_ylabel('Total Irradiance (kWh/m²)', fontsize=11)
    else:
        ax2.bar(dates, daily_df['Total_Irradiance_MJm2'], color='#FF9800', alpha=0.7,
                label='Daily Irradiance')
        ax2.set_ylabel('Total Irradiance (MJ/m²)', fontsize=11)
    
    ax2.set_title('Daily Total Solar Irradiance', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=11)
    ax2.legend(loc='upper right')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_facecolor('#f8f9fa')
    
    # Set x-axis labels
    if len(dates) <= 15:
        ax2.set_xticks(dates)
        ax2.set_xticklabels(date_labels, rotation=45, ha='right')
    else:
        step = max(1, len(dates) // 10)
        ax2.set_xticks(dates[::step])
        ax2.set_xticklabels(date_labels[::step], rotation=45, ha='right')
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, "weather_daily_summary.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_weather_calendar_month_averages(
    hourly_df: pd.DataFrame,
    daily_df: pd.DataFrame = None,
    export_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Plot average irradiance and temperature by calendar month (Jan, Feb, Mar, etc.).
    Useful for comparing seasonal patterns across months.
    """
    if hourly_df is None or hourly_df.empty:
        return None
    
    # Extract month from Timestamp
    df = hourly_df.copy()
    df['Month'] = pd.to_datetime(df['Timestamp']).dt.month
    df['MonthName'] = pd.to_datetime(df['Timestamp']).dt.strftime('%b')
    
    # Calculate averages by month
    monthly_avg = df.groupby('Month').agg({
        'Irradiance_Wm2': 'mean',
        'Temperature_C': 'mean'
    }).reset_index()
    
    # Get month names in order
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    monthly_avg['MonthName'] = monthly_avg['Month'].apply(lambda x: month_names[x-1])
    monthly_avg = monthly_avg.sort_values('Month')
    
    # Create figure with two subplots
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Irradiance by month
    bars1 = ax1.bar(
        monthly_avg['MonthName'], 
        monthly_avg['Irradiance_Wm2'],
        color='#FF9800',
        alpha=0.8,
        edgecolor='#E65100'
    )
    ax1.set_xlabel('Month', fontsize=11)
    ax1.set_ylabel('Avg Irradiance (W/m²)', fontsize=11)
    ax1.set_title('Average Irradiance by Month', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_facecolor('#f8f9fa')
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.annotate(f'{height:.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    # Temperature by month
    bars2 = ax2.bar(
        monthly_avg['MonthName'], 
        monthly_avg['Temperature_C'],
        color='#E91E63',
        alpha=0.8,
        edgecolor='#880E4F'
    )
    ax2.set_xlabel('Month', fontsize=11)
    ax2.set_ylabel('Avg Temperature (°C)', fontsize=11)
    ax2.set_title('Average Temperature by Month', fontsize=13, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')
    ax2.set_facecolor('#f8f9fa')
    
    # Add value labels on bars
    for bar in bars2:
        height = bar.get_height()
        ax2.annotate(f'{height:.1f}°',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    
    if export_dir:
        filepath = os.path.join(export_dir, "weather_calendar_month_averages.png")
        fig.savefig(filepath, dpi=150, bbox_inches='tight')
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None
