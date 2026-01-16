"""
Multi-Site Comparison Visualizations
Plotting functions for comparing multiple solar installation sites.
"""

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple


# Color palette for sites (max 10 sites)
SITE_COLORS = [
    '#3498DB',  # Blue
    '#E74C3C',  # Red
    '#2ECC71',  # Green
    '#9B59B6',  # Purple
    '#F39C12',  # Orange
    '#1ABC9C',  # Teal
    '#E91E63',  # Pink
    '#00BCD4',  # Cyan
    '#FF5722',  # Deep Orange
    '#607D8B',  # Blue Grey
]


def get_site_color(index: int) -> str:
    """Get a color for a site based on its index."""
    return SITE_COLORS[index % len(SITE_COLORS)]


def plot_multi_site_pr_bar(
    comparison_df: pd.DataFrame,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a bar chart comparing Performance Ratio across sites.
    
    Args:
        comparison_df: DataFrame with 'Site Name' and 'Avg PR (%)' columns
        show_plot: If True, return figure for display
    
    Returns:
        Figure object if show_plot=True
    """
    if comparison_df.empty or 'Avg PR (%)' not in comparison_df.columns:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sites = comparison_df['Site Name'].tolist()
    pr_values = comparison_df['Avg PR (%)'].tolist()
    
    # Create bars with colors based on PR value
    colors = []
    for pr in pr_values:
        if pr >= 80:
            colors.append('#2ECC71')  # Green - Excellent
        elif pr >= 70:
            colors.append('#F1C40F')  # Yellow - Good
        elif pr >= 60:
            colors.append('#E67E22')  # Orange - Fair
        else:
            colors.append('#E74C3C')  # Red - Poor
    
    bars = ax.bar(sites, pr_values, color=colors, edgecolor='white', linewidth=1.5)
    
    # Add value labels on bars
    for bar, val in zip(bars, pr_values):
        height = bar.get_height()
        ax.annotate(f'{val:.1f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold')
    
    # Add reference lines
    ax.axhline(y=80, color='#2ECC71', linestyle='--', linewidth=1, alpha=0.7, label='Excellent (80%)')
    ax.axhline(y=70, color='#F1C40F', linestyle='--', linewidth=1, alpha=0.7, label='Good (70%)')
    ax.axhline(y=60, color='#E67E22', linestyle='--', linewidth=1, alpha=0.7, label='Fair (60%)')
    
    ax.set_ylabel('Performance Ratio (%)', fontsize=12)
    ax.set_xlabel('Site', fontsize=12)
    ax.set_title('Performance Ratio Comparison', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    
    # Styling
    ax.set_ylim(0, max(pr_values) * 1.15 if pr_values else 100)
    ax.set_facecolor('#f8f9fa')
    ax.grid(axis='y', alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_yield_bar(
    comparison_df: pd.DataFrame,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a bar chart comparing Daily Specific Yield across sites.
    
    Args:
        comparison_df: DataFrame with 'Site Name' and 'Avg Daily Yield (kWh/kWp)' columns
        show_plot: If True, return figure for display
    
    Returns:
        Figure object if show_plot=True
    """
    if comparison_df.empty or 'Avg Daily Yield (kWh/kWp)' not in comparison_df.columns:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    sites = comparison_df['Site Name'].tolist()
    yield_values = comparison_df['Avg Daily Yield (kWh/kWp)'].tolist()
    
    # Assign colors by index
    colors = [get_site_color(i) for i in range(len(sites))]
    
    bars = ax.bar(sites, yield_values, color=colors, edgecolor='white', linewidth=1.5)
    
    # Add value labels on bars
    for bar, val in zip(bars, yield_values):
        height = bar.get_height()
        ax.annotate(f'{val:.2f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom',
                    fontsize=11, fontweight='bold')
    
    ax.set_ylabel('Daily Specific Yield (kWh/kWp)', fontsize=12)
    ax.set_xlabel('Site', fontsize=12)
    ax.set_title('Daily Energy Production per kWp', fontsize=14, fontweight='bold')
    
    # Styling
    ax.set_ylim(0, max(yield_values) * 1.15 if yield_values else 5)
    ax.set_facecolor('#f8f9fa')
    ax.grid(axis='y', alpha=0.3)
    
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_pr_trend(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a time series overlay of daily PR for all sites.
    
    Args:
        sites: Dictionary of site data
        date_range: Optional date filter
        show_plot: If True, return figure for display
    
    Returns:
        Figure object if show_plot=True
    """
    from modules.multi_site import get_daily_metrics_for_comparison
    
    pr_data = get_daily_metrics_for_comparison(sites, 'PR_pct', date_range)
    
    if pr_data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, site_name in enumerate(pr_data.columns):
        color = get_site_color(i)
        ax.plot(pr_data.index, pr_data[site_name], 
                color=color, linewidth=2, marker='o', markersize=4,
                label=site_name, alpha=0.8)
    
    # Add reference bands
    ax.axhspan(80, 100, color='#2ECC71', alpha=0.1)
    ax.axhspan(70, 80, color='#F1C40F', alpha=0.1)
    ax.axhspan(60, 70, color='#E67E22', alpha=0.1)
    ax.axhspan(0, 60, color='#E74C3C', alpha=0.1)
    
    ax.set_ylabel('Performance Ratio (%)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_title('Daily Performance Ratio Trend - All Sites', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')
    
    # Styling
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_yield_trend(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a time series overlay of daily Specific Yield for all sites.
    Normalizes energy by each site's nominal power.
    """
    if not sites:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, (site_id, site_data) in enumerate(sites.items()):
        daily = site_data['daily_metrics'].copy()
        
        if date_range and date_range[0] and date_range[1]:
            # Convert string dates to date objects for comparison
            start_dt = pd.to_datetime(date_range[0]).date()
            end_dt = pd.to_datetime(date_range[1]).date()
            daily_dates = pd.to_datetime(daily['Date']).dt.date
            mask = (daily_dates >= start_dt) & (daily_dates <= end_dt)
            daily = daily[mask]
        
        if 'Actual_Energy_kWh' not in daily.columns:
            continue
        
        # Calculate daily specific yield
        nominal = site_data['nominal_power_kwp']
        daily['Specific_Yield'] = daily['Actual_Energy_kWh'] / nominal if nominal > 0 else 0
        
        dates = pd.to_datetime(daily['Date'])
        color = get_site_color(i)
        
        ax.plot(dates, daily['Specific_Yield'],
                color=color, linewidth=2, marker='o', markersize=4,
                label=site_data['name'], alpha=0.8)
    
    ax.set_ylabel('Daily Specific Yield (kWh/kWp)', fontsize=12)
    ax.set_xlabel('Date', fontsize=12)
    ax.set_title('Daily Energy Production per kWp - All Sites', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    
    # Format x-axis
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')
    
    # Styling
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_pr_boxplot(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create box plots showing PR distribution for each site.
    Great for comparing consistency across sites.
    """
    from modules.multi_site import get_daily_metrics_for_comparison
    
    pr_data = get_daily_metrics_for_comparison(sites, 'PR_pct', date_range)
    
    if pr_data.empty:
        return None
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Prepare data for boxplot
    data = [pr_data[col].dropna().values for col in pr_data.columns]
    positions = list(range(len(pr_data.columns)))
    
    bp = ax.boxplot(data, positions=positions, patch_artist=True, widths=0.6)
    
    # Color each box
    for i, (box, median) in enumerate(zip(bp['boxes'], bp['medians'])):
        color = get_site_color(i)
        box.set_facecolor(color)
        box.set_alpha(0.7)
        median.set_color('black')
        median.set_linewidth(2)
    
    # Add reference lines
    ax.axhline(y=80, color='#2ECC71', linestyle='--', linewidth=1, alpha=0.7, label='Excellent')
    ax.axhline(y=70, color='#F1C40F', linestyle='--', linewidth=1, alpha=0.7, label='Good')
    
    ax.set_xticklabels(pr_data.columns, rotation=45, ha='right')
    ax.set_ylabel('Performance Ratio (%)', fontsize=12)
    ax.set_xlabel('Site', fontsize=12)
    ax.set_title('PR Distribution by Site', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=9)
    
    ax.set_facecolor('#f8f9fa')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_monthly_heatmap(
    sites: Dict[str, Dict],
    metric: str = 'pr',
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a heatmap with sites as rows and months as columns.
    
    Args:
        sites: Dictionary of site data
        metric: 'pr' for Performance Ratio or 'yield' for Specific Yield
        show_plot: If True, return figure for display
    """
    if not sites:
        return None
    
    # Collect monthly data for all sites
    all_monthly = {}
    
    for site_id, site_data in sites.items():
        monthly = site_data['monthly_metrics']
        if monthly is None or len(monthly) == 0:
            continue
        
        if metric == 'pr' and 'PR_pct' in monthly.columns:
            values = monthly.set_index('Month')['PR_pct']
        elif metric == 'yield' and 'Actual_Energy_kWh' in monthly.columns:
            # Calculate monthly specific yield
            values = monthly.set_index('Month')['Actual_Energy_kWh'] / site_data['nominal_power_kwp']
        else:
            continue
        
        all_monthly[site_data['name']] = values
    
    if not all_monthly:
        return None
    
    # Create DataFrame
    heatmap_df = pd.DataFrame(all_monthly).T
    
    fig, ax = plt.subplots(figsize=(14, max(4, len(heatmap_df) * 0.8)))
    
    # Create heatmap
    cmap = 'RdYlGn' if metric == 'pr' else 'YlGnBu'
    im = ax.imshow(heatmap_df.values, cmap=cmap, aspect='auto')
    
    # Add colorbar
    label = 'Performance Ratio (%)' if metric == 'pr' else 'Specific Yield (kWh/kWp)'
    cbar = plt.colorbar(im, ax=ax, label=label)
    
    # Set ticks
    ax.set_xticks(range(len(heatmap_df.columns)))
    ax.set_xticklabels(heatmap_df.columns, rotation=45, ha='right')
    ax.set_yticks(range(len(heatmap_df.index)))
    ax.set_yticklabels(heatmap_df.index)
    
    # Add value annotations
    for i in range(len(heatmap_df.index)):
        for j in range(len(heatmap_df.columns)):
            val = heatmap_df.iloc[i, j]
            if pd.notna(val):
                text_color = 'white' if val < heatmap_df.values.mean() else 'black'
                fmt = f'{val:.1f}%' if metric == 'pr' else f'{val:.1f}'
                ax.text(j, i, fmt, ha='center', va='center', color=text_color, fontsize=9)
    
    title = 'Monthly Performance Ratio by Site' if metric == 'pr' else 'Monthly Specific Yield by Site'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Site', fontsize=12)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_ranking(
    comparison_df: pd.DataFrame,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create a combined ranking visualization showing both PR and Yield rankings.
    """
    if comparison_df.empty or 'PR Rank' not in comparison_df.columns:
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Sort by PR for left chart
    pr_sorted = comparison_df.sort_values('Avg PR (%)', ascending=True)
    colors_pr = [get_site_color(i) for i in range(len(pr_sorted))]
    
    ax1.barh(pr_sorted['Site Name'], pr_sorted['Avg PR (%)'], color=colors_pr, edgecolor='white')
    ax1.set_xlabel('Performance Ratio (%)', fontsize=12)
    ax1.set_title('Sites Ranked by PR', fontsize=13, fontweight='bold')
    ax1.set_xlim(0, 100)
    
    # Add value labels
    for i, (idx, row) in enumerate(pr_sorted.iterrows()):
        ax1.text(row['Avg PR (%)'] + 1, i, f"{row['Avg PR (%)']:.1f}%", va='center', fontsize=10)
    
    # Sort by Yield for right chart
    yield_sorted = comparison_df.sort_values('Avg Daily Yield (kWh/kWp)', ascending=True)
    colors_yield = [get_site_color(i) for i in range(len(yield_sorted))]
    
    ax2.barh(yield_sorted['Site Name'], yield_sorted['Avg Daily Yield (kWh/kWp)'], 
             color=colors_yield, edgecolor='white')
    ax2.set_xlabel('Daily Specific Yield (kWh/kWp)', fontsize=12)
    ax2.set_title('Sites Ranked by Yield', fontsize=13, fontweight='bold')
    
    # Add value labels
    max_yield = yield_sorted['Avg Daily Yield (kWh/kWp)'].max()
    for i, (idx, row) in enumerate(yield_sorted.iterrows()):
        ax2.text(row['Avg Daily Yield (kWh/kWp)'] + max_yield * 0.02, i, 
                 f"{row['Avg Daily Yield (kWh/kWp)']:.2f}", va='center', fontsize=10)
    
    for ax in [ax1, ax2]:
        ax.set_facecolor('#f8f9fa')
        ax.grid(axis='x', alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_hourly_specific_yield(
    sites: Dict[str, Dict],
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create hourly-averaged specific yield (kW/kWp) comparison for all sites.
    Shows normalized power output by hour of day for fair comparison.
    """
    if not sites:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, (site_id, site_data) in enumerate(sites.items()):
        analysis_df = site_data['analysis_df']
        
        if 'Power_W' not in analysis_df.columns or 'Hour' not in analysis_df.columns:
            continue
        
        # Calculate hourly average power per kWp
        nominal = site_data['nominal_power_kwp']
        hourly_avg = analysis_df.groupby('Hour')['Power_W'].mean() / 1000  # Convert to kW
        hourly_specific = hourly_avg / nominal if nominal > 0 else hourly_avg  # kW/kWp
        
        color = get_site_color(i)
        ax.plot(hourly_specific.index, hourly_specific.values,
                color=color, linewidth=2, marker='o', markersize=5,
                label=site_data['name'], alpha=0.8)
    
    ax.set_xlabel('Hour of Day', fontsize=12)
    ax.set_ylabel('Normalized Power (kW/kWp)', fontsize=12)
    ax.set_title('Hourly Average Power per kWp - All Sites', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    ax.set_xlim(0, 23)
    ax.set_xticks(range(0, 24, 2))
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_power_per_unit(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create daily normalized power (kW/kWp) trend for fair comparison.
    Shows max daily power per unit installed capacity.
    """
    if not sites:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, (site_id, site_data) in enumerate(sites.items()):
        daily = site_data['daily_metrics'].copy()
        
        if date_range and date_range[0] and date_range[1]:
            start_dt = pd.to_datetime(date_range[0]).date()
            end_dt = pd.to_datetime(date_range[1]).date()
            daily_dates = pd.to_datetime(daily['Date']).dt.date
            mask = (daily_dates >= start_dt) & (daily_dates <= end_dt)
            daily = daily[mask]
        
        if 'Max_Power_kW' not in daily.columns:
            continue
        
        # Calculate max power per kWp
        nominal = site_data['nominal_power_kwp']
        daily['Power_per_kWp'] = daily['Max_Power_kW'] / nominal if nominal > 0 else 0
        
        dates = pd.to_datetime(daily['Date'])
        color = get_site_color(i)
        
        ax.plot(dates, daily['Power_per_kWp'],
                color=color, linewidth=2, marker='o', markersize=3,
                label=site_data['name'], alpha=0.8)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Max Power per kWp (kW/kWp)', fontsize=12)
    ax.set_title('Daily Maximum Normalized Power - All Sites', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')
    
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_irradiance_combined(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create combined irradiance trend for all sites.
    Shows daily average irradiance comparison.
    """
    if not sites:
        return None
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for i, (site_id, site_data) in enumerate(sites.items()):
        daily = site_data['daily_metrics'].copy()
        
        if date_range and date_range[0] and date_range[1]:
            start_dt = pd.to_datetime(date_range[0]).date()
            end_dt = pd.to_datetime(date_range[1]).date()
            daily_dates = pd.to_datetime(daily['Date']).dt.date
            mask = (daily_dates >= start_dt) & (daily_dates <= end_dt)
            daily = daily[mask]
        
        if 'Avg_Irradiance' not in daily.columns:
            continue
        
        dates = pd.to_datetime(daily['Date'])
        color = get_site_color(i)
        
        ax.plot(dates, daily['Avg_Irradiance'],
                color=color, linewidth=2, marker='o', markersize=3,
                label=site_data['name'], alpha=0.8)
    
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Avg Daily Irradiance (W/m²)', fontsize=12)
    ax.set_title('Daily Irradiance Comparison - All Sites', fontsize=14, fontweight='bold')
    ax.legend(loc='upper right', fontsize=10)
    
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    plt.xticks(rotation=45, ha='right')
    
    ax.set_facecolor('#f8f9fa')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_irradiance_individual(
    sites: Dict[str, Dict],
    date_range: Tuple[str, str] = None,
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create individual irradiance plots for each site in a grid.
    """
    if not sites:
        return None
    
    n_sites = len(sites)
    if n_sites == 0:
        return None
    
    # Calculate grid dimensions
    n_cols = min(2, n_sites)
    n_rows = (n_sites + n_cols - 1) // n_cols
    
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(7 * n_cols, 4 * n_rows))
    
    # Handle single plot case
    if n_sites == 1:
        axes = np.array([axes])
    axes = np.atleast_1d(axes).flatten()
    
    for i, (site_id, site_data) in enumerate(sites.items()):
        ax = axes[i]
        daily = site_data['daily_metrics'].copy()
        
        if date_range and date_range[0] and date_range[1]:
            start_dt = pd.to_datetime(date_range[0]).date()
            end_dt = pd.to_datetime(date_range[1]).date()
            daily_dates = pd.to_datetime(daily['Date']).dt.date
            mask = (daily_dates >= start_dt) & (daily_dates <= end_dt)
            daily = daily[mask]
        
        if 'Avg_Irradiance' in daily.columns:
            dates = pd.to_datetime(daily['Date'])
            color = get_site_color(i)
            
            ax.fill_between(dates, daily['Avg_Irradiance'], alpha=0.3, color=color)
            ax.plot(dates, daily['Avg_Irradiance'],
                    color=color, linewidth=2, alpha=0.8)
            
            avg_irr = daily['Avg_Irradiance'].mean()
            ax.axhline(y=avg_irr, color='red', linestyle='--', linewidth=1, alpha=0.7)
            ax.text(dates.iloc[-1], avg_irr, f' Avg: {avg_irr:.0f}', 
                    va='center', fontsize=9, color='red')
        
        ax.set_title(f"{site_data['name']}", fontsize=11, fontweight='bold')
        ax.set_xlabel('Date', fontsize=10)
        ax.set_ylabel('Irradiance (W/m²)', fontsize=10)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(axis='x', rotation=45)
        ax.set_facecolor('#f8f9fa')
        ax.grid(True, alpha=0.3)
    
    # Hide empty subplots
    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)
    
    plt.suptitle('Daily Irradiance by Site', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None


def plot_multi_site_hourly_power_irradiance(
    sites: Dict[str, Dict],
    show_plot: bool = False
) -> Optional[plt.Figure]:
    """
    Create combined hourly power (per unit) and irradiance profiles.
    Shows overlay of normalized power vs irradiance by hour of day.
    """
    if not sites:
        return None
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Left: Normalized Power by Hour
    for i, (site_id, site_data) in enumerate(sites.items()):
        analysis_df = site_data['analysis_df']
        
        if 'Power_W' not in analysis_df.columns or 'Hour' not in analysis_df.columns:
            continue
        
        nominal = site_data['nominal_power_kwp']
        hourly_avg = analysis_df.groupby('Hour')['Power_W'].mean() / 1000
        hourly_specific = hourly_avg / nominal if nominal > 0 else hourly_avg
        
        color = get_site_color(i)
        ax1.plot(hourly_specific.index, hourly_specific.values,
                color=color, linewidth=2, marker='o', markersize=4,
                label=site_data['name'], alpha=0.8)
    
    ax1.set_xlabel('Hour of Day', fontsize=12)
    ax1.set_ylabel('Power (kW/kWp)', fontsize=12)
    ax1.set_title('Normalized Power Profile', fontsize=13, fontweight='bold')
    ax1.legend(loc='upper right', fontsize=9)
    ax1.set_xlim(0, 23)
    ax1.set_xticks(range(0, 24, 3))
    ax1.set_facecolor('#f8f9fa')
    ax1.grid(True, alpha=0.3)
    
    # Right: Irradiance by Hour
    for i, (site_id, site_data) in enumerate(sites.items()):
        analysis_df = site_data['analysis_df']
        
        if 'Irradiance_Wm2' not in analysis_df.columns or 'Hour' not in analysis_df.columns:
            continue
        
        hourly_irr = analysis_df.groupby('Hour')['Irradiance_Wm2'].mean()
        
        color = get_site_color(i)
        ax2.plot(hourly_irr.index, hourly_irr.values,
                color=color, linewidth=2, marker='s', markersize=4,
                label=site_data['name'], alpha=0.8)
    
    ax2.set_xlabel('Hour of Day', fontsize=12)
    ax2.set_ylabel('Irradiance (W/m²)', fontsize=12)
    ax2.set_title('Irradiance Profile', fontsize=13, fontweight='bold')
    ax2.legend(loc='upper right', fontsize=9)
    ax2.set_xlim(0, 23)
    ax2.set_xticks(range(0, 24, 3))
    ax2.set_facecolor('#f8f9fa')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    if show_plot:
        return fig
    
    plt.close(fig)
    return None
