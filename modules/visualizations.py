"""
Visualizations Module
Professional graph generation with Matplotlib
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Optional, Tuple, List
import os

# Set professional style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("husl")

# Default figure settings
DEFAULT_FIGSIZE = (14, 7)  # 1400x700 at 100 DPI
DEFAULT_DPI = 100
HIGH_RES_DPI = 150  # For exports

# Color scheme
COLORS = {
    'power': '#2E86AB',      # Blue
    'irradiance': '#F6AE2D', # Orange/Yellow  
    'soc': '#33A02C',        # Green
    'temperature': '#E63946', # Red
    'expected': '#8338EC',   # Purple
    'actual': '#3A86FF',     # Light Blue
    'pr': '#06D6A0'          # Teal
}


def setup_figure(figsize: Tuple[int, int] = DEFAULT_FIGSIZE) -> Tuple[plt.Figure, plt.Axes]:
    """Create a figure with professional styling."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.grid(True, alpha=0.3)
    return fig, ax


def format_time_axis(ax: plt.Axes, df: pd.DataFrame):
    """Format x-axis for time series data."""
    if 'Timestamp' in df.columns:
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')


def save_figure(fig: plt.Figure, filepath: str, dpi: int = HIGH_RES_DPI):
    """Save figure as high-resolution image."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    fig.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white', edgecolor='none')
    plt.close(fig)
    return filepath


# ============================================================================
# DAILY GRAPHS
# ============================================================================

def plot_daily_power_irradiance(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create daily Power and Irradiance line graph.
    Y-axis: Power (W), Irradiance (W/m²)
    X-axis: Time (6:00 - 18:00)
    """
    day_df = df[df['Date'] == pd.to_datetime(date).date()].copy()
    
    if len(day_df) == 0:
        return None
    
    fig, ax1 = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Plot Power on primary axis
    if 'Power_W' in day_df.columns:
        ax1.plot(day_df['Timestamp'], day_df['Power_W'], 
                color=COLORS['power'], linewidth=2, label='Power (W)')
        ax1.set_ylabel('Power (W)', color=COLORS['power'], fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor=COLORS['power'])
        ax1.fill_between(day_df['Timestamp'], day_df['Power_W'], alpha=0.2, color=COLORS['power'])
    
    # Create secondary axis for Irradiance
    if 'Irradiance_Wm2' in day_df.columns:
        ax2 = ax1.twinx()
        ax2.plot(day_df['Timestamp'], day_df['Irradiance_Wm2'], 
                color=COLORS['irradiance'], linewidth=2, linestyle='--', label='Irradiance (W/m²)')
        ax2.set_ylabel('Irradiance (W/m²)', color=COLORS['irradiance'], fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=COLORS['irradiance'])
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and labels
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_title(f'Power & Irradiance - {date}', fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    if 'Irradiance_Wm2' in day_df.columns:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    else:
        ax1.legend(loc='upper right')
    
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = f"{date}_Power_Irradiance.png"
    filepath = os.path.join(output_dir, 'daily', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_daily_power_irradiance_soc(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create daily Power, Irradiance, and Battery SoC graph.
    """
    day_df = df[df['Date'] == pd.to_datetime(date).date()].copy()
    
    if len(day_df) == 0:
        return None
    
    fig, ax1 = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Plot Power on primary axis
    if 'Power_W' in day_df.columns:
        line1, = ax1.plot(day_df['Timestamp'], day_df['Power_W'], 
                color=COLORS['power'], linewidth=2, label='Power (W)')
        ax1.set_ylabel('Power (W)', color=COLORS['power'], fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor=COLORS['power'])
    
    # Create secondary axis for Irradiance
    ax2 = ax1.twinx()
    if 'Irradiance_Wm2' in day_df.columns:
        line2, = ax2.plot(day_df['Timestamp'], day_df['Irradiance_Wm2'], 
                color=COLORS['irradiance'], linewidth=2, linestyle='--', label='Irradiance (W/m²)')
        ax2.set_ylabel('Irradiance (W/m²)', color=COLORS['irradiance'], fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=COLORS['irradiance'])
    
    # Create third axis for SoC
    if 'SoC_pct' in day_df.columns:
        ax3 = ax1.twinx()
        ax3.spines['right'].set_position(('axes', 1.12))
        line3, = ax3.plot(day_df['Timestamp'], day_df['SoC_pct'], 
                color=COLORS['soc'], linewidth=2, linestyle=':', label='Battery SoC (%)')
        ax3.set_ylabel('Battery SoC (%)', color=COLORS['soc'], fontsize=12, fontweight='bold')
        ax3.tick_params(axis='y', labelcolor=COLORS['soc'])
        ax3.set_ylim(0, 105)
        
        # Highlight high SoC region
        ax3.axhline(y=95, color=COLORS['soc'], linestyle='--', alpha=0.5, linewidth=1)
        ax3.fill_between(day_df['Timestamp'], 95, 100, 
                         where=(day_df['SoC_pct'] >= 95), alpha=0.2, color=COLORS['soc'])
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and labels
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_title(f'Power, Irradiance & Battery SoC - {date}', fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines = []
    labels = []
    if 'Power_W' in day_df.columns:
        lines.append(line1)
        labels.append('Power (W)')
    if 'Irradiance_Wm2' in day_df.columns:
        lines.append(line2)
        labels.append('Irradiance (W/m²)')
    if 'SoC_pct' in day_df.columns:
        lines.append(line3)
        labels.append('Battery SoC (%)')
    
    ax1.legend(lines, labels, loc='upper left')
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = f"{date}_Power_Irradiance_SoC.png"
    filepath = os.path.join(output_dir, 'daily', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_daily_temperature_effect(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create daily Temperature Effect scatter plot.
    X-axis: Cell Temperature
    Y-axis: Power or PR
    """
    day_df = df[df['Date'] == pd.to_datetime(date).date()].copy()
    
    if len(day_df) == 0 or 'Temperature_C' not in day_df.columns:
        return None
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Filter out low irradiance periods (nighttime/cloudy)
    if 'Irradiance_Wm2' in day_df.columns:
        day_df = day_df[day_df['Irradiance_Wm2'] > 100]
    
    if len(day_df) == 0:
        return None
    
    # Scatter plot of Power vs Temperature
    if 'Power_W' in day_df.columns:
        scatter = ax.scatter(day_df['Temperature_C'], day_df['Power_W'], 
                            c=day_df['Irradiance_Wm2'] if 'Irradiance_Wm2' in day_df.columns else COLORS['power'],
                            cmap='YlOrRd', alpha=0.7, s=50)
        
        if 'Irradiance_Wm2' in day_df.columns:
            cbar = plt.colorbar(scatter, ax=ax)
            cbar.set_label('Irradiance (W/m²)', fontsize=10)
        
        # Add trend line
        z = np.polyfit(day_df['Temperature_C'], day_df['Power_W'], 1)
        p = np.poly1d(z)
        temp_range = np.linspace(day_df['Temperature_C'].min(), day_df['Temperature_C'].max(), 100)
        ax.plot(temp_range, p(temp_range), '--', color=COLORS['temperature'], 
                linewidth=2, label=f'Trend: {z[0]:.1f} W/°C')
    
    ax.set_xlabel('Cell Temperature (°C)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Power (W)', fontsize=12, fontweight='bold')
    ax.set_title(f'Temperature Effect on Power - {date}', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = f"{date}_Temperature_Effect.png"
    filepath = os.path.join(output_dir, 'daily', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_daily_voltage_irradiance(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create daily Voltage and Irradiance line graph.
    Y-axis: Voltage (V), Irradiance (W/m²)
    X-axis: Time
    """
    day_df = df[df['Date'] == pd.to_datetime(date).date()].copy()
    
    if len(day_df) == 0:
        return None
    
    fig, ax1 = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Plot Voltage on primary axis
    if 'Voltage_V' in day_df.columns:
        ax1.plot(day_df['Timestamp'], day_df['Voltage_V'], 
                color='#9B59B6', linewidth=2, label='Voltage (V)')  # Purple
        ax1.set_ylabel('Voltage (V)', color='#9B59B6', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#9B59B6')
        ax1.fill_between(day_df['Timestamp'], day_df['Voltage_V'], alpha=0.2, color='#9B59B6')
    
    # Create secondary axis for Irradiance
    if 'Irradiance_Wm2' in day_df.columns:
        ax2 = ax1.twinx()
        ax2.plot(day_df['Timestamp'], day_df['Irradiance_Wm2'], 
                color=COLORS['irradiance'], linewidth=2, linestyle='--', label='Irradiance (W/m²)')
        ax2.set_ylabel('Irradiance (W/m²)', color=COLORS['irradiance'], fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=COLORS['irradiance'])
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and labels
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_title(f'Voltage & Irradiance - {date}', fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    if 'Irradiance_Wm2' in day_df.columns:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    else:
        ax1.legend(loc='upper right')
    
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = f"{date}_Voltage_Irradiance.png"
    filepath = os.path.join(output_dir, 'daily', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_daily_current_irradiance(
    df: pd.DataFrame,
    date: str,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create daily Current and Irradiance line graph.
    Y-axis: Current (A), Irradiance (W/m²)
    X-axis: Time
    """
    day_df = df[df['Date'] == pd.to_datetime(date).date()].copy()
    
    if len(day_df) == 0:
        return None
    
    fig, ax1 = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Plot Current on primary axis
    if 'Current_A' in day_df.columns:
        ax1.plot(day_df['Timestamp'], day_df['Current_A'], 
                color='#E74C3C', linewidth=2, label='Current (A)')  # Red
        ax1.set_ylabel('Current (A)', color='#E74C3C', fontsize=12, fontweight='bold')
        ax1.tick_params(axis='y', labelcolor='#E74C3C')
        ax1.fill_between(day_df['Timestamp'], day_df['Current_A'], alpha=0.2, color='#E74C3C')
    
    # Create secondary axis for Irradiance
    if 'Irradiance_Wm2' in day_df.columns:
        ax2 = ax1.twinx()
        ax2.plot(day_df['Timestamp'], day_df['Irradiance_Wm2'], 
                color=COLORS['irradiance'], linewidth=2, linestyle='--', label='Irradiance (W/m²)')
        ax2.set_ylabel('Irradiance (W/m²)', color=COLORS['irradiance'], fontsize=12, fontweight='bold')
        ax2.tick_params(axis='y', labelcolor=COLORS['irradiance'])
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45, ha='right')
    
    # Title and labels
    ax1.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax1.set_title(f'Current & Irradiance - {date}', fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    if 'Irradiance_Wm2' in day_df.columns:
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
    else:
        ax1.legend(loc='upper right')
    
    ax1.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = f"{date}_Current_Irradiance.png"
    filepath = os.path.join(output_dir, 'daily', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


# ============================================================================
# MONTHLY/AGGREGATED GRAPHS
# ============================================================================

def plot_pr_trend(
    daily_metrics: pd.DataFrame,
    output_dir: str,
    title_suffix: str = "",
    show_plot: bool = False
) -> Optional[str]:
    """
    Create Performance Ratio trend line graph.
    """
    if len(daily_metrics) == 0 or 'PR_pct' not in daily_metrics.columns:
        return None
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Remove None/NaN values
    plot_df = daily_metrics.dropna(subset=['PR_pct'])
    
    if len(plot_df) == 0:
        return None
    
    # Plot PR trend
    ax.plot(plot_df['Date'], plot_df['PR_pct'], 
            color=COLORS['pr'], linewidth=2, marker='o', markersize=6, label='Daily PR')
    
    # Add horizontal reference lines
    ax.axhline(y=80, color='green', linestyle='--', alpha=0.5, label='Good (80%)')
    ax.axhline(y=70, color='orange', linestyle='--', alpha=0.5, label='Fair (70%)')
    ax.axhline(y=60, color='red', linestyle='--', alpha=0.5, label='Poor (60%)')
    
    # Fill area under curve
    ax.fill_between(plot_df['Date'], plot_df['PR_pct'], alpha=0.2, color=COLORS['pr'])
    
    # Add rolling average
    if len(plot_df) >= 7:
        rolling_avg = plot_df['PR_pct'].rolling(window=7, min_periods=1).mean()
        ax.plot(plot_df['Date'], rolling_avg, 
                color='black', linewidth=2, linestyle='-', alpha=0.7, label='7-day Average')
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Performance Ratio (%)', fontsize=12, fontweight='bold')
    ax.set_title(f'Performance Ratio Trend {title_suffix}', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='lower left')
    ax.set_ylim(0, 110)
    ax.grid(True, alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    
    # Save
    date_range = f"{plot_df['Date'].min()}_{plot_df['Date'].max()}"
    filename = f"{date_range}_PR_Trend.png"
    filepath = os.path.join(output_dir, 'monthly', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_specific_yield_trend(
    daily_metrics: pd.DataFrame,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create Specific Yield (kWh/kWp) trend graph.
    """
    if len(daily_metrics) == 0 or 'Specific_Yield_kWhkWp' not in daily_metrics.columns:
        return None
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    plot_df = daily_metrics.dropna(subset=['Specific_Yield_kWhkWp'])
    
    if len(plot_df) == 0:
        return None
    
    # Bar chart for daily specific yield
    bars = ax.bar(plot_df['Date'], plot_df['Specific_Yield_kWhkWp'], 
                  color=COLORS['actual'], alpha=0.7, label='Daily Specific Yield')
    
    # Add cumulative line
    cumulative = plot_df['Specific_Yield_kWhkWp'].cumsum()
    ax2 = ax.twinx()
    ax2.plot(plot_df['Date'], cumulative, 
             color=COLORS['expected'], linewidth=2, marker='s', markersize=4, label='Cumulative')
    ax2.set_ylabel('Cumulative Specific Yield (kWh/kWp)', color=COLORS['expected'], fontsize=12, fontweight='bold')
    ax2.tick_params(axis='y', labelcolor=COLORS['expected'])
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Daily Specific Yield (kWh/kWp)', fontsize=12, fontweight='bold')
    ax.set_title('Specific Yield Over Time', fontsize=14, fontweight='bold', pad=20)
    
    # Combined legend
    lines1, labels1 = ax.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45, ha='right')
    fig.tight_layout()
    
    # Save
    date_range = f"{plot_df['Date'].min()}_{plot_df['Date'].max()}"
    filename = f"{date_range}_Specific_Yield.png"
    filepath = os.path.join(output_dir, 'monthly', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_expected_vs_actual(
    daily_metrics: pd.DataFrame,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create Expected vs Actual Yield comparison chart.
    """
    if len(daily_metrics) == 0:
        return None
    
    required_cols = ['Actual_Energy_kWh', 'Expected_Energy_kWh']
    if not all(col in daily_metrics.columns for col in required_cols):
        return None
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    plot_df = daily_metrics.dropna(subset=required_cols)
    
    if len(plot_df) == 0:
        return None
    
    x = np.arange(len(plot_df))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, plot_df['Expected_Energy_kWh'], width, 
                   label='Expected Yield', color=COLORS['expected'], alpha=0.8)
    bars2 = ax.bar(x + width/2, plot_df['Actual_Energy_kWh'], width, 
                   label='Actual Yield', color=COLORS['actual'], alpha=0.8)
    
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Energy (kWh)', fontsize=12, fontweight='bold')
    ax.set_title('Expected vs Actual Daily Yield', fontsize=14, fontweight='bold', pad=20)
    ax.set_xticks(x)
    ax.set_xticklabels([str(d) for d in plot_df['Date']], rotation=45, ha='right')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    fig.tight_layout()
    
    # Save
    date_range = f"{plot_df['Date'].min()}_{plot_df['Date'].max()}"
    filename = f"{date_range}_Expected_vs_Actual.png"
    filepath = os.path.join(output_dir, 'monthly', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_monthly_summary(
    monthly_metrics: pd.DataFrame,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create monthly summary bar chart with PR and Energy.
    """
    if len(monthly_metrics) == 0:
        return None
    
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    
    # 1. Monthly Energy Production
    ax1 = axes[0, 0]
    if 'Actual_Energy_kWh' in monthly_metrics.columns:
        x = np.arange(len(monthly_metrics))
        width = 0.35
        ax1.bar(x - width/2, monthly_metrics['Expected_Energy_kWh'], width, 
                label='Expected', color=COLORS['expected'], alpha=0.8)
        ax1.bar(x + width/2, monthly_metrics['Actual_Energy_kWh'], width, 
                label='Actual', color=COLORS['actual'], alpha=0.8)
        ax1.set_xlabel('Month')
        ax1.set_ylabel('Energy (kWh)')
        ax1.set_title('Monthly Energy Production')
        ax1.set_xticks(x)
        ax1.set_xticklabels(monthly_metrics['Month'], rotation=45, ha='right')
        ax1.legend()
        ax1.grid(True, alpha=0.3, axis='y')
    
    # 2. Monthly PR
    ax2 = axes[0, 1]
    if 'PR_pct' in monthly_metrics.columns:
        ax2.bar(monthly_metrics['Month'], monthly_metrics['PR_pct'], 
                color=COLORS['pr'], alpha=0.8)
        ax2.axhline(y=80, color='green', linestyle='--', alpha=0.5)
        ax2.set_xlabel('Month')
        ax2.set_ylabel('Performance Ratio (%)')
        ax2.set_title('Monthly Performance Ratio')
        ax2.set_ylim(0, 100)
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax2.grid(True, alpha=0.3, axis='y')
    
    # 3. Monthly Specific Yield
    ax3 = axes[1, 0]
    if 'Specific_Yield_kWhkWp' in monthly_metrics.columns:
        ax3.bar(monthly_metrics['Month'], monthly_metrics['Specific_Yield_kWhkWp'], 
                color=COLORS['actual'], alpha=0.8)
        ax3.set_xlabel('Month')
        ax3.set_ylabel('Specific Yield (kWh/kWp)')
        ax3.set_title('Monthly Specific Yield')
        plt.setp(ax3.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax3.grid(True, alpha=0.3, axis='y')
    
    # 4. Average Temperature and Irradiance
    ax4 = axes[1, 1]
    if 'Avg_Irradiance' in monthly_metrics.columns:
        ax4.bar(monthly_metrics['Month'], monthly_metrics['Avg_Irradiance'], 
                color=COLORS['irradiance'], alpha=0.8, label='Avg Irradiance')
        ax4.set_xlabel('Month')
        ax4.set_ylabel('Avg Irradiance (W/m²)')
        ax4.set_title('Monthly Average Conditions')
        
        if 'Avg_Temperature' in monthly_metrics.columns:
            ax4_twin = ax4.twinx()
            ax4_twin.plot(monthly_metrics['Month'], monthly_metrics['Avg_Temperature'], 
                         color=COLORS['temperature'], linewidth=2, marker='o', label='Avg Temperature')
            ax4_twin.set_ylabel('Avg Temperature (°C)', color=COLORS['temperature'])
            ax4_twin.tick_params(axis='y', labelcolor=COLORS['temperature'])
        
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45, ha='right')
        ax4.grid(True, alpha=0.3, axis='y')
    
    fig.suptitle('Monthly Performance Summary', fontsize=16, fontweight='bold', y=1.02)
    fig.tight_layout()
    
    # Save
    filename = f"Monthly_Summary.png"
    filepath = os.path.join(output_dir, 'monthly', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def plot_temperature_effect_scatter(
    df: pd.DataFrame,
    output_dir: str,
    show_plot: bool = False
) -> Optional[str]:
    """
    Create overall Temperature Effect scatter plot across all data.
    """
    if 'Temperature_C' not in df.columns or 'Power_W' not in df.columns:
        return None
    
    # Filter for meaningful data (daytime, good irradiance)
    plot_df = df.copy()
    if 'Irradiance_Wm2' in plot_df.columns:
        plot_df = plot_df[plot_df['Irradiance_Wm2'] > 200]
    
    if len(plot_df) < 10:
        return None
    
    fig, ax = plt.subplots(figsize=DEFAULT_FIGSIZE)
    
    # Create scatter plot
    scatter = ax.scatter(plot_df['Temperature_C'], plot_df['Power_W'],
                        c=plot_df['Irradiance_Wm2'] if 'Irradiance_Wm2' in plot_df.columns else COLORS['power'],
                        cmap='YlOrRd', alpha=0.5, s=20)
    
    if 'Irradiance_Wm2' in plot_df.columns:
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Irradiance (W/m²)', fontsize=10)
    
    # Add trend line
    z = np.polyfit(plot_df['Temperature_C'], plot_df['Power_W'], 1)
    p = np.poly1d(z)
    temp_range = np.linspace(plot_df['Temperature_C'].min(), plot_df['Temperature_C'].max(), 100)
    ax.plot(temp_range, p(temp_range), '--', color=COLORS['temperature'], 
            linewidth=3, label=f'Trend: {z[0]:.1f} W/°C')
    
    ax.set_xlabel('Cell Temperature (°C)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Power (W)', fontsize=12, fontweight='bold')
    ax.set_title('Temperature Effect on Power Output (All Data)', fontsize=14, fontweight='bold', pad=20)
    ax.legend(loc='upper right')
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    
    # Save
    filename = "Temperature_Effect_Overall.png"
    filepath = os.path.join(output_dir, 'monthly', filename)
    
    if show_plot:
        return fig
    
    return save_figure(fig, filepath)


def generate_all_daily_graphs(
    df: pd.DataFrame,
    output_dir: str
) -> List[str]:
    """
    Generate all daily graphs for each unique date in the data.
    Returns list of saved file paths.
    """
    saved_files = []
    
    if 'Date' not in df.columns:
        return saved_files
    
    unique_dates = df['Date'].unique()
    
    for date in unique_dates:
        date_str = str(date)
        
        # Power & Irradiance
        filepath = plot_daily_power_irradiance(df, date_str, output_dir)
        if filepath:
            saved_files.append(filepath)
        
        # Power, Irradiance & SoC
        if 'SoC_pct' in df.columns:
            filepath = plot_daily_power_irradiance_soc(df, date_str, output_dir)
            if filepath:
                saved_files.append(filepath)
        
        # Temperature Effect
        if 'Temperature_C' in df.columns:
            filepath = plot_daily_temperature_effect(df, date_str, output_dir)
            if filepath:
                saved_files.append(filepath)
        
        # Voltage & Irradiance
        if 'Voltage_V' in df.columns:
            filepath = plot_daily_voltage_irradiance(df, date_str, output_dir)
            if filepath:
                saved_files.append(filepath)
        
        # Current & Irradiance
        if 'Current_A' in df.columns:
            filepath = plot_daily_current_irradiance(df, date_str, output_dir)
            if filepath:
                saved_files.append(filepath)
    
    return saved_files


def generate_all_monthly_graphs(
    df: pd.DataFrame,
    daily_metrics: pd.DataFrame,
    monthly_metrics: pd.DataFrame,
    output_dir: str
) -> List[str]:
    """
    Generate all monthly/aggregated graphs.
    Returns list of saved file paths.
    """
    saved_files = []
    
    # PR Trend
    filepath = plot_pr_trend(daily_metrics, output_dir)
    if filepath:
        saved_files.append(filepath)
    
    # Specific Yield
    filepath = plot_specific_yield_trend(daily_metrics, output_dir)
    if filepath:
        saved_files.append(filepath)
    
    # Expected vs Actual
    filepath = plot_expected_vs_actual(daily_metrics, output_dir)
    if filepath:
        saved_files.append(filepath)
    
    # Monthly Summary
    if len(monthly_metrics) > 0:
        filepath = plot_monthly_summary(monthly_metrics, output_dir)
        if filepath:
            saved_files.append(filepath)
    
    # Temperature Effect Overall
    filepath = plot_temperature_effect_scatter(df, output_dir)
    if filepath:
        saved_files.append(filepath)
    
    return saved_files


# ============================================================================
# CALENDAR VIEW & ANOMALY DETECTION
# ============================================================================

def detect_daily_anomalies(daily_metrics: pd.DataFrame) -> pd.DataFrame:
    """
    Detect anomalies in daily metrics and return a dataframe with anomaly flags.
    
    Anomaly Types:
    - low_pr: PR < 60%
    - warning_pr: PR 60-70%
    - low_energy: Energy significantly below average
    - zero_energy: No energy generated
    - high_soc_day: >50% of day at high SoC (curtailment)
    """
    if len(daily_metrics) == 0:
        return daily_metrics.copy()
    
    df = daily_metrics.copy()
    
    # Initialize anomaly columns
    df['anomaly_type'] = 'normal'
    df['anomaly_severity'] = 0  # 0=normal, 1=warning, 2=critical
    df['anomaly_details'] = ''
    
    # Calculate thresholds
    avg_energy = df['Actual_Energy_kWh'].mean() if 'Actual_Energy_kWh' in df.columns else 0
    
    anomaly_details_list = []
    
    for idx, row in df.iterrows():
        anomalies = []
        severity = 0
        
        # Check PR anomalies
        if 'PR_pct' in df.columns and pd.notna(row.get('PR_pct')):
            pr = row['PR_pct']
            if pr < 50:
                anomalies.append('Very Low PR (<50%)')
                severity = max(severity, 2)
            elif pr < 60:
                anomalies.append('Low PR (<60%)')
                severity = max(severity, 2)
            elif pr < 70:
                anomalies.append('Warning PR (60-70%)')
                severity = max(severity, 1)
        
        # Check energy anomalies
        if 'Actual_Energy_kWh' in df.columns:
            energy = row['Actual_Energy_kWh']
            if energy == 0 or pd.isna(energy):
                anomalies.append('Zero Energy')
                severity = max(severity, 2)
            elif avg_energy > 0 and energy < avg_energy * 0.3:
                anomalies.append('Very Low Energy')
                severity = max(severity, 1)
        
        # Check high SoC (curtailment)
        if 'High_SoC_Points' in df.columns and 'Total_Points' in df.columns:
            if row['Total_Points'] > 0:
                soc_ratio = row['High_SoC_Points'] / row['Total_Points']
                if soc_ratio > 0.5:
                    anomalies.append('High Curtailment (>50% high SoC)')
                    # This is informational, not necessarily an issue
        
        # Set anomaly type
        if severity == 2:
            df.at[idx, 'anomaly_type'] = 'critical'
        elif severity == 1:
            df.at[idx, 'anomaly_type'] = 'warning'
        else:
            df.at[idx, 'anomaly_type'] = 'normal'
        
        df.at[idx, 'anomaly_severity'] = severity
        df.at[idx, 'anomaly_details'] = '; '.join(anomalies) if anomalies else 'No issues'
    
    return df


def get_pr_color(pr_value: float) -> str:
    """Get color based on PR value."""
    if pd.isna(pr_value):
        return '#CCCCCC'  # Gray for missing
    elif pr_value >= 80:
        return '#2ECC71'  # Green - Excellent
    elif pr_value >= 70:
        return '#82E0AA'  # Light Green - Good
    elif pr_value >= 60:
        return '#F4D03F'  # Yellow - Fair
    elif pr_value >= 50:
        return '#E67E22'  # Orange - Poor
    else:
        return '#E74C3C'  # Red - Critical


def get_energy_color(energy: float, max_energy: float) -> str:
    """Get color based on energy relative to maximum."""
    if pd.isna(energy) or max_energy == 0:
        return '#CCCCCC'  # Gray for missing
    ratio = energy / max_energy
    if ratio >= 0.8:
        return '#2ECC71'  # Green - High
    elif ratio >= 0.6:
        return '#82E0AA'  # Light Green - Good
    elif ratio >= 0.4:
        return '#F4D03F'  # Yellow - Medium
    elif ratio >= 0.2:
        return '#E67E22'  # Orange - Low
    else:
        return '#E74C3C'  # Red - Very Low


def plot_calendar_heatmap(
    daily_metrics: pd.DataFrame,
    metric: str = 'energy',  # 'energy', 'pr', or 'anomaly'
    output_dir: str = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a compact, dynamic calendar heatmap showing daily metrics.
    Shows Energy (kWh) and Avg Irradiance (W/m²) per day.
    """
    if len(daily_metrics) == 0 or 'Date' not in daily_metrics.columns:
        return None
    
    df = daily_metrics.copy()
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date')
    
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    # Cell dimensions - wider to fit full text labels
    cell_width = 2.2
    cell_height = 1.3
    month_header_height = 0.6
    top_margin = 1.2  # Extra space at top for title
    
    # Group dates by month
    months = pd.date_range(start=min_date.replace(day=1), end=max_date, freq='MS')
    
    # Pre-calculate total height needed
    total_rows = 0
    month_info = []
    
    for month_start in months:
        month_end = min(month_start + pd.DateOffset(months=1) - pd.DateOffset(days=1), max_date)
        actual_start = max(month_start, min_date)
        actual_end = min(month_end, max_date)
        
        if actual_start > actual_end:
            continue
        
        first_data_day = actual_start.day
        last_data_day = actual_end.day
        
        start_week = (first_data_day - 1 + month_start.weekday()) // 7
        end_week = (last_data_day - 1 + month_start.weekday()) // 7
        weeks_needed = end_week - start_week + 1
        
        month_info.append({
            'month_start': month_start,
            'actual_start': actual_start,
            'actual_end': actual_end,
            'start_week': start_week,
            'weeks_needed': weeks_needed,
            'month_name': actual_start.strftime('%B %Y')
        })
        total_rows += weeks_needed
    
    num_months = len(month_info)
    total_height = total_rows * cell_height + num_months * (month_header_height + 0.3) + top_margin
    fig_height = max(5, total_height * 0.55 + 1.5)
    
    fig, ax = plt.subplots(figsize=(12, fig_height))
    
    # Title at the very top
    if metric == 'energy':
        title = "Daily Energy & Irradiance"
        legend = "Color: Energy (Green=High, Red=Low) | Values: kWh, W/m²"
    elif metric == 'pr':
        title = "Daily Performance Ratio"
        legend = "Green>=80% | Yellow 60-80% | Red<60%"
    else:
        title = "Daily Anomaly Status"
        legend = "Green=Normal | Yellow=Warning | Red=Critical"
    
    ax.text(3.5 * cell_width, top_margin + 0.3, title, 
            ha='center', va='bottom', fontsize=13, fontweight='bold', color='#2C3E50')
    ax.text(3.5 * cell_width, top_margin + 0.1, legend,
            ha='center', va='top', fontsize=9, color='#666666')
    
    # Weekday headers - with proper spacing below title
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, wd in enumerate(weekdays):
        ax.text(i * cell_width + cell_width/2, top_margin - 0.4, wd, 
                ha='center', va='center', fontsize=9, fontweight='bold', color='#555555')
    
    current_y = top_margin - 0.8
    
    # Draw each month
    for info in month_info:
        month_start = info['month_start']
        actual_start = info['actual_start']
        actual_end = info['actual_end']
        start_week = info['start_week']
        
        # Month header with line
        ax.axhline(y=current_y + 0.1, xmin=0.02, xmax=0.98, color='#CCCCCC', linewidth=1)
        current_y -= month_header_height
        ax.text(3.5 * cell_width, current_y + 0.3, info['month_name'],
                ha='center', va='center', fontsize=10, fontweight='bold', color='#333333')
        
        # Draw days
        dates_in_range = pd.date_range(start=actual_start, end=actual_end, freq='D')
        
        for date in dates_in_range:
            day = date.day
            weekday = date.weekday()
            
            week_in_month = (day - 1 + month_start.weekday()) // 7
            week_offset = week_in_month - start_week
            
            # Get data
            date_data = df[df['Date'] == date]
            
            if len(date_data) > 0:
                row = date_data.iloc[0]
                energy = row.get('Actual_Energy_kWh', 0)
                irradiance = row.get('Avg_Irradiance', 0)
                pr = row.get('PR_pct', None)
                
                max_energy = df['Actual_Energy_kWh'].max() if 'Actual_Energy_kWh' in df.columns else 1
                
                if metric == 'energy':
                    color = get_energy_color(energy, max_energy)
                    line1 = f"Energy: {energy:.2f} kWh" if pd.notna(energy) else "-"
                    line2 = f"Irradiance: {irradiance:.0f} W/m²" if pd.notna(irradiance) else "-"
                elif metric == 'pr':
                    color = get_pr_color(pr)
                    line1 = f"PR: {pr:.0f}%" if pd.notna(pr) else "-"
                    line2 = f"Energy: {energy:.2f} kWh" if pd.notna(energy) else "-"
                else:  # anomaly
                    anomaly_df = detect_daily_anomalies(date_data)
                    severity = anomaly_df.iloc[0]['anomaly_severity']
                    if severity == 2:
                        color = '#E74C3C'
                    elif severity == 1:
                        color = '#F4D03F'
                    else:
                        color = '#2ECC71'
                    line1 = f"PR: {pr:.0f}%" if pd.notna(pr) else "OK"
                    line2 = f"Energy: {energy:.2f} kWh" if pd.notna(energy) else "-"
            else:
                color = '#F0F0F0'
                line1 = "-"
                line2 = "-"
            
            # Cell position
            x = weekday * cell_width
            y = current_y - (week_offset + 1) * cell_height
            
            # Draw cell with rounded appearance
            rect = plt.Rectangle((x + 0.03, y + 0.03), cell_width - 0.06, cell_height - 0.06,
                                  facecolor=color, edgecolor='white', linewidth=1.5)
            ax.add_patch(rect)
            
            # Day number (top-left, smaller)
            ax.text(x + 0.1, y + cell_height - 0.12, str(day),
                    ha='left', va='top', fontsize=7, color='#444444', fontweight='bold')
            
            # Line 1: Main value (center-top) - Energy or PR
            ax.text(x + cell_width/2, y + cell_height * 0.55, line1,
                    ha='center', va='center', fontsize=7.5, color='#222222', fontweight='bold')
            
            # Line 2: Secondary value (center-bottom) - Irradiance or Energy
            ax.text(x + cell_width/2, y + cell_height * 0.25, line2,
                    ha='center', va='center', fontsize=6.5, color='#555555')
        
        # Move down for next month
        current_y -= (info['weeks_needed'] * cell_height + 0.3)
    
    # Axis settings
    ax.set_xlim(-0.2, 7 * cell_width + 0.2)
    ax.set_ylim(current_y - 0.3, top_margin + 0.7)
    ax.set_aspect('equal')
    ax.axis('off')
    
    fig.tight_layout(pad=0.3)
    
    if show_plot:
        return fig
    
    if output_dir:
        filename = f"Calendar_{metric.title()}_View.png"
        filepath = os.path.join(output_dir, 'monthly', filename)
        return save_figure(fig, filepath)
    
    return None


def plot_daily_summary_cards(
    daily_metrics: pd.DataFrame,
    show_plot: bool = True
) -> Optional[plt.Figure]:
    """
    Create a summary card showing recent daily performance with anomaly indicators.
    """
    if len(daily_metrics) == 0:
        return None
    
    # Detect anomalies
    df = detect_daily_anomalies(daily_metrics.copy())
    
    # Get last 7 days
    df = df.sort_values('Date', ascending=False).head(7)
    df = df.sort_values('Date')
    
    fig, axes = plt.subplots(1, len(df), figsize=(min(18, len(df) * 2.5), 4))
    
    if len(df) == 1:
        axes = [axes]
    
    for i, (idx, row) in enumerate(df.iterrows()):
        ax = axes[i]
        
        # Card background color based on anomaly
        if row['anomaly_type'] == 'critical':
            bg_color = '#FADBD8'
            border_color = '#E74C3C'
        elif row['anomaly_type'] == 'warning':
            bg_color = '#FCF3CF'
            border_color = '#F4D03F'
        else:
            bg_color = '#D5F4E6'
            border_color = '#2ECC71'
        
        ax.set_facecolor(bg_color)
        for spine in ax.spines.values():
            spine.set_color(border_color)
            spine.set_linewidth(3)
        
        # Date
        date_str = pd.to_datetime(row['Date']).strftime('%b %d')
        ax.text(0.5, 0.92, date_str, ha='center', va='top', 
                fontsize=12, fontweight='bold', transform=ax.transAxes)
        
        # Energy
        energy = row.get('Actual_Energy_kWh', 0)
        ax.text(0.5, 0.65, f"{energy:.2f}", ha='center', va='center',
                fontsize=18, fontweight='bold', transform=ax.transAxes, color='#2C3E50')
        ax.text(0.5, 0.50, "kWh", ha='center', va='center',
                fontsize=10, transform=ax.transAxes, color='#7F8C8D')
        
        # PR
        pr = row.get('PR_pct', None)
        pr_text = f"PR: {pr:.0f}%" if pd.notna(pr) else "PR: N/A"
        pr_color = get_pr_color(pr)
        ax.text(0.5, 0.28, pr_text, ha='center', va='center',
                fontsize=11, fontweight='bold', transform=ax.transAxes, color=pr_color)
        
        # Anomaly indicator
        if row['anomaly_type'] != 'normal':
            ax.text(0.5, 0.08, "⚠️", ha='center', va='center',
                    fontsize=14, transform=ax.transAxes)
        else:
            ax.text(0.5, 0.08, "✓", ha='center', va='center',
                    fontsize=14, transform=ax.transAxes, color='#2ECC71')
        
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([])
        ax.set_yticks([])
    
    fig.suptitle("Last 7 Days Performance", fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    
    if show_plot:
        return fig
    
    return None


def get_anomaly_summary(daily_metrics: pd.DataFrame) -> dict:
    """
    Get a summary of anomalies detected in the data.
    """
    if len(daily_metrics) == 0:
        return {
            'total_days': 0,
            'normal_days': 0,
            'warning_days': 0,
            'critical_days': 0,
            'anomalies': []
        }
    
    df = detect_daily_anomalies(daily_metrics)
    
    summary = {
        'total_days': len(df),
        'normal_days': len(df[df['anomaly_type'] == 'normal']),
        'warning_days': len(df[df['anomaly_type'] == 'warning']),
        'critical_days': len(df[df['anomaly_type'] == 'critical']),
        'anomalies': []
    }
    
    # Get list of anomalies
    for _, row in df[df['anomaly_type'] != 'normal'].iterrows():
        summary['anomalies'].append({
            'date': row['Date'],
            'type': row['anomaly_type'],
            'details': row['anomaly_details']
        })
    
    return summary

