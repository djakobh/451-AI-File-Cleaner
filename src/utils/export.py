"""
Export utilities for generating reports
"""

import csv
import json
from typing import List, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def export_to_csv(data: List[Dict], filepath: str):
    """
    Export scan results to CSV
    
    Args:
        data: List of file dictionaries
        filepath: Output CSV file path
    """
    if not data:
        raise ValueError("No data to export")
    
    # Define columns to export
    columns = [
        'path', 'name', 'extension', 'category',
        'size_mb', 'accessed_days_ago', 'modified_days_ago',
        'recommend_delete', 'confidence', 'ml_prediction', 'ml_confidence',
        'is_anomaly', 'is_disposable_ext', 'is_hidden'
    ]
    
    try:
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(data)
        
        logger.info(f"Exported {len(data)} rows to {filepath}")
    
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        raise


def export_to_json(data: List[Dict], filepath: str):
    """
    Export scan results to JSON
    
    Args:
        data: List of file dictionaries
        filepath: Output JSON file path
    """
    if not data:
        raise ValueError("No data to export")
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(data)} entries to {filepath}")
    
    except Exception as e:
        logger.error(f"Error exporting to JSON: {e}")
        raise