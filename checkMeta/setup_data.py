#!/usr/bin/env python3
"""
META Fantasy League Simulator - Data Setup Script
Sets up data directories and moves files to their proper locations
"""

import os
import shutil
import sys
from data.loaders import ensure_data_directories, get_data_filepath

def setup_data_directories():
    """Create the data directory structure"""
    print("Setting up data directories...")
    ensure_data_directories()
    print("Data directories created.")

def move_file_to_data_dir(source_file, target_subdir):
    """Move a file to the appropriate data subdirectory
    
    Args:
        source_file (str): Path to the source file
        target_subdir (str): Target subdirectory in data/
    
    Returns:
        bool: True if successful, False otherwise
    """
    if not os.path.exists(source_file):
        print(f"Error: Source file '{source_file}' does not exist")
        return False
    
    target_path = get_data_filepath(target_subdir, os.path.basename(source_file))
    
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        
        # Copy the file
        shutil.copy2(source_file, target_path)
        print(f"Copied: {source_file} -> {target_path}")
        return True
    except Exception as e:
        print(f"Error moving file: {e}")
        return False

def main():
    """Main function to set up data structure"""
    print("META Fantasy League Simulator - Data Setup")
    print("=========================================")
    
    # Create data directories
    setup_data_directories()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        lineup_file = sys.argv[1]
        print(f"Using lineup file: {lineup_file}")
    else:
        lineup_file = "All Lineups 1.xlsx"
        print(f"Using default lineup file: {lineup_file}")
    
    if len(sys.argv) > 2:
        attribute_file = sys.argv[2]
        print(f"Using attribute file: {attribute_file}")
    else:
        attribute_file = "Attribute Stats.csv"
        print(f"Using default attribute file: {attribute_file}")
    
    # Move files to their appropriate locations
    print("\nMoving files to data directories...")
    
    # Move lineup file
    if move_file_to_data_dir(lineup_file, "lineups"):
        print(f"✓ Lineup file moved to data/lineups/")
    else:
        print(f"✗ Failed to move lineup file")
    
    # Move attribute file
    if move_file_to_data_dir(attribute_file, "attributes"):
        print(f"✓ Attribute file moved to data/attributes/")
    else:
        print(f"✗ Failed to move attribute file")
    
    print("\nSetup complete. You can now run the simulator.")
    print("\nUsage: python main.py [day_number] [lineup_file]")

if __name__ == "__main__":
    main()