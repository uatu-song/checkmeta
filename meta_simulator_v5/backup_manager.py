"""
META Fantasy League Simulator - Backup Manager
System for versioning and backing up simulator state
"""

import os
import json
import shutil
import logging
import datetime
from typing import Dict, Any, Optional, List

class BackupManager:
    """System for versioning and backing up simulator state"""
    
    def __init__(self, config):
        """Initialize the backup manager
        
        Args:
            config: Configuration manager
        """
        self.config = config
        self.backup_dir = config.get("paths.backups_dir", "backups")
        self.logger = logging.getLogger("system.backup")
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_snapshot(self, day_number: int, name: Optional[str] = None) -> str:
        """Create a snapshot of the current simulator state
        
        Args:
            day_number: Day number
            name: Optional snapshot name
            
        Returns:
            str: Path to snapshot directory
        """
        timestamp = datetime.datetime.now().strftime(
            self.config.get("date.timestamp_format", "%Y%m%d_%H%M%S")
        )
        snapshot_name = name or f"day_{day_number}_{timestamp}"
        snapshot_dir = os.path.join(self.backup_dir, snapshot_name)
        
        # Create snapshot directory
        os.makedirs(snapshot_dir, exist_ok=True)
        
        # Backup key directories
        directories_to_backup = [
            self.config.get("paths.results_dir", "results"),
            self.config.get("paths.pgn_dir", "results/pgn"),
            self.config.get("paths.stats_dir", "results/stats")
        ]
        
        for directory in directories_to_backup:
            if os.path.exists(directory):
                dest_dir = os.path.join(snapshot_dir, os.path.basename(directory))
                self.logger.info(f"Backing up {directory} to {dest_dir}")
                try:
                    shutil.copytree(directory, dest_dir)
                except Exception as e:
                    self.logger.error(f"Error backing up {directory}: {e}")
        
        # Save metadata
        metadata = {
            "timestamp": timestamp,
            "day_number": day_number,
            "name": snapshot_name,
            "version": self.config.get("simulator.version", "4.0.0")
        }
        
        with open(os.path.join(snapshot_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f, indent=2)
        
        self.logger.info(f"Created snapshot: {snapshot_name}")
        return snapshot_dir
    
    def restore_snapshot(self, snapshot_name: str) -> Dict[str, Any]:
        """Restore from a snapshot
        
        Args:
            snapshot_name: Snapshot name or path
            
        Returns:
            dict: Snapshot metadata
        """
        # Handle full path or just name
        if os.path.dirname(snapshot_name):
            snapshot_dir = snapshot_name
        else:
            snapshot_dir = os.path.join(self.backup_dir, snapshot_name)
        
        if not os.path.exists(snapshot_dir):
            raise ValueError(f"Snapshot not found: {snapshot_name}")
        
        # Load metadata
        metadata_path = os.path.join(snapshot_dir, "metadata.json")
        if not os.path.exists(metadata_path):
            raise ValueError(f"Snapshot metadata not found: {metadata_path}")
            
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
        
        # Restore each directory
        for subdir in os.listdir(snapshot_dir):
            src_dir = os.path.join(snapshot_dir, subdir)
            
            if os.path.isdir(src_dir) and subdir != "metadata.json":
                # Determine destination path
                if subdir == "results":
                    dest_dir = self.config.get("paths.results_dir", "results")
                elif subdir == "pgn":
                    dest_dir = self.config.get("paths.pgn_dir", "results/pgn")
                elif subdir == "stats":
                    dest_dir = self.config.get("paths.stats_dir", "results/stats")
                else:
                    # Skip unknown directories
                    self.logger.warning(f"Skipping unknown directory: {subdir}")
                    continue
                
                # Backup current before replacing
                if os.path.exists(dest_dir):
                    backup = f"{dest_dir}_backup_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.logger.info(f"Backing up {dest_dir} to {backup}")
                    try:
                        shutil.move(dest_dir, backup)
                    except Exception as e:
                        self.logger.error(f"Error backing up {dest_dir}: {e}")
                
                # Restore from snapshot
                self.logger.info(f"Restoring {src_dir} to {dest_dir}")
                try:
                    shutil.copytree(src_dir, dest_dir)
                except Exception as e:
                    self.logger.error(f"Error restoring {src_dir}: {e}")
        
        self.logger.info(f"Restored from snapshot: {snapshot_name}")
        return metadata
    
    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all available snapshots
        
        Returns:
            list: Snapshot metadata
        """
        snapshots = []
        
        for item in os.listdir(self.backup_dir):
            item_path = os.path.join(self.backup_dir, item)
            metadata_path = os.path.join(item_path, "metadata.json")
            
            if os.path.isdir(item_path) and os.path.exists(metadata_path):
                try:
                    with open(metadata_path, "r") as f:
                        metadata = json.load(f)
                    
                    snapshots.append({
                        "name": item,
                        "path": item_path,
                        "metadata": metadata
                    })
                except Exception as e:
                    self.logger.error(f"Error reading snapshot metadata: {e}")
        
        return snapshots
    
    def delete_snapshot(self, snapshot_name: str) -> bool:
        """Delete a snapshot
        
        Args:
            snapshot_name: Snapshot name or path
            
        Returns:
            bool: Success status
        """
        # Handle full path or just name
        if os.path.dirname(snapshot_name):
            snapshot_dir = snapshot_name
        else:
            snapshot_dir = os.path.join(self.backup_dir, snapshot_name)
        
        if not os.path.exists(snapshot_dir):
            self.logger.error(f"Snapshot not found: {snapshot_name}")
            return False
        
        try:
            shutil.rmtree(snapshot_dir)
            self.logger.info(f"Deleted snapshot: {snapshot_name}")
            return True
        except Exception as e:
            self.logger.error(f"Error deleting snapshot: {e}")
            return False