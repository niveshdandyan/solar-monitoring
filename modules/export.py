"""
Export Module
High-resolution image export and batch processing
"""

import os
import zipfile
from datetime import datetime
from typing import List, Optional
import shutil


def get_export_directory(base_dir: str = "exports") -> str:
    """
    Get or create the export directory.
    """
    os.makedirs(base_dir, exist_ok=True)
    os.makedirs(os.path.join(base_dir, "daily"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "monthly"), exist_ok=True)
    return base_dir


def generate_filename(
    date: str,
    graph_type: str,
    extension: str = "png"
) -> str:
    """
    Generate standardized filename.
    Format: YYYY-MM-DD_Graph_Type.png
    """
    # Sanitize date
    date_clean = str(date).replace("/", "-").replace(" ", "_")
    
    # Sanitize graph type
    graph_type_clean = graph_type.replace(" ", "_").replace("/", "_")
    
    return f"{date_clean}_{graph_type_clean}.{extension}"


def create_zip_archive(
    files: List[str],
    output_path: str,
    archive_name: str = None
) -> str:
    """
    Create a ZIP archive of all exported files.
    
    Args:
        files: List of file paths to include
        output_path: Directory to save the ZIP file
        archive_name: Optional custom name for the archive
    
    Returns:
        Path to the created ZIP file
    """
    if archive_name is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"Solar_Performance_Report_{timestamp}.zip"
    
    zip_path = os.path.join(output_path, archive_name)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            if os.path.exists(file_path):
                # Use relative path within archive
                arcname = os.path.basename(file_path)
                zipf.write(file_path, arcname)
    
    return zip_path


def list_exported_files(export_dir: str) -> dict:
    """
    List all exported files organized by category.
    """
    files = {
        'daily': [],
        'monthly': [],
        'other': []
    }
    
    daily_dir = os.path.join(export_dir, 'daily')
    monthly_dir = os.path.join(export_dir, 'monthly')
    
    if os.path.exists(daily_dir):
        files['daily'] = [
            os.path.join(daily_dir, f) 
            for f in os.listdir(daily_dir) 
            if f.endswith(('.png', '.jpg', '.jpeg'))
        ]
    
    if os.path.exists(monthly_dir):
        files['monthly'] = [
            os.path.join(monthly_dir, f) 
            for f in os.listdir(monthly_dir) 
            if f.endswith(('.png', '.jpg', '.jpeg'))
        ]
    
    # Sort files
    files['daily'].sort()
    files['monthly'].sort()
    
    return files


def clean_export_directory(export_dir: str):
    """
    Clean all files from export directories.
    """
    for subdir in ['daily', 'monthly']:
        dir_path = os.path.join(export_dir, subdir)
        if os.path.exists(dir_path):
            for file in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)


def export_dataframe_to_csv(
    df,
    output_path: str,
    filename: str = "solar_data_processed.csv"
) -> str:
    """
    Export processed dataframe to CSV.
    """
    filepath = os.path.join(output_path, filename)
    df.to_csv(filepath, index=False)
    return filepath


def get_export_summary(files: dict) -> str:
    """
    Generate a summary of exported files.
    """
    total = len(files['daily']) + len(files['monthly'])
    
    summary = f"""
## Export Summary

**Total Files Generated:** {total}

### Daily Reports: {len(files['daily'])}
"""
    
    for f in files['daily'][:10]:
        summary += f"- {os.path.basename(f)}\n"
    
    if len(files['daily']) > 10:
        summary += f"- ... and {len(files['daily']) - 10} more\n"
    
    summary += f"""
### Monthly Reports: {len(files['monthly'])}
"""
    
    for f in files['monthly']:
        summary += f"- {os.path.basename(f)}\n"
    
    return summary
