"""
META Fantasy League Simulator - Configuration Manager
Centralized configuration management with validation
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Callable, List

class ConfigurationManager:
    """Enhanced configuration manager with validation"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager
        
        Args:
            config_file: Optional path to config file
        """
        self.config_data = {}
        self.schema = {}
        self.logger = logging.getLogger("system.config")
        
        # Load default configuration
        self._load_defaults()
        
        # Load from file if provided
        if config_file:
            self.load_from_file(config_file)
    
    def _load_defaults(self) -> None:
        """Load default configuration values"""
        self.logger.info("Loading default configuration")
        
        # Define default paths relative to this file
        base_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
        
        # Core configuration
        self.config_data = {
            "simulator": {
                "version": "4.0.0",
                "name": "META Fantasy League Simulator"
            },
            "simulation": {
                "max_moves": 30,              # Maximum chess moves per board
                "teams_per_match": 8,         # STRICT: exactly 8 players per team
                "matches_per_day": 5,         # STRICT: exactly 5 matches per day
                "max_convergences_per_char": 3,  # Maximum convergences per character
                "damage_scaling": 2.0,        # Base multiplier for damage 
                "base_damage_reduction": 35,  # Base damage reduction percentage
                "max_damage_reduction": 75,   # Maximum damage reduction percentage
                "hp_regen_rate": 3,          # HP regeneration per turn
                "stamina_regen_rate": 5,     # Stamina regeneration per turn
                "critical_threshold": 25,    # Threshold for critical hits
                "ko_threshold": 3,           # Number of KOs to trigger team loss
                "team_hp_threshold": 25      # Team HP percentage below this triggers loss
            },
            "paths": {
                "base_dir": base_dir,
                "data_dir": os.path.join(base_dir, "data"),
                "results_dir": os.path.join(base_dir, "results"),
                "pgn_dir": os.path.join(base_dir, "results", "pgn"),
                "reports_dir": os.path.join(base_dir, "results", "reports"),
                "stats_dir": os.path.join(base_dir, "results", "stats"),
                "logs_dir": os.path.join(base_dir, "logs"),
                "backups_dir": os.path.join(base_dir, "backups"),
                "config_dir": os.path.join(base_dir, "config"),
                "lineup_file": os.path.join(base_dir, "data", "lineups", "All Lineups 1.xlsx"),
                "team_ids_file": os.path.join(base_dir, "data", "teams", "SimEngine v3 teamIDs 1.csv"),
                "divisions_file": os.path.join(base_dir, "data", "teams", "SimEngine v3  Divisions.csv"),
                "trait_catalog": os.path.join(base_dir, "data", "traits", "SimEngine v2  full_trait_catalog_export.csv")
            },
            "date": {
                "day_one": "2025-04-07",  # First day is April 7, 2025 (Monday)
                "date_format": "%Y-%m-%d",
                "timestamp_format": "%Y%m%d_%H%M%S"
            },
            "logging": {
                "level": "INFO",
                "file_level": "DEBUG",
                "console_level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            },
            "features": {
                "use_stockfish": True,        # Use Stockfish for move selection
                "xp_enabled": True,           # Enable XP progression
                "synergy_enabled": True,      # Enable team synergies
                "injury_enabled": True,       # Enable injury system
                "morale_enabled": True,       # Enable morale system
                "stamina_enabled": True       # Enable stamina tracking
            },
            "divisions": {
                "undercurrent": "undercurrent",  # Division names
                "overlay": "overlay"
            }
        }
        
        # Define validation schema
        self.schema = {
            "simulation.teams_per_match": {
                "type": int,
                "validator": lambda x: x == 8,  # MUST be exactly 8
                "error": "Teams MUST have exactly 8 players"
            },
            "simulation.matches_per_day": {
                "type": int,
                "validator": lambda x: x == 5,  # MUST be exactly 5
                "error": "There MUST be exactly 5 matches per day"
            }
        }
    
    def load_from_file(self, config_file: str) -> bool:
        """Load configuration from JSON file
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            bool: Success status
        """
        if not os.path.exists(config_file):
            self.logger.error(f"Configuration file not found: {config_file}")
            return False
        
        try:
            with open(config_file, 'r') as f:
                data = json.load(f)
            
            # Update configuration with loaded values
            self._update_dict_recursive(self.config_data, data)
            
            self.logger.info(f"Configuration loaded from: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error loading configuration: {e}")
            return False
    
    def _update_dict_recursive(self, target: Dict, source: Dict) -> None:
        """Update dictionary recursively
        
        Args:
            target: Target dictionary
            source: Source dictionary
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively update nested dictionaries
                self._update_dict_recursive(target[key], value)
            else:
                # Set or override value
                target[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value with dot notation
        
        Args:
            key: Configuration key (e.g., "paths.data_dir")
            default: Default value if key not found
            
        Returns:
            Any: Configuration value
        """
        parts = key.split('.')
        value = self.config_data
        
        for part in parts:
            if not isinstance(value, dict) or part not in value:
                return default
            value = value[part]
            
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set a configuration value with validation
        
        Args:
            key: Configuration key (e.g., "paths.data_dir")
            value: Value to set
            
        Returns:
            bool: Success status
        """
        # Validate against schema if present
        if key in self.schema:
            schema_def = self.schema[key]
            
            # Type check
            if not isinstance(value, schema_def["type"]):
                self.logger.error(f"Invalid type for {key}: Expected {schema_def['type'].__name__}, got {type(value).__name__}")
                return False
                
            # Custom validation
            if "validator" in schema_def and not schema_def["validator"](value):
                self.logger.error(f"Invalid value for {key}: {schema_def['error']}")
                return False
        
        # Apply the value
        parts = key.split('.')
        target = self.config_data
        
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            elif not isinstance(target[part], dict):
                # Cannot set nested key on non-dict value
                self.logger.error(f"Cannot set nested key {key}: {part} is not a dictionary")
                return False
                
            target = target[part]
            
        target[parts[-1]] = value
        return True
    
    def save_to_file(self, config_file: str) -> bool:
        """Save configuration to JSON file
        
        Args:
            config_file: Path to save configuration
            
        Returns:
            bool: Success status
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            
            # Save configuration
            with open(config_file, 'w') as f:
                json.dump(self.config_data, f, indent=2)
            
            self.logger.info(f"Configuration saved to: {config_file}")
            return True
        except Exception as e:
            self.logger.error(f"Error saving configuration: {e}")
            return False
    
    def validate_all(self) -> List[str]:
        """Validate all configuration against schema
        
        Returns:
            list: Validation errors
        """
        errors = []
        
        for key, schema_def in self.schema.items():
            value = self.get(key)
            
            # Skip if key not set
            if value is None:
                continue
                
            # Type check
            if not isinstance(value, schema_def["type"]):
                errors.append(f"Invalid type for {key}: Expected {schema_def['type'].__name__}, got {type(value).__name__}")
                continue
                
            # Custom validation
            if "validator" in schema_def and not schema_def["validator"](value):
                errors.append(f"Invalid value for {key}: {schema_def['error']}")
        
        return errors
    
    def ensure_directories(self) -> None:
        """Ensure all required directories exist"""
        for key, path in self.config_data.get("paths", {}).items():
            if key.endswith('_dir') and not os.path.exists(path):
                self.logger.info(f"Creating directory: {path}")
                os.makedirs(path, exist_ok=True)