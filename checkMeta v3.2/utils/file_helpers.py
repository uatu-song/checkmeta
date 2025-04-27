"""
META Fantasy League Simulator - File Helpers
Provides robust file operations with error handling
"""

import os
import json
import shutil
import tempfile
from typing import Dict, List, Any, Optional
from config import get_config

def save_json_safely(data, filepath, create_backup=True):
    """Save JSON data with robust error handling
    
    Args:
        data: Data to save
        filepath: Path to save file
        create_backup: Whether to create a backup file
        
    Returns:
        bool: Success status
    """
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create a temp file for atomic write
    temp_file = None
    
    try:
        # Write to temporary file first
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp:
            temp_file = temp.name
            json.dump(data, temp, indent=2)
        
        # Create backup if needed
        if create_backup and os.path.exists(filepath):
            backup_path = f"{filepath}.bak"
            shutil.copy2(filepath, backup_path)
        
        # Atomic rename of temp file to target
        shutil.move(temp_file, filepath)
        return True
    
    except Exception as e:
        print(f"Error saving JSON file: {e}")
        
        # Clean up temp file if it exists
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
                
        # Try emergency save
        try:
            emergency_path = f"{filepath}.emergency"
            with open(emergency_path, 'w') as f:
                json.dump(data, f)
            print(f"Emergency backup saved to {emergency_path}")
        except Exception as e2:
            print(f"Emergency save also failed: {e2}")
            
        return False

def load_json_safely(filepath, default=None):
    """Load JSON data with robust error handling
    
    Args:
        filepath: Path to JSON file
        default: Default value if loading fails
        
    Returns:
        object: Loaded data or default
    """
    # Check if file exists
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        
        # Try to find backup
        backup_path = f"{filepath}.bak"
        emergency_path = f"{filepath}.emergency"
        
        if os.path.exists(backup_path):
            print(f"Found backup file: {backup_path}")
            filepath = backup_path
        elif os.path.exists(emergency_path):
            print(f"Found emergency file: {emergency_path}")
            filepath = emergency_path
        else:
            return default
    
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        
        # Try backup files if main load failed
        try:
            backup_path = f"{filepath}.bak"
            if os.path.exists(backup_path):
                print(f"Trying backup file: {backup_path}")
                with open(backup_path, 'r') as f:
                    return json.load(f)
        except Exception as e2:
            print(f"Backup load also failed: {e2}")
            
        return default

def ensure_directory_exists(dirpath):
    """Ensure directory exists, create if needed
    
    Args:
        dirpath: Directory path
        
    Returns:
        bool: Success status
    """
    try:
        os.makedirs(dirpath, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory: {e}")
        return False

def ensure_file_paths():
    """Ensure all config-defined file paths exist
    
    Returns:
        bool: Success status
    """
    config = get_config()
    
    # List of directories to check/create
    directories = [
        config.paths["results_dir"],
        config.paths["pgn_dir"],
        config.paths["reports_dir"],
        config.paths["stats_dir"]
    ]
    
    success = True
    for directory in directories:
        if not ensure_directory_exists(directory):
            success = False
    
    return success

def get_filename_with_timestamp(base_name, extension, use_date_only=False):
    """Create a filename with a timestamp
    
    Args:
        base_name: Base filename
        extension: File extension
        use_date_only: Whether to use date only (no time)
        
    Returns:
        str: Filename with timestamp
    """
    config = get_config()
    
    if use_date_only:
        timestamp = datetime.datetime.now().strftime("%Y%m%d")
    else:
        timestamp = config.get_timestamp()
    
    # Clean extension
    if not extension.startswith('.'):
        extension = '.' + extension
    
    return f"{base_name}_{timestamp}{extension}"