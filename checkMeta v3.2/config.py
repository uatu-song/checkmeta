"""
META Fantasy League Simulator - Configuration Module
Centralized configuration management for the simulator
"""

import os
import json
import datetime
from typing import Dict, Any, List, Optional

class Config:
    """
    Configuration manager for META Fantasy League Simulator
    Provides centralized access to all simulation parameters, file paths,
    and constants used throughout the system.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration with default values or from config file
        
        Args:
            config_file: Optional path to JSON configuration file
        """
        # Initialize with default values
        self._init_defaults()
        
        # Load from file if provided
        if config_file and os.path.exists(config_file):
            self.load_from_file(config_file)
            
        # Create required directories
        self._ensure_directories()
    
    def _init_defaults(self):
        """Initialize default configuration values"""
        # Simulation parameters
        self.simulation = {
            # Core simulation settings
            "max_moves": 30,               # Maximum moves per simulation
            "max_batch_size": 5,           # Maximum batch size for processing
            "max_convergences_per_char": 3,  # Maximum convergences per character
            
            # Battle parameters
            "damage_scaling": 2.0,         # Base multiplier for damage 
            "base_damage_reduction": 35,   # Base damage reduction percentage
            "max_damage_reduction": 75,    # Maximum damage reduction percentage
            "max_damage_per_hit": 30,      # Safety cap on damage per hit
            "hp_regen_rate": 3,            # HP regeneration per turn
            "stamina_regen_rate": 5,       # Stamina regeneration per turn
            "critical_threshold": 25,      # Threshold for critical hits
            
            # Team loss conditions
            "ko_threshold": 3,             # Number of KOs to trigger team loss
            "team_hp_threshold": 25,       # Team HP percentage below this triggers loss
            
            # Advanced features
            "enable_advanced_features": True,  # Enable advanced simulation features
            "use_stockfish": True,          # Use Stockfish for move selection if available
        }
        
        # File paths
        self.paths = {
            # Directory structure
            "results_dir": "results",
            "pgn_dir": "results/pgn",
            "reports_dir": "results/reports",
            "stats_dir": "results/stats",
            
            # External resources
            "stockfish_path": self._find_stockfish_path(),
            "default_lineup_file": "data/lineups/All Lineups 1.xlsx",
            "trait_catalog": "data/traits/SimEngine v2  full_trait_catalog_export.csv",
            "team_ids_file": "data/teams/SimEngine v3 teamIDs 1.csv",
            "divisions_file": "data/teams/SimEngine v3  Divisions.csv"
        }
        
        # Time and date settings
        today = datetime.datetime.now()
        self.date = {
            "current_day": 1,
            "current_week": 1,
            "current_date": today.strftime("%Y-%m-%d"),
            "date_format": "%Y-%m-%d",
            "timestamp_format": "%Y%m%d_%H%M%S"
        }
        
        # Team data
        self.teams = {
            # Team mappings
            "mappings": {
                "t001": "Xavier's School", 
                "t002": "Brotherhood", 
                "t003": "Avengers", 
                "t004": "Fantastic Four", 
                "t005": "Hellfire Club", 
                "t006": "Asgardians", 
                "t007": "Shield Ops", 
                "t008": "Mutant Underground", 
                "t009": "X-Force", 
                "t010": "The Illuminati"
            },
            
            # Matchday configurations
            "matchdays": {
                1: [
                    ("t001", "t002"),
                    ("t004", "t003"),
                    ("t005", "t006"),
                    ("t008", "t007"),
                    ("t009", "t010")
                ],
                2: [
                    ("t001", "t003"),
                    ("t004", "t006"),
                    ("t005", "t007"),
                    ("t008", "t010"),
                    ("t009", "t002")
                ],
                3: [
                    ("t001", "t006"),
                    ("t004", "t007"),
                    ("t005", "t010"),
                    ("t008", "t002"),
                    ("t009", "t003")
                ],
                4: [
                    ("t001", "t007"),
                    ("t004", "t010"),
                    ("t005", "t002"),
                    ("t008", "t003"),
                    ("t009", "t006")
                ],
                5: [
                    ("t001", "t010"),
                    ("t004", "t002"),
                    ("t005", "t003"),
                    ("t008", "t006"),
                    ("t009", "t007")
                ]
            }
        }
        
        # Chess-related parameters
        self.chess = {
            # Role-based openings
            "role_openings": {
                "FL": ["e4", "d4", "c4"],         # Field Leader
                "RG": ["Nf3", "g3", "b3"],        # Ranger
                "VG": ["e4 e5 Nf3", "d4 d5 c4"],  # Vanguard
                "EN": ["c4", "d4 d5", "e4 c5"],   # Enforcer
                "GO": ["g3", "b3", "c4"],         # Ghost Operative
                "PO": ["d4 Nf6", "e4 e6", "c4 c5"], # Psi Operative
                "SV": ["e4 e5 Nf3 Nc6", "d4 d5 c4 e6"] # Sovereign
            }
        }
        
        # Role and division mappings
        self.roles = {
            # Role mappings
            "mappings": {
                "FIELD LEADER": "FL",
                "VANGUARD": "VG",
                "ENFORCER": "EN",
                "RANGER": "RG",
                "GHOST OPERATIVE": "GO",
                "PSI OPERATIVE": "PO",
                "SOVEREIGN": "SV"
            },
            
            # Division mappings
            "divisions": {
                "operations": ["FL", "VG", "EN"],
                "intelligence": ["RG", "GO", "PO", "SV"]
            }
        }
        
        # Logging configuration
        self.logging = {
            "level": "INFO",
            "file": "results/simulation.log",
            "console": True,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    
    def _find_stockfish_path(self) -> Optional[str]:
        """Find Stockfish executable path"""
        common_paths = [
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "C:/Program Files/Stockfish/stockfish.exe",
            "stockfish"  # Relies on PATH environment variable
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
        return None
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.paths["results_dir"],
            self.paths["pgn_dir"],
            self.paths["reports_dir"],
            self.paths["stats_dir"]
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_timestamp(self) -> str:
        """Get current timestamp in configured format
        
        Returns:
            str: Formatted timestamp
        """
        return datetime.datetime.now().strftime(self.date["timestamp_format"])
    
    def get_date(self) -> str:
        """Get current date in configured format
        
        Returns:
            str: Formatted date
        """
        return datetime.datetime.now().strftime(self.date["date_format"])
    
    def get_team_name(self, team_id: str) -> str:
        """Get team name from team ID
        
        Args:
            team_id: Team ID
            
        Returns:
            str: Team name
        """
        # Normalize team ID
        team_id = team_id.lower()
        if not team_id.startswith('t'):
            team_id = 't' + team_id
            
        # Lookup team name
        return self.teams["mappings"].get(team_id, f"Team {team_id[1:]}")
    
    def get_matchups_for_day(self, day_number: int) -> List[tuple]:
        """Get matchups for a specific day
        
        Args:
            day_number: Day number
            
        Returns:
            List: Matchups as tuples of team IDs
        """
        return self.teams["matchdays"].get(day_number, [])
    
    def map_position_to_role(self, position: str) -> str:
        """Map position name to standardized role code
        
        Args:
            position: Position name or code
            
        Returns:
            str: Standardized role code
        """
        position = str(position).upper().strip()
        
        # Check for exact matches
        if position in self.roles["mappings"]:
            return self.roles["mappings"][position]
        
        # Check for partial matches
        for key, value in self.roles["mappings"].items():
            if key in position:
                return value
        
        # Check if already a valid role code
        valid_roles = list(self.roles["mappings"].values())
        if position in valid_roles:
            return position
        
        # Default to Field Leader
        return "FL"
    
    def get_division_from_role(self, role: str) -> str:
        """Map role to division
        
        Args:
            role: Role code
            
        Returns:
            str: Division code ('o' for operations, 'i' for intelligence)
        """
        if role in self.roles["divisions"]["operations"]:
            return "o"
        elif role in self.roles["divisions"]["intelligence"]:
            return "i"
        
        # Default to operations
        return "o"
    
    def load_from_file(self, config_file: str) -> bool:
        """Load configuration from JSON file
        
        Args:
            config_file: Path to JSON configuration file
            
        Returns:
            bool: Success status
        """
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                
            # Update configuration with loaded values
            # Note: This uses a shallow update - nested dicts require special handling
            for section, values in config_data.items():
                if section in self.__dict__ and isinstance(self.__dict__[section], dict):
                    self.__dict__[section].update(values)
                    
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def save_to_file(self, config_file: str) -> bool:
        """Save current configuration to JSON file
        
        Args:
            config_file: Path to save configuration
            
        Returns:
            bool: Success status
        """
        try:
            # Create config data dict from instance variables
            config_data = {
                "simulation": self.simulation,
                "paths": self.paths,
                "date": self.date,
                "teams": self.teams,
                "chess": self.chess,
                "roles": self.roles,
                "logging": self.logging
            }
            
            # Save to file with pretty formatting
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def update_section(self, section: str, values: Dict[str, Any]) -> bool:
        """Update a configuration section
        
        Args:
            section: Section name
            values: Dictionary of values to update
            
        Returns:
            bool: Success status
        """
        if section in self.__dict__ and isinstance(self.__dict__[section], dict):
            self.__dict__[section].update(values)
            return True
        
        return False
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get a configuration section
        
        Args:
            section: Section name
            
        Returns:
            dict: Section values
        """
        if section in self.__dict__ and isinstance(self.__dict__[section], dict):
            return self.__dict__[section]
        
        return {}

# Global configuration instance
CONFIG = Config()

# Function to get global configuration
def get_config() -> Config:
    """Get global configuration instance
    
    Returns:
        Config: Global configuration instance
    """
    return CONFIG