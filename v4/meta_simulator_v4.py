"""
META Fantasy League Simulator - Monolithic Implementation
A single-file implementation of the fantasy league simulator with all core features

This simulator implements:
- 8v8 team matchups (STRICTLY enforced)
- Division-based matchups (Undercurrent vs Overlay only)
- Alternating home/away every day (automatic flipping)
- Individual chess matches for each player (16 games per match)
- 5 matches per day, 5 days per week (Monday-Friday)
- Full PGN recording and tracking
- Match visualization and reporting
- Comprehensive stats tracking
- Fairness and parity assurance through randomized processing

Usage:
    python meta_simulator_monolith.py [--day DAY_NUMBER] [--lineup LINEUP_FILE]
"""

import os
import sys
import time
import json
import random
import datetime
import argparse
import csv
import io
import math
import logging
import chess
import chess.pgn
import chess.engine
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Union
from collections import defaultdict

#############################################################################
#                           LOGGER SETUP                                    #
#############################################################################

# Setup logging
log_dir = "logs"
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"meta_simulator_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("META_SIMULATOR")

#############################################################################
#                             CONFIGURATION                                 #
#############################################################################

class Config:
    """Configuration manager for simulator"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration with default values or from config file"""
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
            "max_moves": 30,               # Maximum chess moves per board
            "max_convergences_per_char": 3,  # Maximum convergences per character
            "damage_scaling": 2.0,         # Base multiplier for damage 
            "base_damage_reduction": 35,   # Base damage reduction percentage
            "max_damage_reduction": 75,    # Maximum damage reduction percentage
            "hp_regen_rate": 3,            # HP regeneration per turn
            "stamina_regen_rate": 5,       # Stamina regeneration per turn
            "critical_threshold": 25,      # Threshold for critical hits
            "ko_threshold": 3,             # Number of KOs to trigger team loss
            "team_hp_threshold": 25,       # Team HP percentage below this triggers loss
            "use_stockfish": True,         # Use Stockfish for move selection if available
            "teams_per_match": 8,          # STRICTLY 8 players per team
            "active_days": [0, 1, 2, 3, 4], # Mon-Fri (0-4)
            "matches_per_day": 5,          # STRICTLY 5 matches per day
        }
        
        # File paths
        self.paths = {
            "results_dir": "results",
            "pgn_dir": "results/pgn",
            "reports_dir": "results/reports",
            "stats_dir": "results/stats",
            "data_dir": "data",
            "lineups_file": "data/lineups/All Lineups 1.xlsx",
            "team_ids_file": "data/teams/SimEngine v3 teamIDs 1.csv",
            "divisions_file": "data/teams/SimEngine v3  Divisions.csv",
            "trait_catalog": "data/traits/SimEngine v2  full_trait_catalog_export.csv",
            "stockfish_path": self._find_stockfish_path(),
        }
        
        # Time and date settings
        self.date = {
            "day_one": datetime.datetime(2025, 4, 7),  # Day 1 is April 7, 2025 (Monday)
            "date_format": "%Y-%m-%d",
            "timestamp_format": "%Y%m%d_%H%M%S"
        }
        
        # Division settings
        self.divisions = {
            "undercurrent": "undercurrent",  # Division names
            "overlay": "overlay",
            "division_key": "division"       # Key in team data for division
        }
        
        # Role mappings
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
    
    def _find_stockfish_path(self) -> Optional[str]:
        """Find Stockfish executable path"""
        common_paths = [
            "/usr/local/bin/stockfish",
            "/usr/bin/stockfish",
            "C:/Program Files/Stockfish/stockfish.exe",
            "stockfish.exe",  # Local directory
            "stockfish"       # Relies on PATH environment variable
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
            self.paths["stats_dir"],
            "logs"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_date_for_day(self, day_number: int) -> str:
        """Get the date for a specific day number
        
        Args:
            day_number: Day number (1-indexed)
            
        Returns:
            str: Date string in configured format
        """
        if day_number < 1:
            logger.error(f"Invalid day number: {day_number}")
            raise ValueError(f"Day number must be at least 1, got {day_number}")
        
        # Calculate days since day one
        # Day 1 is April 7, 2025 (Monday)
        current_date = self.date["day_one"]
        
        # Calculate business days
        days_added = 0
        while days_added < day_number - 1:
            current_date += datetime.timedelta(days=1)
            # Skip weekends (5=Saturday, 6=Sunday)
            if current_date.weekday() < 5:
                days_added += 1
        
        return current_date.strftime(self.date["date_format"])
    
    def get_current_day(self) -> int:
        """Get the current day number based on today's date
        
        Returns:
            int: Current day number
        """
        today = datetime.datetime.now()
        day_one = self.date["day_one"]
        
        # Cannot be before day one
        if today < day_one:
            return 1
        
        # Calculate business days between
        business_days = 0
        current_date = day_one
        
        while current_date < today:
            current_date += datetime.timedelta(days=1)
            # Skip weekends (5=Saturday, 6=Sunday)
            if current_date.weekday() < 5:
                business_days += 1
        
        return business_days + 1
    
    def get_weekday_for_day(self, day_number: int) -> int:
        """Get the weekday for a specific day number
        
        Args:
            day_number: Day number (1-indexed)
            
        Returns:
            int: Weekday (0=Monday, 6=Sunday)
        """
        date_str = self.get_date_for_day(day_number)
        date_obj = datetime.datetime.strptime(date_str, self.date["date_format"])
        return date_obj.weekday()
    
    def is_valid_match_day(self, day_number: int) -> bool:
        """Check if a day number is a valid match day (Mon-Fri)
        
        Args:
            day_number: Day number (1-indexed)
            
        Returns:
            bool: True if valid match day
        """
        weekday = self.get_weekday_for_day(day_number)
        return weekday in self.simulation["active_days"]
    
    def get_excel_date_format(self, day_number: int) -> str:
        """Get date in format used in Excel sheets (M/D/YY)
        
        Args:
            day_number: Day number (1-indexed)
            
        Returns:
            str: Date string in Excel format
        """
        date_str = self.get_date_for_day(day_number)
        date_obj = datetime.datetime.strptime(date_str, self.date["date_format"])
        return date_obj.strftime("%-m/%-d/%y")  # Format: M/D/YY (no leading zeros)
    
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
                    
            logger.info(f"Configuration loaded from {config_file}")
            return True
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False

# Global configuration instance
CONFIG = Config()

#############################################################################
#                           SYSTEM VALIDATOR                                #
#############################################################################

class SystemValidator:
    """Validates system integrity before simulation"""
    
    @staticmethod
    def validate_all() -> bool:
        """Run all validation checks
        
        Returns:
            bool: True if all checks pass
        """
        checks = [
            SystemValidator.validate_directories,
            SystemValidator.validate_required_files,
            SystemValidator.validate_stockfish,
            SystemValidator.validate_division_data
        ]
        
        all_passed = True
        
        for check in checks:
            try:
                if not check():
                    all_passed = False
            except Exception as e:
                logger.error(f"Validation check {check.__name__} failed with error: {e}")
                all_passed = False
        
        return all_passed
    
    @staticmethod
    def validate_directories() -> bool:
        """Validate that all required directories exist
        
        Returns:
            bool: True if all directories exist
        """
        required_dirs = [
            CONFIG.paths["results_dir"],
            CONFIG.paths["pgn_dir"],
            CONFIG.paths["reports_dir"],
            CONFIG.paths["stats_dir"],
            CONFIG.paths["data_dir"]
        ]
        
        missing_dirs = [d for d in required_dirs if not os.path.exists(d)]
        
        if missing_dirs:
            logger.error(f"Missing required directories: {missing_dirs}")
            return False
        
        logger.info("Directory validation passed")
        return True
    
    @staticmethod
    def validate_required_files() -> bool:
        """Validate that all required files exist
        
        Returns:
            bool: True if all required files exist
        """
        required_files = [
            CONFIG.paths["lineups_file"],
            CONFIG.paths["team_ids_file"],
            CONFIG.paths["divisions_file"],
            CONFIG.paths["trait_catalog"]
        ]
        
        missing_files = [f for f in required_files if not os.path.exists(f)]
        
        if missing_files:
            logger.error(f"Missing required files: {missing_files}")
            return False
        
        logger.info("File validation passed")
        return True
    
    @staticmethod
    def validate_stockfish() -> bool:
        """Validate that Stockfish is available if enabled
        
        Returns:
            bool: True if Stockfish is available or not enabled
        """
        if not CONFIG.simulation["use_stockfish"]:
            logger.info("Stockfish validation skipped (not enabled)")
            return True
        
        stockfish_path = CONFIG.paths["stockfish_path"]
        
        if not stockfish_path or not os.path.exists(stockfish_path):
            logger.warning("Stockfish not found but enabled in config")
            return False
        
        # Try to initialize Stockfish (optional, can be removed if causes issues)
        try:
            engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
            engine.quit()  # Just testing, close it right away
            logger.info("Stockfish validation passed")
            return True
        except Exception as e:
            logger.error(f"Stockfish initialization failed: {e}")
            return False
    
    @staticmethod
    def validate_division_data() -> bool:
        """Validate that division data is available and correctly formatted
        
        Returns:
            bool: True if division data is valid
        """
        try:
            # Check if divisions file exists and is readable
            if not os.path.exists(CONFIG.paths["divisions_file"]):
                logger.error(f"Divisions file not found: {CONFIG.paths['divisions_file']}")
                return False
            
            # Try to read the file
            df = pd.read_csv(CONFIG.paths["divisions_file"])
            
            # Check if required columns exist
            required_cols = ["team_id", "division"]
            
            # Check if file has a header
            if df.shape[0] == 0:
                logger.error("Divisions file is empty")
                return False
                
            # Check column names (direct match or case-insensitive)
            found_cols = set()
            for col in required_cols:
                # Direct match
                if col in df.columns:
                    found_cols.add(col)
                    continue
                
                # Case-insensitive match
                matched = False
                for df_col in df.columns:
                    if col.lower() == df_col.lower():
                        found_cols.add(col)
                        matched = True
                        break
                
                if not matched:
                    logger.error(f"Required column not found in divisions file: {col}")
            
            if len(found_cols) != len(required_cols):
                logger.error(f"Missing required columns in divisions file")
                return False
            
            # Check that there are at least two divisions
            distinct_divisions = df["division"].unique()
            if len(distinct_divisions) < 2:
                logger.error(f"Not enough divisions found in file: {distinct_divisions}")
                return False
            
            logger.info("Division data validation passed")
            return True
                
        except Exception as e:
            logger.error(f"Error validating division data: {e}")
            return False

#############################################################################
#                           DATA LOADERS                                    #
#############################################################################

class DataLoader:
    """Handles loading and processing team and player data"""
    
    @staticmethod
    def load_team_ids() -> Dict[str, str]:
        """Load team IDs and names from CSV file
        
        Returns:
            dict: Mapping of team IDs to team names
        """
        team_ids_file = CONFIG.paths["team_ids_file"]
        
        if not os.path.exists(team_ids_file):
            logger.error(f"Team IDs file not found: {team_ids_file}")
            raise FileNotFoundError(f"Team IDs file not found: {team_ids_file}")
        
        try:
            df = pd.read_csv(team_ids_file)
            
            # Check if required columns exist
            id_column = None
            name_column = None
            
            # Try to find columns with team IDs and names
            for col in df.columns:
                if "team" in col.lower() and "id" in col.lower():
                    id_column = col
                elif "team" in col.lower() and "name" in col.lower():
                    name_column = col
            
            # Use first column as ID and second as name if not found
            if id_column is None and len(df.columns) > 0:
                id_column = df.columns[0]
            
            if name_column is None and len(df.columns) > 1:
                name_column = df.columns[1]
            
            if id_column is None or name_column is None:
                logger.error(f"Could not identify ID and name columns in team IDs file")
                raise ValueError(f"Could not identify ID and name columns in team IDs file")
            
            # Create mapping
            team_ids = {}
            for _, row in df.iterrows():
                team_id = str(row[id_column]).strip()
                team_name = str(row[name_column]).strip()
                
                # Normalize ID format
                team_id = DataLoader.normalize_team_id(team_id)
                
                team_ids[team_id] = team_name
            
            logger.info(f"Loaded {len(team_ids)} team IDs from {team_ids_file}")
            return team_ids
            
        except Exception as e:
            logger.error(f"Error loading team IDs: {e}")
            raise e
    
    @staticmethod
    def load_divisions() -> Dict[str, str]:
        """Load team divisions from CSV file
        
        Returns:
            dict: Mapping of team IDs to divisions
        """
        divisions_file = CONFIG.paths["divisions_file"]
        
        if not os.path.exists(divisions_file):
            logger.error(f"Divisions file not found: {divisions_file}")
            raise FileNotFoundError(f"Divisions file not found: {divisions_file}")
        
        try:
            df = pd.read_csv(divisions_file)
            
            # Check if required columns exist
            id_column = None
            division_column = None
            
            # Try to find columns with team IDs and divisions
            for col in df.columns:
                if "team" in col.lower() and "id" in col.lower():
                    id_column = col
                elif "division" in col.lower():
                    division_column = col
            
            # Use first column as ID and second as division if not found
            if id_column is None and len(df.columns) > 0:
                id_column = df.columns[0]
            
            if division_column is None and len(df.columns) > 1:
                division_column = df.columns[1]
            
            if id_column is None or division_column is None:
                logger.error(f"Could not identify ID and division columns in divisions file")
                raise ValueError(f"Could not identify ID and division columns in divisions file")
            
            # Create mapping
            divisions = {}
            for _, row in df.iterrows():
                team_id = str(row[id_column]).strip()
                division = str(row[division_column]).strip().lower()
                
                # Normalize ID format
                team_id = DataLoader.normalize_team_id(team_id)
                
                divisions[team_id] = division
            
            logger.info(f"Loaded {len(divisions)} team divisions from {divisions_file}")
            return divisions
            
        except Exception as e:
            logger.error(f"Error loading divisions: {e}")
            raise e
    
    @staticmethod
    def load_lineups_from_excel(day_number: int) -> Dict[str, List[Dict]]:
        """Load character lineups from Excel file for a specific day
        
        Args:
            day_number: Day number to load lineups for
            
        Returns:
            dict: Dictionary of team lineups by team ID
        """
        lineups_file = CONFIG.paths["lineups_file"]
        
        if not os.path.exists(lineups_file):
            logger.error(f"Lineups file not found: {lineups_file}")
            raise FileNotFoundError(f"Lineups file not found: {lineups_file}")
        
        try:
            # Get date in Excel format
            day_sheet = CONFIG.get_excel_date_format(day_number)
            logger.info(f"Loading lineups for day {day_number} (sheet: {day_sheet})")
            
            # Load Excel file
            xls = pd.ExcelFile(lineups_file)
            available_sheets = xls.sheet_names
            logger.debug(f"Available sheets in Excel file: {available_sheets}")
            
            # Try to find a matching sheet
            day_sheet_clean = day_sheet.replace('/', '')
            matching_sheets = [s for s in available_sheets if day_sheet_clean in s.replace('/', '').replace('-', '')]
            selected_sheet = None
            
            if day_sheet in available_sheets:
                selected_sheet = day_sheet
                logger.info(f"Found exact match for sheet: {day_sheet}")
            elif matching_sheets:
                selected_sheet = matching_sheets[0]
                logger.info(f"Found partial match for sheet: {selected_sheet}")
            else:
                # Fall back to first sheet
                selected_sheet = available_sheets[0]
                logger.warning(f"No matching sheet found. Using first sheet: {selected_sheet}")
            
            # Load the selected sheet
            df = pd.read_excel(lineups_file, sheet_name=selected_sheet)
            logger.debug(f"Columns in sheet: {df.columns.tolist()}")
            
            # Map column names based on what's available
            column_mapping = {
                'team_id': ['Team', 'team_id', 'team', 'team id', 'teamid', 'tid'],
                'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name'],
                'role': ['Position', 'PositionFull', 'role', 'position', 'char_role', 'character_role'],
                'active': ['Active', 'is_active', 'active', 'playing', 'is_playing']
            }
            
            # Create new columns with required names based on available columns
            required_columns = ['team_id', 'name', 'role', 'active']
            
            for required_col, possible_cols in column_mapping.items():
                found = False
                for col in possible_cols:
                    if col in df.columns:
                        logger.debug(f"Mapping '{col}' to '{required_col}'")
                        df[required_col] = df[col]
                        found = True
                        break
                
                if not found:
                    logger.warning(f"Could not find any column to map to '{required_col}'")
                    
                    # Set defaults for missing columns
                    if required_col == 'active':
                        df[required_col] = True  # Default to active if not specified
                    elif required_col == 'role':
                        df[required_col] = 'FL'  # Default to Field Leader if not specified
            
            # Organize by teams
            teams = {}
            valid_rows = 0
            
            for _, row in df.iterrows():
                # Skip completely empty rows
                if pd.isna(row.get('team_id', None)) and pd.isna(row.get('name', None)):
                    continue
                
                team_id = str(row.get('team_id', '')).strip()
                
                # Skip rows with empty team_id
                if not team_id or pd.isna(team_id):
                    continue
                
                # Clean team_id format if needed (some Excel exports add '.0')
                if team_id.endswith('.0'):
                    team_id = team_id[:-2]
                
                # Normalize team ID
                team_id = DataLoader.normalize_team_id(team_id)
                
                if team_id not in teams:
                    teams[team_id] = []
                
                # Get character name
                char_name = str(row.get('name', f"Character {len(teams[team_id])}")).strip()
                if not char_name or pd.isna(char_name):
                    char_name = f"Character {len(teams[team_id])}"
                
                # Get role
                role = str(row.get('role', 'FL')).strip()
                if not role or pd.isna(role):
                    role = 'FL'
                
                # Get active status
                is_active = True
                if 'active' in row:
                    active_val = row.get('active')
                    if not pd.isna(active_val):
                        # Convert various values to boolean
                        if isinstance(active_val, bool):
                            is_active = active_val
                        elif isinstance(active_val, (int, float)):
                            is_active = active_val > 0
                        elif isinstance(active_val, str):
                            is_active = active_val.lower() in ('true', 'yes', 'y', '1', 'active', 'playing')
                
                # Get team name (from Team column or construct from team_id)
                team_name = None
                if 'Team' in df.columns and not pd.isna(row.get('Team')):
                    team_name = f"Team {row.get('Team')}"
                else:
                    team_name = f"Team {team_id[1:]}"  # Remove 't' prefix for name
                
                # Create character dictionary
                role_standardized = DataLoader.map_position_to_role(role)
                division = DataLoader.get_division_from_role(role_standardized)
                
                character = {
                    'id': f"{team_id}_{len(teams[team_id])}",
                    'name': char_name,
                    'team_id': team_id,
                    'team_name': team_name,
                    'role': role_standardized,
                    'division': division,
                    'is_active': is_active,
                    'HP': 100,
                    'stamina': 100,
                    'life': 100,
                    'morale': 50,
                    'traits': [],
                    'rStats': {},
                    'xp_total': 0
                }
                
                # Add stats - use default values since these usually aren't in the Excel
                for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
                    character[f"a{stat}"] = 5
                
                # Try to get Rank as a value for stats
                if 'Rank' in df.columns and not pd.isna(row.get('Rank')):
                    try:
                        rank = int(row.get('Rank'))
                        # Scale rank to stats (assuming rank is 1-10)
                        stat_value = min(10, max(1, rank))
                        # Apply to key stats
                        character["aSTR"] = stat_value
                        character["aSPD"] = stat_value
                        character["aOP"] = stat_value
                    except:
                        pass
                
                # Add traits based on Primary Type
                if 'Primary Type' in df.columns and not pd.isna(row.get('Primary Type')):
                    primary_type = str(row.get('Primary Type')).lower()
                    
                    # Map primary types to traits
                    type_to_trait = {
                        'tech': ['genius', 'armor'],
                        'energy': ['genius', 'tactical'],
                        'cosmic': ['shield', 'healing'],
                        'mutant': ['agile', 'stretchy'],
                        'bio': ['agile', 'spider-sense'],
                        'mystic': ['tactical', 'healing'],
                        'skill': ['tactical', 'spider-sense']
                    }
                    
                    # Assign traits based on primary type
                    for type_key, traits in type_to_trait.items():
                        if type_key in primary_type:
                            character['traits'] = traits
                            break
                    
                    # Default traits if no match
                    if not character['traits']:
                        character['traits'] = ['genius', 'tactical']
                else:
                    # Default traits if no primary type
                    character['traits'] = ['genius', 'tactical']
                
                teams[team_id].append(character)
                valid_rows += 1
            
            logger.info(f"Loaded {valid_rows} characters across {len(teams)} teams")
            
            # If no valid teams loaded, return error
            if not teams:
                raise ValueError("No valid teams found in the Excel file")
            
            # Validate that each team has exactly 8 active players
            for team_id, chars in teams.items():
                active_chars = [c for c in chars if c.get('is_active', False)]
                if len(active_chars) != CONFIG.simulation["teams_per_match"]:
                    logger.warning(f"Team {team_id} has {len(active_chars)} active characters, expected {CONFIG.simulation['teams_per_match']}")
            
            return teams
        
        except Exception as e:
            logger.error(f"Error loading team data: {e}")
            raise e
    
    @staticmethod
    def get_matchups_for_day(day_number: int, team_divisions: Dict[str, str], teams: Dict[str, List[Dict]]) -> List[Tuple[str, str]]:
        """Get matchups for a specific day
        
        Args:
            day_number: Day number to get matchups for
            team_divisions: Mapping of team IDs to divisions
            teams: Dictionary of team lineups by team ID
            
        Returns:
            list: List of (team_a_id, team_b_id) matchup tuples
        """
        # Get valid team IDs with enough active players
        valid_teams = {}
        
        for team_id, characters in teams.items():
            active_chars = [c for c in characters if c.get('is_active', False)]
            if len(active_chars) >= CONFIG.simulation["teams_per_match"]:
                division = team_divisions.get(team_id)
                if division:
                    if division not in valid_teams:
                        valid_teams[division] = []
                    valid_teams[division].append(team_id)
        
        # Check if we have enough teams
        if len(valid_teams.keys()) < 2:
            logger.error(f"Not enough divisions with valid teams for matchups")
            raise ValueError(f"Not enough divisions with valid teams for matchups")
        
        # Get division names
        undercurrent = CONFIG.divisions["undercurrent"]
        overlay = CONFIG.divisions["overlay"]
        
        # Ensure both divisions have teams
        if undercurrent not in valid_teams:
            logger.error(f"No valid teams in {undercurrent} division")
            raise ValueError(f"No valid teams in {undercurrent} division")
        
        if overlay not in valid_teams:
            logger.error(f"No valid teams in {overlay} division")
            raise ValueError(f"No valid teams in {overlay} division")
        
        # Count teams in each division
        undercurrent_teams = valid_teams.get(undercurrent, [])
        overlay_teams = valid_teams.get(overlay, [])
        
        logger.info(f"Found {len(undercurrent_teams)} valid teams in {undercurrent} division")
        logger.info(f"Found {len(overlay_teams)} valid teams in {overlay} division")
        
        # Check if we have enough teams for 5 matches
        if len(undercurrent_teams) < CONFIG.simulation["matches_per_day"] or len(overlay_teams) < CONFIG.simulation["matches_per_day"]:
            logger.error(f"Not enough teams for {CONFIG.simulation['matches_per_day']} matches")
            raise ValueError(f"Not enough teams for {CONFIG.simulation['matches_per_day']} matches")
        
        # Create matchups
        matchups = []
        
        # Shuffle teams to randomize matchups
        random.shuffle(undercurrent_teams)
        random.shuffle(overlay_teams)
        
        # Determine home side based on day number
        # Even days: undercurrent is home (team_a), odd days: overlay is home (team_a)
        if day_number % 2 == 0:
            # Even day: undercurrent is home (team_a)
            for i in range(CONFIG.simulation["matches_per_day"]):
                if i < len(undercurrent_teams) and i < len(overlay_teams):
                    matchups.append((undercurrent_teams[i], overlay_teams[i]))
        else:
            # Odd day: overlay is home (team_a)
            for i in range(CONFIG.simulation["matches_per_day"]):
                if i < len(undercurrent_teams) and i < len(overlay_teams):
                    matchups.append((overlay_teams[i], undercurrent_teams[i]))
        
        logger.info(f"Created {len(matchups)} matchups for day {day_number}")
        return matchups
    
    @staticmethod
    def normalize_team_id(team_id: str) -> str:
        """Normalize team ID format
        
        Args:
            team_id: Team ID in any format
            
        Returns:
            str: Normalized team ID
        """
        # Handle None or empty string
        if not team_id:
            return ""
            
        # Convert to string if not already
        team_id = str(team_id)
        
        # Remove any non-alphanumeric characters
        team_id = ''.join(c for c in team_id if c.isalnum())
        
        # Ensure it starts with 't' (lowercase)
        if not team_id.lower().startswith('t'):
            team_id = 't' + team_id
        
        # Lowercase the entire ID for consistent comparison
        return team_id.lower()
    
    @staticmethod
    def map_position_to_role(position: str) -> str:
        """Map position name to standardized role code
        
        Args:
            position: Position name or code
            
        Returns:
            str: Standardized role code
        """
        position = str(position).upper().strip()
        
        # Standard position mappings
        position_map = CONFIG.roles["mappings"]
        
        # Check for exact matches
        if position in position_map:
            return position_map[position]
        
        # Check for partial matches
        for key, value in position_map.items():
            if key in position:
                return value
        
        # Check if already a valid role code
        valid_roles = list(position_map.values())
        if position in valid_roles:
            return position
        
        # Default
        return "FL"
    
    @staticmethod
    def get_division_from_role(role: str) -> str:
        """Map role to division (operations or intelligence)
        
        Args:
            role: Role code
            
        Returns:
            str: Division code ('o' for operations, 'i' for intelligence)
        """
        operations_roles = CONFIG.roles["divisions"]["operations"]
        intelligence_roles = CONFIG.roles["divisions"]["intelligence"]
        
        if role in operations_roles:
            return "o"
        elif role in intelligence_roles:
            return "i"
        else:
            return "o"  # Default to operations

#############################################################################
#                        CHESS & COMBAT SYSTEMS                             #
#############################################################################

class ChessSystem:
    """Handles chess game simulation and move selection"""
    
    def __init__(self, stockfish_path: Optional[str] = None):
        """Initialize the chess system
        
        Args:
            stockfish_path: Path to Stockfish executable
        """
        self.stockfish_path = stockfish_path
        self.stockfish_available = False
        
        # Try to activate Stockfish
        if stockfish_path and os.path.exists(stockfish_path):
            try:
                import chess.engine
                engine = chess.engine.SimpleEngine.popen_uci(stockfish_path)
                engine.quit()  # Just testing, close it right away
                self.stockfish_available = True
                logger.info(f"Stockfish activated at {stockfish_path}")
            except Exception as e:
                logger.warning(f"Stockfish initialization failed: {e}")
    
    def create_board(self) -> chess.Board:
        """Create a new chess board
        
        Returns:
            chess.Board: New chess board
        """
        return chess.Board()
    
    def select_move(self, board: chess.Board, character: Dict[str, Any]) -> Optional[chess.Move]:
        """Select a move for a character
        
        Args:
            board: Chess board
            character: Character making the move
            
        Returns:
            chess.Move: Selected chess move
        """
        if not self.stockfish_available:
            # Fall back to random move selection
            return self._select_move_random(board)
        
        try:
            # Determine analysis depth based on character attributes
            base_depth = min(max(2, character.get("aFS", 5) // 2), 10)
            
            # Adjust depth based on stamina (lower stamina = lower depth)
            stamina_factor = max(0.5, character.get("stamina", 100) / 100)
            adjusted_depth = max(1, int(base_depth * stamina_factor))
            
            # Initialize Stockfish engine
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                # Set thinking time based on character's Focus/Speed
                thinking_ms = character.get("aFS", 5) * 50
                
                # Set limit object
                limit = chess.engine.Limit(depth=adjusted_depth, time=thinking_ms/1000.0)
                
                # Get trait-influenced decision quality
                decision_quality = self._calculate_decision_quality(character)
                
                # Select move based on decision quality
                if decision_quality > 0.9:  # Excellent move
                    # Get best move directly
                    result = engine.play(board, limit)
                    return result.move
                elif decision_quality > 0.7:  # Good move
                    # Get top 3 moves and pick randomly
                    analysis = engine.analyse(board, limit, multipv=3)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                elif decision_quality > 0.4:  # Average move
                    # Get top 5 moves and pick randomly
                    analysis = engine.analyse(board, limit, multipv=5)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                else:  # Below average move
                    # Pick a random legal move with some bias towards non-terrible moves
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        # Try to avoid obvious blunders
                        if random.random() > 0.3:  # 70% chance to avoid obvious blunders
                            info = engine.analyse(board, chess.engine.Limit(depth=1))
                            if "pv" in info and info["pv"]:
                                safe_move = info["pv"][0]
                                return safe_move
                        
                        return random.choice(legal_moves)
        except Exception as e:
            logger.error(f"Error selecting move with Stockfish: {e}")
            # Fall back to random move selection
            return self._select_move_random(board)
        
        # Final fallback
        return self._select_move_random(board)
    
    def _select_move_random(self, board: chess.Board) -> Optional[chess.Move]:
        """Select a random legal move as fallback
        
        Args:
            board: Chess board
            
        Returns:
            chess.Move: Selected chess move
        """
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None
    
    def _calculate_decision_quality(self, character: Dict[str, Any]) -> float:
        """Calculate decision quality based on character attributes and state
        
        Args:
            character: Character making the decision
            
        Returns:
            float: Decision quality (0-1)
        """
        # Base quality on Focus/Speed and Willpower
        base_quality = (character.get("aFS", 5) + character.get("aWIL", 5)) / 20.0
        
        # Apply stamina factor
        stamina = character.get("stamina", 100)
        stamina_factor = max(0.6, stamina / 100)  # 60% minimum
        
        # Apply morale factor
        morale = character.get("morale", 50)
        morale_factor = 0.8 + (morale / 250)  # 0.8-1.2 range
        
        # Apply role bonuses
        role_factor = 1.0
        role = character.get("role", "")
        if role == "FL":  # Field Leader
            role_factor = 1.1  # 10% bonus
        elif role == "SV":  # Sovereign
            role_factor = 1.15  # 15% bonus
        
        # Combine factors
        quality = base_quality * stamina_factor * morale_factor * role_factor
        
        # Clamp to valid range
        return max(0.1, min(quality, 0.99))
    
    def simulate_chess_match(self, character: Dict[str, Any], max_moves: int = 30) -> Tuple[chess.Board, str]:
        """Simulate a chess match for a character
        
        Args:
            character: Character playing chess
            max_moves: Maximum number of moves
            
        Returns:
            tuple: (chess board, result)
        """
        board = self.create_board()
        move_count = 0
        result = "unknown"
        
        # Run until game is over or max moves reached
        while not board.is_game_over() and move_count < max_moves:
            try:
                # White's move (our character)
                if board.turn == chess.WHITE:
                    move = self.select_move(board, character)
                    if move is None:
                        logger.warning(f"No move found for {character['name']}")
                        break
                    board.push(move)
                # Black's move (opponent)
                else:
                    # Use random move for simplicity
                    move = self._select_move_random(board)
                    if move is None:
                        logger.warning(f"No move found for opponent")
                        break
                    board.push(move)
                
                move_count += 1
                
                # Update character stats based on move
                if move_count % 5 == 0:
                    # Every 5 moves, apply stamina cost
                    stamina_cost = 1.0
                    character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
                
            except Exception as e:
                logger.error(f"Error during chess simulation: {e}")
                break
        
        # Determine result
        if board.is_checkmate():
            if board.turn == chess.BLACK:  # White won (our character)
                result = "win"
            else:  # Black won (opponent)
                result = "loss"
        elif board.is_stalemate() or board.is_insufficient_material():
            result = "draw"
        
        # Record result in character
        character["result"] = result
        
        return board, result

class CombatSystem:
    """Handles combat mechanics, damage calculation, and move selection"""
    
    def __init__(self, trait_system=None):
        """Initialize the combat system
        
        Args:
            trait_system: Optional trait system for trait activations
        """
        self.trait_system = trait_system
        
        # Balance constants
        self.BASE_DAMAGE_REDUCTION = CONFIG.simulation["base_damage_reduction"]
        self.MAX_DAMAGE_REDUCTION = CONFIG.simulation["max_damage_reduction"]
        self.DAMAGE_SCALING = CONFIG.simulation["damage_scaling"]
        self.HP_REGEN_BASE = CONFIG.simulation["hp_regen_rate"]
        self.STAMINA_REGEN_BASE = CONFIG.simulation["stamina_regen_rate"]
    
    def update_character_metrics(self, character: Dict[str, Any], material_change: float, show_details: bool = False) -> None:
        """Update character metrics based on material change
        
        Args:
            character: Character to update
            material_change: Chess material change
            show_details: Whether to show detailed output
        """
        # Material loss = damage
        if material_change < 0:
            # Calculate damage from material loss
            damage = abs(material_change) * self.DAMAGE_SCALING
            
            # Calculate damage reduction from DUR/RES stats
            reduction = 0
            
            # Durability gives damage reduction
            dur_bonus = (character.get("aDUR", 5) - 5) * 3  # 3% per point above 5
            reduction += dur_bonus
            
            # Resilience gives damage reduction
            res_bonus = (character.get("aRES", 5) - 5) * 2  # 2% per point above 5
            reduction += res_bonus
            
            # Apply damage reduction from traits
            trait_reduction = 0
            if self.trait_system:
                context = {"damage": damage, "source": "material_loss"}
                trait_effects = self.trait_system.apply_trait_effect(
                    character, "damage_taken", context
                )
                
                for effect in trait_effects:
                    if effect.get("effect") == "damage_reduction":
                        trait_reduction += effect.get("value", 0)
            
            # Apply total damage reduction
            total_reduction = self.BASE_DAMAGE_REDUCTION + reduction + trait_reduction
            total_reduction = min(total_reduction, self.MAX_DAMAGE_REDUCTION)  # Cap at max
            
            reduced_damage = max(1, damage * (1 - total_reduction/100.0))
            
            # Apply damage to character
            self.apply_damage(character, reduced_damage)
            
            # Update rStats for damage sustained
            character.setdefault("rStats", {})
            character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + reduced_damage
            
            if character.get("division") == "o":
                character["rStats"]["rDSo"] = character["rStats"].get("rDSo", 0) + reduced_damage
            else:
                character["rStats"]["rDSi"] = character["rStats"].get("rDSi", 0) + reduced_damage
            
            if show_details:
                logger.debug(f"  {character['name']} took {reduced_damage:.1f} damage")
                logger.debug(f"  {character['name']} HP: {character['HP']:.1f}, Stamina: {character['stamina']:.1f}")
        
        # Material gain = damage dealt to opponent
        elif material_change > 0:
            # Calculate damage dealt
            damage_dealt = material_change * self.DAMAGE_SCALING
            
            # Update rStats for damage dealt
            character.setdefault("rStats", {})
            character["rStats"]["rDD"] = character["rStats"].get("rDD", 0) + damage_dealt
            
            if character.get("division") == "o":
                character["rStats"]["rDDo"] = character["rStats"].get("rDDo", 0) + damage_dealt
            else:
                character["rStats"]["rDDi"] = character["rStats"].get("rDDi", 0) + damage_dealt
                
            # If material gain is significant, record special stat
            if material_change >= 4:
                if character.get("division") == "i":
                    character["rStats"]["rMBi"] = character["rStats"].get("rMBi", 0) + 1
                else:
                    character["rStats"]["rCVo"] = character["rStats"].get("rCVo", 0) + 1
        
        # Apply stamina cost for moving
        stamina_cost = 1.0
        
        # Apply WIL bonus to reduce stamina cost
        wil_bonus = (character.get("aWIL", 5) - 5) * 0.08  # 8% reduction per point above 5
        stamina_cost *= max(0.3, 1 - wil_bonus)  # Cap at 70% reduction
        
        character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
    
    def apply_damage(self, character: Dict[str, Any], damage: float, source_character: Optional[Dict[str, Any]] = None, 
                   damage_reduction: float = 0, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Apply damage to a character
        
        Args:
            character: Character taking damage
            damage: Amount of damage
            source_character: Character dealing damage (optional)
            damage_reduction: Additional damage reduction percentage (0-100)
            context: Additional context for damage application
            
        Returns:
            Dict: Damage application results
        """
        context = context or {}
        damage = float(damage)  # Ensure damage is a float for calculations
        
        # Apply to HP first with improved reduction
        current_hp = character.get("HP", 100)
        
        # Calculate base reduction
        base_reduction = self.BASE_DAMAGE_REDUCTION + damage_reduction
        
        # Additional reduction from character attributes
        attr_reduction = 0
        dur_value = character.get("aDUR", 5)
        res_value = character.get("aRES", 5)
        
        if dur_value > 5:
            attr_reduction += (dur_value - 5) * 3  # 3% per point above 5
        
        if res_value > 5:
            attr_reduction += (res_value - 5) * 2  # 2% per point above 5
        
        # Total reduction (capped at maximum)
        total_reduction = min(self.MAX_DAMAGE_REDUCTION, base_reduction + attr_reduction)
        
        # Apply reduction
        reduced_damage = max(1, damage * (1 - total_reduction/100.0))
        
        # Apply to HP
        new_hp = max(0, current_hp - reduced_damage)
        character["HP"] = new_hp
        
        # Update damage stats in rStats
        character.setdefault("rStats", {})
        character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + reduced_damage
        
        # Track damage by source character for assists
        if source_character and context.get("damage_contributors"):
            char_id = character.get("id", "unknown")
            source_id = source_character.get("id", "unknown")
            
            if char_id not in context["damage_contributors"]:
                context["damage_contributors"][char_id] = []
                
            if source_id not in context["damage_contributors"][char_id]:
                context["damage_contributors"][char_id].append(source_id)
        
        # Overflow to stamina if HP is depleted, but at reduced rate
        stamina_damage = 0
        if new_hp == 0:
            # Reduce stamina damage rate for better survivability
            stamina_damage = (reduced_damage - current_hp) * 0.4  # Only 40% overflow to stamina
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Overflow to life with higher threshold
            if new_stamina == 0:
                life_threshold = 100
                if stamina_damage > current_stamina + life_threshold:
                    life_damage = 0.5  # Fractional life loss
                    character["life"] = max(0, character.get("life", 100) - life_damage)
                    
                    # Record life lost rStat
                    character["rStats"]["rLLS"] = character["rStats"].get("rLLS", 0) + 1
                    
                # Mark character as KO'd
                character["is_ko"] = True
                
                # Record KO in rStats if KO'd for first time this match
                if character.get("first_ko", True):
                    character["first_ko"] = False
                    
                    if character.get("division") == "o":
                        character["rStats"]["rKNBo"] = character["rStats"].get("rKNBo", 0) + 1
                    
                    # Record opponent takedown for source character
                    if source_character:
                        source_character.setdefault("rStats", {})
                        source_character["rStats"]["rOTD"] = source_character["rStats"].get("rOTD", 0) + 1
        
        return {
            "original_damage": damage,
            "reduced_damage": reduced_damage,
            "new_hp": new_hp,
            "stamina_damage": stamina_damage,
            "is_ko": character.get("is_ko", False),
            "is_dead": character.get("is_dead", False)
        }
    
    def apply_end_of_round_effects(self, characters: List[Dict[str, Any]], context: Dict[str, Any], show_details: bool = True) -> None:
        """Apply end-of-round effects
        
        Args:
            characters: List of characters
            context: Match context
            show_details: Whether to show detailed output
        """
        for character in characters:
            # Skip dead characters
            if character.get("is_dead", False):
                continue
                    
            # Base HP regeneration
            base_hp_regen = self.HP_REGEN_BASE
            
            # Regeneration effects from traits
            trait_heal_amount = 0
            if self.trait_system:
                trait_effects = self.trait_system.apply_trait_effect(character, "end_of_turn", {})
                
                for effect in trait_effects:
                    if effect.get("effect") == "healing":
                        # Moderate healing trait effectiveness
                        trait_heal_amount = effect.get("value", 0) * 2  # 2x healing effect
                        context["trait_logs"].append({
                            "round": context["round"],
                            "character": character["name"],
                            "trait": effect.get("trait_name", "Unknown"),
                            "effect": f"Healing +{trait_heal_amount}"
                        })
            
            # Apply total healing
            total_heal = base_hp_regen + trait_heal_amount
            
            # Only heal if not at full HP
            if character.get("HP", 100) < 100:
                old_hp = character.get("HP", 0)
                character["HP"] = min(100, old_hp + total_heal)
                
                # Record healing in rStats
                if trait_heal_amount > 0:
                    character.setdefault("rStats", {})
                    character["rStats"]["rHLG"] = character["rStats"].get("rHLG", 0) + trait_heal_amount
            
            # Apply stamina regeneration
            base_stamina_regen = self.STAMINA_REGEN_BASE
            
            # Apply WIL bonus to stamina regen
            wil_bonus = max(0, character.get("aWIL", 5) - 5)
            wil_regen = wil_bonus * 0.8  # 0.8 per point above 5
            
            regen_rate = base_stamina_regen + wil_regen
            
            # Faster recovery from knockdown
            if character.get("is_ko", False):
                # KO'd characters recover faster
                regen_rate *= 3
                
                # Chance to recover from KO based on stamina
                stamina = character.get("stamina", 0)
                if stamina > 20:
                    # Increased recovery chance
                    recovery_chance = stamina / 150  # 13-66% chance based on stamina
                    
                    # Apply WIL bonus to recovery chance
                    wil_factor = character.get("aWIL", 5) / 5.0
                    recovery_chance *= wil_factor
                    
                    if random.random() < recovery_chance:
                        character["is_ko"] = False
                        character["HP"] = max(20, character.get("HP", 0))  # Ensure at least 20 HP
                        
                        # Record recovery in rStats
                        character.setdefault("rStats", {})
                        character["rStats"]["rEVS"] = character["rStats"].get("rEVS", 0) + 1
                        
                        if show_details:
                            logger.info(f"  {character['name']} has recovered from knockout!")
            
            character["stamina"] = min(100, character.get("stamina", 0) + regen_rate)
            
            if show_details and (total_heal > 0 or regen_rate > 0):
                logger.debug(f"  {character['name']} recovered HP: +{total_heal:.1f}, Stamina: +{regen_rate:.1f}")

#############################################################################
#                         TRAIT SYSTEM                                      #
#############################################################################

#############################################################################
#                       CONVERGENCE SYSTEM                                 #
#############################################################################

class ConvergenceSystem:
    """Handles detection and resolution of convergences between chess boards"""
    
    def __init__(self, trait_system=None):
        """Initialize the convergence system
        
        Args:
            trait_system: Optional TraitSystem for trait activations
        """
        self.trait_system = trait_system
        
        # Balance constants
        self.BASE_DAMAGE_REDUCTION = CONFIG.simulation["base_damage_reduction"]
        self.MAX_DAMAGE_REDUCTION = CONFIG.simulation["max_damage_reduction"]
        self.DAMAGE_SCALING = CONFIG.simulation["damage_scaling"]
        self.CRITICAL_THRESHOLD = CONFIG.simulation["critical_threshold"]
    
    def process_convergences(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board], 
                            team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board], 
                            context: Dict[str, Any], max_per_char: int, show_details: bool = True) -> List[Dict[str, Any]]:
        """Process convergences between boards with improved balance and randomized order
        
        Args:
            team_a: Team A characters
            team_a_boards: Team A chess boards
            team_b: Team B characters
            team_b_boards: Team B chess boards
            context: Match context
            max_per_char: Maximum convergences per character
            show_details: Whether to show detailed output
            
        Returns:
            List: Processed convergences
        """
        # Randomize team processing order for fairness
        first_team, first_boards, first_id, second_team, second_boards, second_id = self._randomize_team_order(
            team_a, team_a_boards, "A", team_b, team_b_boards, "B"
        )
        
        convergences = []
        
        # Limit the number of convergences per round to prevent overwhelming damage
        max_convergences = 30  # Maximum total convergences per round
        convergence_count = 0
        char_convergence_counts = {char["id"]: 0 for char in first_team + second_team}
        
        # First collect all possible convergences
        possible_convergences = []
        
        # Check for non-pawn pieces occupying the same square across different boards
        for a_idx, (a_char, a_board) in enumerate(zip(first_team, first_boards)):
            # Skip if character is KO'd or dead
            if a_char.get("is_ko", False) or a_char.get("is_dead", False):
                continue
                
            # Skip if character has reached max convergences
            if char_convergence_counts[a_char["id"]] >= max_per_char:
                continue
                
            for b_idx, (b_char, b_board) in enumerate(zip(second_team, second_boards)):
                # Skip if character is KO'd or dead
                if b_char.get("is_ko", False) or b_char.get("is_dead", False):
                    continue
                
                # Skip if character has reached max convergences
                if char_convergence_counts[b_char["id"]] >= max_per_char:
                    continue
                
                # Find overlapping positions with non-pawn pieces
                for square in chess.SQUARES:
                    a_piece = a_board.piece_at(square)
                    b_piece = b_board.piece_at(square)
                    
                    if (a_piece and b_piece and 
                        a_piece.piece_type != chess.PAWN and 
                        b_piece.piece_type != chess.PAWN):
                        
                        # Calculate combat rolls
                        a_roll = self._calculate_combat_roll(a_char, b_char)
                        b_roll = self._calculate_combat_roll(b_char, a_char)
                        
                        # Apply trait effects for convergence
                        if self.trait_system:
                            # Create context for trait activation
                            a_context = {"opponent": b_char, "square": square, "roll": a_roll}
                            a_effects = self.trait_system.apply_trait_effect(a_char, "convergence", a_context)
                            
                            for effect in a_effects:
                                if effect.get("effect") == "combat_bonus":
                                    a_roll += effect.get("value", 0)
                                    context["trait_logs"].append({
                                        "round": context.get("round", 1),
                                        "character": a_char["name"],
                                        "trait": effect.get("trait_name", "Unknown Trait"),
                                        "effect": f"Added {effect.get('value', 0)} to combat roll"
                                    })
                            
                            # Same for B character
                            b_context = {"opponent": a_char, "square": square, "roll": b_roll}
                            b_effects = self.trait_system.apply_trait_effect(b_char, "convergence", b_context)
                            
                            for effect in b_effects:
                                if effect.get("effect") == "combat_bonus":
                                    b_roll += effect.get("value", 0)
                                    context["trait_logs"].append({
                                        "round": context.get("round", 1),
                                        "character": b_char["name"],
                                        "trait": effect.get("trait_name", "Unknown Trait"),
                                        "effect": f"Added {effect.get('value', 0)} to combat roll"
                                    })
                        
                        # Calculate priority (higher difference = more important convergence)
                        priority = abs(a_roll - b_roll)
                        
                        # Map original team indices
                        original_a_idx = a_idx if first_id == "A" else b_idx
                        original_b_idx = b_idx if first_id == "A" else a_idx
                        
                        # Store as possible convergence
                        possible_convergences.append({
                            "a_char": a_char,
                            "b_char": b_char,
                            "a_idx": original_a_idx,
                            "b_idx": original_b_idx,
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "square": square,
                            "priority": priority
                        })
        
        # Sort by priority (highest first) and take only max_convergences
        possible_convergences.sort(key=lambda x: x["priority"], reverse=True)
        selected_convergences = possible_convergences[:max_convergences]
        
        # Now process the selected convergences
        for conv in selected_convergences:
            a_char = conv["a_char"]
            b_char = conv["b_char"]
            a_roll = conv["a_roll"]
            b_roll = conv["b_roll"]
            square = conv["square"]
            
            # Skip if either character has reached max convergences
            if char_convergence_counts[a_char["id"]] >= max_per_char or char_convergence_counts[b_char["id"]] >= max_per_char:
                continue
            
            # Determine winner and loser
            if a_roll > b_roll:
                winner = a_char
                loser = b_char
                winner_roll = a_roll
                loser_roll = b_roll
            else:
                winner = b_char
                loser = a_char
                winner_roll = b_roll
                loser_roll = a_roll
            
            # Calculate convergence outcome
            roll_diff = winner_roll - loser_roll
            outcome = "success"
            
            if roll_diff > self.CRITICAL_THRESHOLD:
                outcome = "critical_success"
            
            # Calculate damage with diminishing returns
            # Use a logarithmic scale to reduce extreme differences
            base_damage = max(1, int(self.DAMAGE_SCALING * math.log(1 + roll_diff/10)))
            
            # Apply damage reduction (for defense traits, etc.)
            damage_reduction = 0
            if self.trait_system:
                damage_context = {"damage": base_damage, "source": winner}
                reduction_effects = self.trait_system.apply_trait_effect(loser, "damage_reduction", damage_context)
                
                for effect in reduction_effects:
                    if effect.get("effect") == "damage_reduction":
                        damage_reduction += effect.get("value", 0)
                        context["trait_logs"].append({
                            "round": context.get("round", 1),
                            "character": loser["name"],
                            "trait": effect.get("trait_name", "Unknown Trait"),
                            "effect": f"Reduced damage by {effect.get('value', 0)}%"
                        })
            
            # Calculate final damage with reduction
            total_reduction = min(self.MAX_DAMAGE_REDUCTION, self.BASE_DAMAGE_REDUCTION + damage_reduction)
            reduced_damage = max(1, base_damage * (1 - total_reduction/100.0))
            
            # Apply damage to loser
            self._apply_damage(loser, reduced_damage, winner, context)
            
            # Record convergence
            convergence_data = {
                "square": chess.square_name(square),
                "a_character": a_char["name"],
                "b_character": b_char["name"],
                "a_roll": a_roll,
                "b_roll": b_roll,
                "winner": winner["name"],
                "loser": loser["name"],
                "damage": base_damage,
                "reduced_damage": reduced_damage,
                "outcome": outcome
            }
            
            convergences.append(convergence_data)
            context["convergence_logs"].append(convergence_data)
            
            # Update rStats for winner and loser
            winner.setdefault("rStats", {})
            loser.setdefault("rStats", {})
            
            # Record convergence win
            if winner.get("division") == "o":
                winner["rStats"]["rCVo"] = winner["rStats"].get("rCVo", 0) + 1
            else:
                winner["rStats"]["rMBi"] = winner["rStats"].get("rMBi", 0) + 1
            
            # Record ultimate move for critical success
            if outcome == "critical_success":
                winner["rStats"]["rULT"] = winner["rStats"].get("rULT", 0) + 1
            
            # Update convergence counts
            char_convergence_counts[a_char["id"]] += 1
            char_convergence_counts[b_char["id"]] += 1
            convergence_count += 1
            
            if show_details:
                logger.info(f"CONVERGENCE: {a_char['name']} ({a_roll}) vs {b_char['name']} ({b_roll}) at {chess.square_name(square)}")
                logger.info(f"  {winner['name']} wins! {loser['name']} takes {reduced_damage:.1f} damage")
                if outcome == "critical_success":
                    logger.info(f"  CRITICAL SUCCESS! {winner['name']} recorded an Ultimate Move")
        
        return convergences
    
    def _randomize_team_order(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board], team_a_id: str,
                             team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board], team_b_id: str) -> Tuple:
        """Randomize team processing order for fairness
        
        Args:
            team_a: Team A characters
            team_a_boards: Team A chess boards
            team_a_id: Team A identifier
            team_b: Team B characters
            team_b_boards: Team B chess boards
            team_b_id: Team B identifier
            
        Returns:
            tuple: (first_team, first_boards, first_id, second_team, second_boards, second_id)
        """
        # Randomize order (coin flip)
        if random.random() < 0.5:
            return team_a, team_a_boards, team_a_id, team_b, team_b_boards, team_b_id
        else:
            return team_b, team_b_boards, team_b_id, team_a, team_a_boards, team_a_id
    
    def _calculate_combat_roll(self, attacker: Dict[str, Any], defender: Dict[str, Any]) -> int:
        """Calculate combat roll for convergence resolution
        
        Args:
            attacker: Attacking character
            defender: Defending character
            
        Returns:
            int: Combat roll value
        """
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        str_val = attacker.get("aSTR", 5)
        fs_val = attacker.get("aFS", 5)
        
        roll += str_val + fs_val
        
        # Scale by Power Potential
        op_factor = attacker.get("aOP", 5) / 5.0
        roll = int(roll * op_factor)
        
        # Apply morale factor
        morale = attacker.get("morale", 50) / 50.0
        roll = int(roll * morale)
        
        # Apply role bonuses
        role = attacker.get("role", "")
        if role == "FL":  # Field Leader
            roll += 10  # +10 to rolls
        elif role == "VG":  # Vanguard
            roll += 5   # +5 to rolls
        elif role == "SV":  # Sovereign
            roll += 15  # +15 to rolls
        
        return roll
    
    def _apply_damage(self, character: Dict[str, Any], damage: float, source: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Apply damage to character from convergence
        
        Args:
            character: Character taking damage
            damage: Amount of damage
            source: Source character dealing damage
            context: Match context
            
        Returns:
            dict: Damage application results
        """
        # Apply to HP first
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - damage)
        character["HP"] = new_hp
        
        # Update damage stats
        character.setdefault("rStats", {})
        character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + damage
        
        source.setdefault("rStats", {})
        source["rStats"]["rDD"] = source["rStats"].get("rDD", 0) + damage
        
        # Track damage contributors for assist attribution
        if "damage_contributors" in context:
            char_id = character.get("id", "unknown")
            source_id = source.get("id", "unknown")
            
            if char_id not in context["damage_contributors"]:
                context["damage_contributors"][char_id] = []
                
            if source_id not in context["damage_contributors"][char_id]:
                context["damage_contributors"][char_id].append(source_id)
        
        # Overflow to stamina if HP is depleted
        stamina_damage = 0
        if new_hp == 0:
            # Reduced stamina damage on overflow
            stamina_damage = (damage - current_hp) * 0.4
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Check for KO
            if new_stamina == 0:
                character["is_ko"] = True
                
                # Record KO stats for source
                source["rStats"]["rOTD"] = source["rStats"].get("rOTD", 0) + 1
                
                # Award assists
                if "damage_contributors" in context:
                    char_id = character.get("id", "unknown")
                    if char_id in context["damage_contributors"]:
                        for contributor_id in context["damage_contributors"][char_id]:
                            # Skip the KO source
                            if contributor_id != source.get("id", "unknown"):
                                # Find contributor and update stats
                                for team in [context.get("team_a", []), context.get("team_b", [])]:
                                    for char in team:
                                        if char.get("id") == contributor_id:
                                            char.setdefault("rStats", {})
                                            char["rStats"]["rAST"] = char["rStats"].get("rAST", 0) + 1
                                            break
        
        return {
            "damage": damage,
            "new_hp": new_hp,
            "stamina_damage": stamina_damage,
            "is_ko": character.get("is_ko", False)
        }

#############################################################################
#                           TRAIT SYSTEM                                    #
#############################################################################

class TraitSystem:
    """System for managing character traits"""
    
    def __init__(self, trait_file: Optional[str] = None):
        """Initialize trait system and load trait definitions
        
        Args:
            trait_file: Path to CSV file containing trait definitions
        """
        # Default to config path if not provided
        trait_file = trait_file or CONFIG.paths["trait_catalog"]
        
        # Load traits
        self.traits = self._load_traits(trait_file)
        
        # Default traits if loading fails
        if not self.traits:
            self.traits = self._get_default_traits()
        
        # Track trait activations
        self.activation_counts = {}
    
    def _load_traits(self, trait_file: str) -> Dict[str, Dict[str, Any]]:
        """Load trait definitions from CSV file
        
        Args:
            trait_file: Path to CSV file
            
        Returns:
            dict: Loaded trait definitions
        """
        traits = {}
        
        # Try to load from CSV
        try:
            if os.path.exists(trait_file):
                with open(trait_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        # Extract key info
                        trait_id = row.get('trait_id', '').strip()
                        if not trait_id:
                            continue
                            
                        # Parse triggers
                        triggers_raw = row.get('triggers', '').strip()
                        triggers = [t.strip() for t in triggers_raw.split(',') if t.strip()]
                        
                        # Create trait definition
                        traits[trait_id] = {
                            'name': row.get('name', trait_id),
                            'type': row.get('type', '').lower(),
                            'triggers': triggers,
                            'formula_key': row.get('formula_key', ''),
                            'formula_expr': row.get('formula_expr', ''),
                            'value': int(row.get('value', 0)) if row.get('value', '').isdigit() else 10,
                            'stamina_cost': int(row.get('stamina_cost', 0)) if row.get('stamina_cost', '').isdigit() else 0,
                            'cooldown': int(row.get('cooldown', 0)) if row.get('cooldown', '').isdigit() else 0,
                            'description': row.get('description', '')
                        }
                
                logger.info(f"Loaded {len(traits)} traits from {trait_file}")
                return traits
        except Exception as e:
            logger.error(f"Error loading traits: {e}")
        
        return {}
    
    def _get_default_traits(self) -> Dict[str, Dict[str, Any]]:
        """Get default trait definitions if loading fails
        
        Returns:
            dict: Default trait definitions
        """
        logger.warning("Using default traits as fallback")
        return {
            "genius": {
                "name": "Genius Intellect",
                "type": "combat",
                "triggers": ["convergence", "critical_hit"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Enhanced cognitive abilities provide combat advantages"
            },
            "armor": {
                "name": "Power Armor",
                "type": "defense",
                "triggers": ["damage_taken"],
                "formula_key": "damage_reduction",
                "value": 25,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Advanced armor reduces incoming damage"
            },
            "tactical": {
                "name": "Tactical Mastery",
                "type": "leadership",
                "triggers": ["convergence", "team_boost"],
                "formula_key": "bonus_roll",
                "value": 20,
                "stamina_cost": 10,
                "cooldown": 2,
                "description": "Superior tactical thinking improves combat capabilities"
            },
            "shield": {
                "name": "Vibranium Shield",
                "type": "defense",
                "triggers": ["damage_taken", "convergence"],
                "formula_key": "damage_reduction",
                "value": 30,
                "stamina_cost": 5,
                "cooldown": 1,
                "description": "Near-indestructible shield provides exceptional protection"
            },
            "agile": {
                "name": "Enhanced Agility",
                "type": "mobility",
                "triggers": ["convergence", "evasion"],
                "formula_key": "bonus_roll",
                "value": 15,
                "stamina_cost": 3,
                "cooldown": 0,
                "description": "Superhuman agility improves combat capabilities"
            },
            "spider-sense": {
                "name": "Spider Sense",
                "type": "precognition",
                "triggers": ["combat", "danger"],
                "formula_key": "defense_bonus",
                "value": 20,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Danger-sensing ability provides combat advantages"
            },
            "stretchy": {
                "name": "Polymorphic Body",
                "type": "mobility",
                "triggers": ["convergence", "positioning"],
                "formula_key": "bonus_roll",
                "value": 10,
                "stamina_cost": 5,
                "cooldown": 0,
                "description": "Malleable physiology allows for creative attacks"
            },
            "healing": {
                "name": "Rapid Healing",
                "type": "regeneration",
                "triggers": ["end_of_turn", "damage_taken"],
                "formula_key": "heal",
                "value": 5,
                "stamina_cost": 0,
                "cooldown": 0,
                "description": "Accelerated healing factor repairs injuries quickly"
            }
        }
    
    def check_trait_activation(self, character: Dict[str, Any], trigger: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Check if a character's traits activate for a given trigger
        
        Args:
            character: Character to check traits for
            trigger: Trigger type to check
            context: Additional context for activation
            
        Returns:
            list: Activated traits
        """
        context = context or {}
        activated_traits = []
        
        # Get character traits
        traits = character.get("traits", [])
        
        # Check each trait
        for trait_id in traits:
            if trait_id not in self.traits:
                continue
                
            trait = self.traits[trait_id]
            
            # Check if this trait responds to this trigger
            if trigger not in trait.get("triggers", []):
                continue
                
            # Check if on cooldown
            char_cooldowns = character.get("trait_cooldowns", {})
            if trait_id in char_cooldowns and char_cooldowns[trait_id] > 0:
                continue
                
            # Calculate activation chance
            activation_chance = self._calculate_activation_chance(character, trait, context)
            
            # Roll for activation
            if random.random() <= activation_chance:
                # Apply stamina cost
                stamina_cost = trait.get("stamina_cost", 0)
                if stamina_cost > 0:
                    character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
                
                # Apply cooldown
                cooldown = trait.get("cooldown", 0)
                if cooldown > 0:
                    if "trait_cooldowns" not in character:
                        character["trait_cooldowns"] = {}
                    character["trait_cooldowns"][trait_id] = cooldown
                
                # Add to activated traits
                activated_traits.append({
                    "trait_id": trait_id,
                    "trait_name": trait.get("name", trait_id),
                    "effect": trait.get("formula_key", ""),
                    "value": trait.get("value", 0),
                    "activation_chance": activation_chance
                })
                
                # Track activation for balance analysis
                if trait_id not in self.activation_counts:
                    self.activation_counts[trait_id] = 0
                self.activation_counts[trait_id] += 1
        
        return activated_traits
    
    def _calculate_activation_chance(self, character: Dict[str, Any], trait: Dict[str, Any], context: Dict[str, Any]) -> float:
        """Calculate trait activation chance with balanced factors
        
        Args:
            character: Character attempting trait activation
            trait: Trait definition
            context: Additional context
            
        Returns:
            float: Activation chance (0-1)
        """
        # Base chance (50%)
        base_chance = 0.5
        
        # Willpower impact
        wil = character.get("aWIL", 5)
        wil_modifier = (wil - 5) * 0.05  # +/- 5% per point away from 5
        
        # Morale impact
        morale = character.get("morale", 50)
        morale_modifier = 0
        if morale < 30:
            morale_modifier = -0.1  # -10% at very low morale
        elif morale > 70:
            morale_modifier = 0.1   # +10% at very high morale
        
        # Stamina impact
        stamina = character.get("stamina", 100)
        stamina_modifier = 0
        if stamina < 30:
            stamina_modifier = -0.1  # -10% at very low stamina
        
        # Combined chance
        final_chance = base_chance + wil_modifier + morale_modifier + stamina_modifier
        
        # Limit to reasonable range (20-90%)
        return max(0.2, min(final_chance, 0.9))
    
    def apply_trait_effect(self, character: Dict[str, Any], trigger: str, context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Apply trait effects for a given trigger
        
        Args:
            character: Character to apply effects to
            trigger: Trigger type
            context: Additional context
            
        Returns:
            list: Applied effects
        """
        context = context or {}
        effects = []
        
        # Check which traits activate
        activated_traits = self.check_trait_activation(character, trigger, context)
        
        # Process each activated trait
        for trait in activated_traits:
            trait_id = trait["trait_id"]
            trait_def = self.traits.get(trait_id, {})
            
            # Get effect type and value
            effect_type = trait_def.get("formula_key", "")
            effect_value = trait_def.get("value", 0)
            
            # Map effect type to standardized effect
            standardized_effect = self._map_effect_type(effect_type)
            
            # Add effect to list
            effects.append({
                "trait_id": trait_id,
                "trait_name": trait_def.get("name", trait_id),
                "effect": standardized_effect,
                "value": effect_value
            })
        
        return effects

#############################################################################
#                            PGN TRACKER                                    #
#############################################################################

class PGNTracker:
    """System for recording chess games in PGN format with character metadata"""
    
    def __init__(self, output_dir="results/pgn"):
        """Initialize the PGN tracker
        
        Args:
            output_dir: Directory to store PGN files
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.game_count = 0
        self.current_match = None
    
    def start_match(self, team_a_name: str, team_b_name: str, team_a_id: str, team_b_id: str, day: int = 1) -> None:
        """Start tracking a new match
        
        Args:
            team_a_name: Name of team A
            team_b_name: Name of team B
            team_a_id: ID of team A
            team_b_id: ID of team B
            day: Match day number
        """
        self.current_match = {
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "day": day,
            "date": datetime.datetime.now(),
            "games": []
        }
        self.game_count = 0
    
    def record_game(self, board: chess.Board, character_data: Dict[str, Any], opponent_name: str = "AI Opponent", 
                  result: str = "unknown") -> str:
        """Record a chess game in PGN format
        
        Args:
            board: Chess board with move history
            character_data: Character data dictionary
            opponent_name: Name of opponent (default: "AI Opponent")
            result: Game result ("win", "loss", "draw", or "unknown")
            
        Returns:
            str: PGN text of the recorded game
        """
        if not self.current_match:
            raise ValueError("No active match. Call start_match() first.")
        
        # Create a new game
        game = chess.pgn.Game()
        
        # Set headers
        game.headers["Event"] = f"META Fantasy League - Day {self.current_match['day']}"
        game.headers["Site"] = "META League Arena"
        game.headers["Date"] = self.current_match["date"].strftime("%Y.%m.%d")
        game.headers["Round"] = str(self.game_count + 1)
        game.headers["White"] = character_data.get("name", "Unknown")
        game.headers["Black"] = opponent_name
        
        # Set result based on game outcome
        if result == "win":
            game.headers["Result"] = "1-0"
        elif result == "loss":
            game.headers["Result"] = "0-1"
        elif result == "draw":
            game.headers["Result"] = "1/2-1/2"
        else:
            game.headers["Result"] = "*"  # Ongoing or unknown
        
        # Add META-specific headers
        game.headers["WhiteTeam"] = character_data.get("team_name", "Unknown Team")
        game.headers["WhiteRole"] = character_data.get("role", "Unknown")
        game.headers["WhiteDivision"] = character_data.get("division", "Unknown")
        
        # Add custom tags for easier analysis
        game.headers["CharacterID"] = character_data.get("id", "Unknown")
        game.headers["TeamID"] = character_data.get("team_id", "Unknown")
        
        # Add initial character stats
        game.headers["InitialHP"] = str(100)
        game.headers["InitialStamina"] = str(100)
        game.headers["FinalHP"] = str(character_data.get("HP", 0))
        game.headers["FinalStamina"] = str(character_data.get("stamina", 0))
        
        # Create comment with character information
        char_info = f"Character: {character_data.get('name', 'Unknown')}, "
        char_info += f"Role: {character_data.get('role', 'Unknown')}, "
        char_info += f"Team: {character_data.get('team_name', 'Unknown')}"
        
        game.comment = char_info
        
        # Add moves from board history
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)
        
        # Convert to PGN text
        pgn_string = io.StringIO()
        exporter = chess.pgn.FileExporter(pgn_string)
        game.accept(exporter)
        pgn_text = pgn_string.getvalue()
        
        # Store game in current match
        self.current_match["games"].append({
            "character_id": character_data.get("id", "Unknown"),
            "character_name": character_data.get("name", "Unknown"),
            "pgn": pgn_text,
            "result": result
        })
        
        self.game_count += 1
        
        return pgn_text
    
    def save_match_pgn(self, filename: Optional[str] = None) -> str:
        """Save all games from the current match to a PGN file
        
        Args:
            filename: Optional filename override
            
        Returns:
            str: Path to saved PGN file
        """
        if not self.current_match:
            raise ValueError("No active match to save")
        
        # Generate default filename if not specified
        if not filename:
            team_a_id = self.current_match["team_a_id"]
            team_b_id = self.current_match["team_b_id"]
            date_str = self.current_match["date"].strftime("%Y%m%d")
            filename = f"day{self.current_match['day']}_{team_a_id}_vs_{team_b_id}_{date_str}.pgn"
        
        # Ensure the filename has .pgn extension
        if not filename.endswith(".pgn"):
            filename += ".pgn"
        
        # Create full path
        file_path = os.path.join(self.output_dir, filename)
        
        # Write all games to file
        with open(file_path, "w") as pgn_file:
            for game in self.current_match["games"]:
                pgn_file.write(game["pgn"])
                pgn_file.write("\n\n")  # Add spacing between games
        
        logger.info(f"Saved {self.game_count} games to {file_path}")
        
        return file_path
    
    def record_match_games(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board], 
                         team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board], 
                         match_context: Dict[str, Any]) -> str:
        """Record PGN files for all characters in a match
        
        Args:
            team_a: List of team A characters
            team_a_boards: List of team A chess boards
            team_b: List of team B characters
            team_b_boards: List of team B chess boards
            match_context: Match context information
            
        Returns:
            str: Path to saved PGN file
        """
        # Start tracking the match
        self.start_match(
            team_a_name=match_context["team_a_name"],
            team_b_name=match_context["team_b_name"],
            team_a_id=match_context["team_a_id"],
            team_b_id=match_context["team_b_id"],
            day=match_context.get("day", 1)
        )
        
        # Record all active boards for team A
        for char, board in zip(team_a, team_a_boards):
            if char.get("is_active", True):
                # Determine result
                result = "unknown"
                if "is_ko" in char and char["is_ko"]:
                    result = "loss"
                elif "result" in char:
                    result = char["result"]
                
                self.record_game(board, char, opponent_name=f"{match_context['team_b_name']} AI", result=result)
        
        # Record all active boards for team B
        for char, board in zip(team_b, team_b_boards):
            if char.get("is_active", True):
                # Determine result
                result = "unknown"
                if "is_ko" in char and char["is_ko"]:
                    result = "loss"
                elif "result" in char:
                    result = char["result"]
                
                self.record_game(board, char, opponent_name=f"{match_context['team_a_name']} AI", result=result)
        
        # Save to file
        return self.save_match_pgn()

#############################################################################
#                         STAT TRACKER SYSTEM                               #
#############################################################################

class StatTracker:
    """System for tracking and processing result statistics"""
    
    def __init__(self):
        """Initialize the stat tracker"""
        # Dictionary to store all unit stats
        self.unit_stats = defaultdict(lambda: defaultdict(int))
        
        # Dictionary to store team stats
        self.team_stats = defaultdict(lambda: defaultdict(int))
        
        # Define canonical rStats
        self.canonical_rstats = self._get_canonical_rstats()
    
    def _get_canonical_rstats(self) -> Dict[str, Dict[str, str]]:
        """Get the canonical rStat definitions
        
        Returns:
            dict: Dictionary of canonical rStat definitions
        """
        return {
            # Shared stats (used by both divisions)
            "DD": {
                "name": "Damage Dealt",
                "domain": "b",
                "description": "Total damage inflicted on opponents"
            },
            "DS": {
                "name": "Damage Sustained",
                "domain": "b",
                "description": "Total damage received from opponents"
            },
            "OTD": {
                "name": "Opponent Takedown",
                "domain": "b",
                "description": "Successfully defeating an opponent"
            },
            "AST": {
                "name": "Assists",
                "domain": "b",
                "description": "Contributing to an opponent's defeat without landing the final blow"
            },
            "ULT": {
                "name": "Ultimate Move Impact",
                "domain": "b",
                "description": "Successful execution of a character's ultimate ability"
            },
            "LVS": {
                "name": "Lives Saved",
                "domain": "b",
                "description": "Preventing an ally from being defeated"
            },
            "LLS": {
                "name": "Lives Lost",
                "domain": "b",
                "description": "Instances of ally defeat"
            },
            "CTT": {
                "name": "Counterattacks",
                "domain": "b",
                "description": "Successful defensive attacks"
            },
            "EVS": {
                "name": "Evasion Success",
                "domain": "b",
                "description": "Successfully avoiding enemy attacks"
            },
            "HLG": {
                "name": "Healing",
                "domain": "b",
                "description": "Total healing provided to allies"
            },
            "WIN": {
                "name": "Matches Won",
                "domain": "b",
                "description": "Number of matches won"
            },
            "LOSS": {
                "name": "Matches Lost",
                "domain": "b",
                "description": "Number of matches lost"
            },
            "DRAW": {
                "name": "Matches Drawn",
                "domain": "b",
                "description": "Number of matches drawn"
            },
            
            # Operations division specific
            "CVo": {
                "name": "Convergence Victory",
                "domain": "o",
                "description": "Winning a convergence battle (Operations)"
            },
            "DVo": {
                "name": "Defensive Victory",
                "domain": "o",
                "description": "Successfully defending against an attack (Operations)"
            },
            "KNBo": {
                "name": "Knockbacks",
                "domain": "o",
                "description": "Pushing back opponents with forceful attacks (Operations)"
            },
            "DDo": {
                "name": "Damage Dealt - Ops",
                "domain": "o",
                "description": "Damage dealt by Operations characters"
            },
            "DSo": {
                "name": "Damage Sustained - Ops",
                "domain": "o",
                "description": "Damage taken by Operations characters"
            },
            
            # Intelligence division specific
            "MBi": {
                "name": "Mind Break",
                "domain": "i",
                "description": "Winning a convergence battle (Intelligence)"
            },
            "ILSi": {
                "name": "Illusion Success",
                "domain": "i",
                "description": "Successfully creating tactical illusions (Intelligence)"
            },
            "DDi": {
                "name": "Damage Dealt - Intel",
                "domain": "i",
                "description": "Damage dealt by Intelligence characters"
            },
            "DSi": {
                "name": "Damage Sustained - Intel",
                "domain": "i",
                "description": "Damage taken by Intelligence characters"
            }
        }
    
    def register_character(self, character: Dict[str, Any]) -> None:
        """Register a character for stat tracking
        
        Args:
            character: Character to register
        """
        char_id = character.get("id", "unknown")
        self.unit_stats[char_id]["unit_id"] = char_id
        self.unit_stats[char_id]["name"] = character.get("name", "Unknown")
        self.unit_stats[char_id]["division"] = character.get("division", "o")
        self.unit_stats[char_id]["role"] = character.get("role", "")
        self.unit_stats[char_id]["team_id"] = character.get("team_id", "")
        
        # Initialize rStats if needed
        if "rStats" not in character:
            character["rStats"] = {}
    
    def update_stat(self, character: Dict[str, Any], stat_name: str, value: int = 1, operation: str = "add") -> Dict[str, int]:
        """Update a specific stat for a character
        
        Args:
            character: Character to update
            stat_name: Name of stat to update (with or without 'r' prefix)
            value: Value to add/set
            operation: 'add' (default), 'set', or 'max'
            
        Returns:
            dict: Updated rStats
        """
        # Get character ID
        char_id = character.get("id", "unknown")
        
        # Strip 'r' prefix if present
        base_stat = stat_name[1:] if stat_name.startswith('r') else stat_name
        
        # Add 'r' prefix for storage
        full_stat_name = f"r{base_stat}"
        
        # Ensure rStats exists
        if "rStats" not in character:
            character["rStats"] = {}
        
        # Update based on operation type
        if operation == "add":
            character["rStats"][full_stat_name] = character["rStats"].get(full_stat_name, 0) + value
        elif operation == "set":
            character["rStats"][full_stat_name] = value
        elif operation == "max":
            character["rStats"][full_stat_name] = max(character["rStats"].get(full_stat_name, 0), value)
        
        # Also update in tracking dictionary
        self.unit_stats[char_id][full_stat_name] = character["rStats"][full_stat_name]
        
        return character["rStats"]
    
    def update_team_stat(self, team_id: str, stat_name: str, value: int = 1, operation: str = "add") -> None:
        """Update a team-level stat
        
        Args:
            team_id: ID of team to update
            stat_name: Name of stat to update (with or without 't' prefix)
            value: Value to add/set
            operation: 'add' (default), 'set', or 'max'
        """
        # Strip 't' prefix if present
        base_stat = stat_name[1:] if stat_name.startswith('t') else stat_name
        
        # Add 't' prefix for storage
        full_stat_name = f"t{base_stat}"
        
        # Update based on operation type
        if operation == "add":
            self.team_stats[team_id][full_stat_name] += value
        elif operation == "set":
            self.team_stats[team_id][full_stat_name] = value
        elif operation == "max":
            self.team_stats[team_id][full_stat_name] = max(self.team_stats[team_id][full_stat_name], value)
    
    def track_combat_event(self, character: Dict[str, Any], event_type: str, value: int = 1, 
                         opponent: Optional[Dict[str, Any]] = None, context: Optional[Dict[str, Any]] = None) -> None:
        """Track a combat-related event
        
        Args:
            character: Character experiencing the event
            event_type: Type of combat event
            value: Value of the event
            opponent: Optional opponent character
            context: Optional additional context
        """
        # Get character properties
        division = character.get("division", "o")
        
        # Map events to stats
        event_to_stat = {
            # General stats
            "damage_dealt": "DD",
            "damage_taken": "DS",
            "ko_caused": "OTD",
            "assist": "AST",
            "ultimate_move": "ULT",
            "lives_saved": "LVS",
            "evasion": "EVS",
            "healing": "HLG",
            
            # Specific stats
            "convergence_win": "CVo" if division == "o" else "MBi",
            "counterattack": "CTT",
            "illusion": "ILSi",
            "knockback": "KNBo"
        }
        
        # Update appropriate stat
        if event_type in event_to_stat:
            stat_name = event_to_stat[event_type]
            
            # Add division suffix for damage stats
            if stat_name == "DD" or stat_name == "DS":
                stat_name = f"{stat_name}{division}"
                
            self.update_stat(character, stat_name, value)
        
        # Special handling for KO events
        if event_type == "ko_caused" and opponent:
            # Update team KO stats
            team_id = character.get("team_id", "unknown")
            opp_team_id = opponent.get("team_id", "unknown")
            
            self.update_team_stat(team_id, "KO_CAUSED", 1)
            self.update_team_stat(opp_team_id, "KO_SUFFERED", 1)
            
            # Special handling for Field Leader KO
            if opponent.get("role") == "FL":
                self.update_team_stat(team_id, "FL_KO_CAUSED", 1)
                self.update_team_stat(opp_team_id, "FL_KO_SUFFERED", 1)
    
    def record_match_result(self, character: Dict[str, Any], result: str) -> None:
        """Record match result for a character
        
        Args:
            character: Character to update
            result: Match result ("win", "loss", "draw", "bench")
        """
        # Map result to stat
        if result == "win":
            self.update_stat(character, "WIN", 1)
        elif result == "loss":
            self.update_stat(character, "LOSS", 1)
        elif result == "draw":
            self.update_stat(character, "DRAW", 1)
        
        # Update team stats
        team_id = character.get("team_id", "unknown")
        
        if result == "win":
            self.update_team_stat(team_id, "WINS", 1)
        elif result == "loss":
            self.update_team_stat(team_id, "LOSSES", 1)
        elif result == "draw":
            self.update_team_stat(team_id, "DRAWS", 1)
    
    def validate_rstats(self, character: Dict[str, Any]) -> Dict[str, int]:
        """Validate and normalize rStats for a character
        
        Args:
            character: Character to validate stats for
            
        Returns:
            dict: Validated rStats
        """
        # Get character division
        division = character.get("division", "o")
        
        # Ensure rStats exists
        if "rStats" not in character:
            character["rStats"] = {}
        
        # Get current rStats
        rstats = character["rStats"]
        
        # Check each stat against canonical definitions
        validated = {}
        
        for stat_name, stat_value in rstats.items():
            # Strip 'r' prefix if present
            base_stat = stat_name[1:] if stat_name.startswith('r') else stat_name
            
            # Check if stat is in canonical list
            if base_stat in self.canonical_rstats:
                stat_def = self.canonical_rstats[base_stat]
                
                # Check if stat is valid for this division
                if stat_def["domain"] == "b" or stat_def["domain"] == division:
                    # Add 'r' prefix for storage
                    validated[f"r{base_stat}"] = stat_value
        
        # Update character's rStats
        character["rStats"] = validated
        
        return validated
    
    def export_stats_to_csv(self, output_path: Optional[str] = None) -> Tuple[str, str, str]:
        """Export tracked stats to CSV files
        
        Args:
            output_path: Base path for output files
            
        Returns:
            tuple: Paths to character and team stats CSV files
        """
        # Generate default path if none provided
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "results/stats"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"rstats_{timestamp}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export character stats
        char_path = f"{output_path}_characters.csv"
        
        with open(char_path, "w", newline="") as f:
            # Get all possible fields
            meta_fields = ["unit_id", "name", "division", "role", "team_id"]
            stat_fields = []
            
            for unit_stats in self.unit_stats.values():
                for key in unit_stats.keys():
                    if key.startswith('r') and key not in stat_fields and key not in meta_fields:
                        stat_fields.append(key)
            
            # Sort stat fields
            stat_fields.sort()
            
            # Create CSV writer
            writer = csv.DictWriter(f, fieldnames=meta_fields + stat_fields)
            writer.writeheader()
            
            # Write character stats
            for unit_id, stats in self.unit_stats.items():
                writer.writerow(stats)
        
        # Export team stats
        team_path = f"{output_path}_teams.csv"
        
        with open(team_path, "w", newline="") as f:
            # Get all possible fields
            fields = ["team_id"]
            
            for team_stats in self.team_stats.values():
                for key in team_stats.keys():
                    if key not in fields:
                        fields.append(key)
            
            # Sort fields
            fields.sort()
            
            # Create CSV writer
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            # Write team stats
            for team_id, stats in self.team_stats.items():
                row = {"team_id": team_id}
                row.update(stats)
                writer.writerow(row)
        
        # Export stat definitions for reference
        def_path = f"{output_path}_definitions.json"
        
        with open(def_path, "w") as f:
            json.dump(self.canonical_rstats, f, indent=2)
        
        logger.info(f"Exported stats to {char_path} and {team_path}")
        return (char_path, team_path, def_path)
    
    def export_stats_to_json(self, output_path: Optional[str] = None) -> Tuple[str, str]:
        """Export tracked stats to JSON files
        
        Args:
            output_path: Base path for output files
            
        Returns:
            tuple: Paths to character and team stats JSON files
        """
        # Generate default path if none provided
        if output_path is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = "results/stats"
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"rstats_{timestamp}")
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export character stats
        char_path = f"{output_path}_characters.json"
        
        with open(char_path, "w") as f:
            json.dump(dict(self.unit_stats), f, indent=2)
        
        # Export team stats
        team_path = f"{output_path}_teams.json"
        
        with open(team_path, "w") as f:
            json.dump(dict(self.team_stats), f, indent=2)
        
        logger.info(f"Exported JSON stats to {char_path} and {team_path}")
        return (char_path, team_path)

#############################################################################
#                        MATCH VISUALIZATION                                #
#############################################################################

class MatchVisualizer:
    """Handles match visualization and reporting"""
    
    @staticmethod
    def generate_match_summary(result: Dict[str, Any]) -> str:
        """Generate a text summary of a match result
        
        Args:
            result: Match result data
            
        Returns:
            str: Formatted match summary
        """
        # Extract key information
        team_a_name = result.get("team_a_name", "Team A")
        team_b_name = result.get("team_b_name", "Team B")
        team_a_wins = result.get("team_a_wins", 0)
        team_b_wins = result.get("team_b_wins", 0)
        winner = result.get("winner", "Draw")
        winning_team = result.get("winning_team", "None")
        convergence_count = result.get("convergence_count", 0)
        trait_activations = result.get("trait_activations", 0)
        
        # Get character results
        character_results = result.get("character_results", [])
        
        # Find key performers
        top_damage_dealer = {"name": "Unknown", "damage": 0, "team": None}
        top_knockouts = {"name": "Unknown", "kos": 0, "team": None}
        
        for char in character_results:
            # Check damage dealt
            damage = 0
            if "rStats" in char:
                # Check different damage stats
                damage += char["rStats"].get("rDD", 0)
                damage += char["rStats"].get("rDDo", 0)
                damage += char["rStats"].get("rDDi", 0)
            
            if damage > top_damage_dealer["damage"]:
                top_damage_dealer = {
                    "name": char["character_name"],
                    "damage": damage,
                    "team": char["team"]
                }
            
            # Check knockouts
            kos = 0
            if "rStats" in char:
                kos = char["rStats"].get("rOTD", 0)
            
            if kos > top_knockouts["kos"]:
                top_knockouts = {
                    "name": char["character_name"],
                    "kos": kos,
                    "team": char["team"]
                }
        
        # Generate summary
        summary = f"""
=== MATCH SUMMARY ===
{team_a_name} vs {team_b_name}

RESULT: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}
WINNER: {winning_team}

KEY STATISTICS:
- Convergences: {convergence_count}
- Trait Activations: {trait_activations}

TOP PERFORMERS:
- Damage Dealer: {top_damage_dealer["name"]} ({team_a_name if top_damage_dealer["team"] == "A" else team_b_name})
- Knockouts: {top_knockouts["name"]} ({team_a_name if top_knockouts["team"] == "A" else team_b_name})

TEAM SUMMARIES:
"""
        
        # Add team A summary
        team_a_active = [c for c in character_results if c["team"] == "A" and c["was_active"]]
        team_a_ko = [c for c in team_a_active if c["is_ko"]]
        
        summary += f"{team_a_name}: {len(team_a_active) - len(team_a_ko)}/{len(team_a_active)} characters active\n"
        
        # Add team B summary
        team_b_active = [c for c in character_results if c["team"] == "B" and c["was_active"]]
        team_b_ko = [c for c in team_b_active if c["is_ko"]]
        
        summary += f"{team_b_name}: {len(team_b_active) - len(team_b_ko)}/{len(team_b_active)} characters active\n"
        
        # Add momentum summary if available
        if "team_a_momentum_final" in result:
            team_a_momentum = result["team_a_momentum_final"]
            team_b_momentum = result["team_b_momentum_final"]
            
            summary += f"\nMOMENTUM STATES:\n"
            summary += f"{team_a_name}: {team_a_momentum['state'].upper()} ({team_a_momentum['value']})\n"
            summary += f"{team_b_name}: {team_b_momentum['state'].upper()} ({team_b_momentum['value']})\n"
        
        # Add injuries summary if any
        injured = [c for c in character_results if c["is_ko"] and c["was_active"]]
        if injured:
            summary += f"\nINJURIES:\n"
            for char in injured:
                team_name = team_a_name if char["team"] == "A" else team_b_name
                summary += f"- {char['character_name']} ({team_name}): Knocked Out\n"
        
        return summary
    
    @staticmethod
    def generate_narrative_report(result: Dict[str, Any]) -> str:
        """Generate a narrative report for a match
        
        Args:
            result: Match result data
            
        Returns:
            str: Narrative match report
        """
        # Extract key information
        team_a_name = result.get("team_a_name", "Team A")
        team_b_name = result.get("team_b_name", "Team B")
        team_a_wins = result.get("team_a_wins", 0)
        team_b_wins = result.get("team_b_wins", 0)
        winner = result.get("winner", "Draw")
        winning_team = result.get("winning_team", "None")
        
        # Get character results for key stories
        character_results = result.get("character_results", [])
        
        # Get convergences for storytelling
        convergences = result.get("convergence_logs", [])
        
        # Determine if this was a close match or a blowout
        match_type = "close" if abs(team_a_wins - team_b_wins) <= 2 else "decisive"
        
        # Generate narrative opening
        if match_type == "close":
            opening = random.choice([
                f"In a thrilling contest that came down to the wire, {winning_team} narrowly defeated their rivals.",
                f"The arena fell silent as {winning_team} secured a hard-fought victory in the closing moments.",
                f"Neither team gave an inch in a back-and-forth battle that {winning_team} ultimately won."
            ])
        else:
            opening = random.choice([
                f"{winning_team} dominated from the opening bell, securing a decisive victory.",
                f"It was a showcase of tactical superiority as {winning_team} overwhelmed their opponents.",
                f"The outcome was never in doubt as {winning_team} controlled every aspect of the match."
            ])
        
        # Find key performers for storylines
        top_performers = []
        for char in character_results:
            if not char["was_active"]:
                continue
                
            # Calculate performance score
            score = 0
            if "rStats" in char:
                # Damage is a factor
                damage = char["rStats"].get("rDD", 0) + char["rStats"].get("rDDo", 0) + char["rStats"].get("rDDi", 0)
                score += damage / 100
                
                # Knockouts are valuable
                kos = char["rStats"].get("rOTD", 0)
                score += kos * 5
                
                # Ultimate moves are impressive
                ults = char["rStats"].get("rULT", 0)
                score += ults * 3
                
                # Healing and support counts
                healing = char["rStats"].get("rHLG", 0)
                score += healing / 50
                
                # Convergence victories matter
                cvs = char["rStats"].get("rCVo", 0) + char["rStats"].get("rMBi", 0)
                score += cvs * 2
            
            if score > 0:
                top_performers.append({
                    "name": char["character_name"],
                    "team": char["team"],
                    "score": score,
                    "role": char["role"],
                    "is_ko": char["is_ko"]
                })
        
        # Sort by performance score
        top_performers.sort(key=lambda x: x["score"], reverse=True)
        
        # Generate narrative body
        body = ""
        
        # Add key performer narratives
        if top_performers:
            mvp = top_performers[0]
            mvp_team = team_a_name if mvp["team"] == "A" else team_b_name
            
            body += f"\n{mvp['name']} was the standout performer for {mvp_team}, "
            
            if mvp["role"] == "FL":
                body += "leading the team with tactical brilliance. "
            elif mvp["role"] == "VG":
                body += "breaking through enemy lines with devastating efficiency. "
            elif mvp["role"] == "EN":
                body += "enforcing dominance with raw power and determination. "
            elif mvp["role"] == "SV":
                body += "controlling reality with unmatched strategic awareness. "
            else:
                body += "showcasing exceptional skill throughout the match. "
            
            # Add a secondary performer if available
            if len(top_performers) > 1:
                second = top_performers[1]
                second_team = team_a_name if second["team"] == "A" else team_b_name
                
                body += f"\n\n{second['name']} of {second_team} also made a significant impact, "
                
                if second["is_ko"]:
                    body += "despite being knocked out in the later stages. "
                else:
                    body += "remaining a threat until the final moments. "
        
        # Add notable convergences if available
        if convergences:
            # Pick a notable convergence
            notable = random.choice(convergences)
            
            body += f"\n\nA pivotal moment came when {notable['winner']} triumphed over {notable['loser']} "
            body += f"in a convergence at {notable['square']}, dealing significant damage. "
            
            # If there was a critical success, highlight it
            critical = next((c for c in convergences if c.get("outcome") == "critical_success"), None)
            if critical:
                body += f"\n\n{critical['winner']} executed a breathtaking ultimate move that shifted the momentum of the match. "
        
        # Add substitution narratives if any occurred
        substitutions = result.get("substitutions", [])
        if substitutions:
            sub = substitutions[0]
            body += f"\n\nThe match saw a critical Field Leader substitution when {sub['replacement']} "
            body += f"stepped in for the knocked out {sub['ko_character']}, changing team dynamics. "
        
        # Generate narrative closing
        if match_type == "close":
            closing = random.choice([
                f"As the dust settled, {winning_team} emerged victorious, but both teams earned respect for their performance.",
                f"The match will be remembered as one of the season's most competitive, with {winning_team} barely edging out the win.",
                f"Analysts will debate the strategic decisions that ultimately gave {winning_team} the narrow victory."
            ])
        else:
            closing = random.choice([
                f"The dominant performance from {winning_team} sends a message to all other teams in the league.",
                f"Questions will be asked about tactical preparation after {winning_team} secured such a one-sided victory.",
                f"The coaching staff of {winning_team} deserves credit for a perfectly executed game plan."
            ])
        
        # Combine all sections
        report = f"""
=== MATCH NARRATIVE REPORT ===
{team_a_name} vs {team_b_name}
Final Score: {team_a_wins}-{team_b_wins}

{opening}
{body}

{closing}
"""
        
        return report
    
    @staticmethod
    def save_match_report(result: Dict[str, Any], output_dir: str = "results/reports") -> Tuple[str, str]:
        """Save match reports to files
        
        Args:
            result: Match result data
            output_dir: Directory to save reports
            
        Returns:
            tuple: Paths to saved report files
        """
        # Create directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Create timestamp and match identifier
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        team_a_id = result.get("team_a_id", "unknown")
        team_b_id = result.get("team_b_id", "unknown")
        match_id = f"{team_a_id}_vs_{team_b_id}"
        
        # Generate reports
        summary = MatchVisualizer.generate_match_summary(result)
        narrative = MatchVisualizer.generate_narrative_report(result)
        
        # Save summary report
        summary_path = os.path.join(output_dir, f"{match_id}_{timestamp}_summary.txt")
        with open(summary_path, "w") as f:
            f.write(summary)
        
        # Save narrative report
        narrative_path = os.path.join(output_dir, f"{match_id}_{timestamp}_narrative.txt")
        with open(narrative_path, "w") as f:
            f.write(narrative)
        
        logger.info(f"Reports saved to {summary_path} and {narrative_path}")
        
        return summary_path, narrative_path
    
    @staticmethod
    def generate_match_visualization(result: Dict[str, Any]) -> str:
        """Generate a text-based visualization of the match
        
        Args:
            result: Match result data
            
        Returns:
            str: Text visualization of the match
        """
        # Extract character results
        character_results = result.get("character_results", [])
        
        # Get team names
        team_a_name = result.get("team_a_name", "Team A")
        team_b_name = result.get("team_b_name", "Team B")
        
        # Filter for active characters
        team_a_active = [c for c in character_results if c["team"] == "A" and c["was_active"]]
        team_b_active = [c for c in character_results if c["team"] == "B" and c["was_active"]]
        
        # Generate team rosters with status
        team_a_roster = []
        for char in team_a_active:
            status = "KO" if char["is_ko"] else ("DEAD" if char.get("is_dead", False) else "OK")
            hp = char["final_hp"]
            stam = char["final_stamina"]
            role = char["role"]
            
            # Format entry
            entry = f"{char['character_name']} ({role}): {status} | HP: {hp:.1f} | STAM: {stam:.1f}"
            team_a_roster.append(entry)
        
        team_b_roster = []
        for char in team_b_active:
            status = "KO" if char["is_ko"] else ("DEAD" if char.get("is_dead", False) else "OK")
            hp = char["final_hp"]
            stam = char["final_stamina"]
            role = char["role"]
            
            # Format entry
            entry = f"{char['character_name']} ({role}): {status} | HP: {hp:.1f} | STAM: {stam:.1f}"
            team_b_roster.append(entry)
        
        # Calculate team health percentages
        team_a_health = sum(c["final_hp"] for c in team_a_active) / (len(team_a_active) * 100) * 100
        team_b_health = sum(c["final_hp"] for c in team_b_active) / (len(team_b_active) * 100) * 100
        
        # Generate health bars
        a_health_bar = MatchVisualizer.generate_health_bar(team_a_health)
        b_health_bar = MatchVisualizer.generate_health_bar(team_b_health)
        
        # Generate visualization
        viz = f"""
==========================================
            MATCH VISUALIZATION            
==========================================

{team_a_name} ({result.get('team_a_wins', 0)} wins)
{a_health_bar} {team_a_health:.1f}%
"""
        
        # Add team A roster
        for entry in team_a_roster:
            viz += f"  {entry}\n"
        
        viz += f"\nvs.\n\n"
        
        # Add team B roster
        viz += f"{team_b_name} ({result.get('team_b_wins', 0)} wins)\n"
        viz += f"{b_health_bar} {team_b_health:.1f}%\n"
        
        for entry in team_b_roster:
            viz += f"  {entry}\n"
        
        viz += "\n==========================================\n"
        
        # Add convergence map if available
        convergences = result.get("convergence_logs", [])
        if convergences:
            viz += "\nNOTABLE CONVERGENCE POINTS:\n"
            
            # Take up to 5 most significant convergences
            significant = sorted(convergences, key=lambda x: abs(x.get("a_roll", 0) - x.get("b_roll", 0)), reverse=True)[:5]
            
            for conv in significant:
                viz += f"  {conv['square']}: {conv['winner']} defeated {conv['loser']} (Damage: {conv.get('reduced_damage', 0):.1f})\n"
        
        return viz
    
    @staticmethod
    def generate_health_bar(percentage: float, width: int = 20) -> str:
        """Generate a text-based health bar
        
        Args:
            percentage: Health percentage (0-100)
            width: Width of the bar
            
        Returns:
            str: Text-based health bar
        """
        # Ensure percentage is within range
        percentage = max(0, min(100, percentage))
        
        # Calculate filled positions
        filled = int(width * percentage / 100)
        
        # Generate bar
        if percentage > 60:
            # Green for high health
            bar = f"[{'#' * filled}{' ' * (width - filled)}]"
        elif percentage > 30:
            # Yellow for medium health
            bar = f"[{'!' * filled}{' ' * (width - filled)}]"
        else:
            # Red for low health
            bar = f"[{'*' * filled}{' ' * (width - filled)}]"
        
        return bar

#############################################################################
#                      MAIN SIMULATOR CLASS                                 #
#############################################################################

class MetaLeagueSimulator:
    """Main simulator class for META Fantasy League simulations"""
    
    def __init__(self):
        """Initialize the simulator"""
        # Validate system integrity
        if not SystemValidator.validate_all():
            logger.error("System validation failed")
            raise RuntimeError("System validation failed. Fix errors before continuing.")
        
        # Initialize subsystems
        self.trait_system = TraitSystem()
        self.chess_system = ChessSystem(CONFIG.paths["stockfish_path"])
        self.combat_system = CombatSystem(self.trait_system)
        self.convergence_system = ConvergenceSystem(self.trait_system)
        self.pgn_tracker = PGNTracker()
        self.stat_tracker = StatTracker()
        
        logger.info("META Fantasy League Simulator initialized successfully")
    
    def simulate_match(self, team_a: List[Dict[str, Any]], team_b: List[Dict[str, Any]], day_number: int = 1, 
                     show_details: bool = True) -> Dict[str, Any]:
        """Simulate a match between two teams
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            day_number: Day number for scheduling
            show_details: Whether to show detailed output
            
        Returns:
            dict: Match result
        """
        # Validate teams
        if not team_a or not team_b:
            raise ValueError("Both teams must have characters")
        
        # Validate team sizes
        if len(team_a) < CONFIG.simulation["teams_per_match"] or len(team_b) < CONFIG.simulation["teams_per_match"]:
            raise ValueError(f"Both teams must have at least {CONFIG.simulation['teams_per_match']} characters")
        
        # Extract active characters only
        team_a_active = [char for char in team_a if char.get("is_active", True)][:CONFIG.simulation["teams_per_match"]]
        team_b_active = [char for char in team_b if char.get("is_active", True)][:CONFIG.simulation["teams_per_match"]]
        
        # Validate active team sizes
        if len(team_a_active) < CONFIG.simulation["teams_per_match"] or len(team_b_active) < CONFIG.simulation["teams_per_match"]:
            raise ValueError(f"Both teams must have at least {CONFIG.simulation['teams_per_match']} active characters")
        
        # Get team information
        team_a_id = team_a_active[0]["team_id"]
        team_b_id = team_b_active[0]["team_id"]
        team_a_name = team_a_active[0]["team_name"]
        team_b_name = team_b_active[0]["team_name"]
        
        # Setup context
        match_context = {
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "day": day_number,
            "date": CONFIG.get_date_for_day(day_number),
            "round": 1,
            "convergence_logs": [],
            "trait_logs": [],
            "damage_contributors": {},
            "team_a": team_a_active,
            "team_b": team_b_active
        }
        
        if show_details:
            logger.info(f"Simulating match: {team_a_name} vs {team_b_name}")
            logger.info(f"Day {day_number} ({match_context['date']})")
        
        # Initialize characters
        for char in team_a_active + team_b_active:
            char["HP"] = 100
            char["stamina"] = 100
            char["is_ko"] = False
            char["is_dead"] = False
            char["was_active"] = True
            char["first_ko"] = True
            char["rStats"] = {}
            char["result"] = "unknown"
            
            # Register with stat tracker
            self.stat_tracker.register_character(char)
            
            # Assign team
            if char in team_a_active:
                char["team"] = "A"
            else:
                char["team"] = "B"
        
        # Initialize chess boards
        team_a_boards = [self.chess_system.create_board() for _ in range(len(team_a_active))]
        team_b_boards = [self.chess_system.create_board() for _ in range(len(team_b_active))]
        
        # Simulate chess games
        max_moves = CONFIG.simulation["max_moves"]
        max_convergences_per_char = CONFIG.simulation["max_convergences_per_char"]
        convergence_count = 0
        trait_activations = len(match_context["trait_logs"])
        
        # Run simulation rounds
        for round_num in range(1, max_moves + 1):
            match_context["round"] = round_num
            
            if show_details:
                logger.info(f"Round {round_num}")
            
            # Process each character's turn
            for idx, (char, board) in enumerate(zip(team_a_active, team_a_boards)):
                if char["is_ko"] or char["is_dead"]:
                    continue
                
                if show_details:
                    logger.debug(f"  {char['name']} (Team A) turn")
                
                # Get material before move
                material_before = self._get_board_material(board)
                
                # Make move
                if board.turn == chess.WHITE:  # Only move if it's our turn
                    move = self.chess_system.select_move(board, char)
                    if move:
                        board.push(move)
                
                # Get material after move
                material_after = self._get_board_material(board)
                
                # Calculate material change
                material_change = material_after - material_before
                
                # Update character metrics
                self.combat_system.update_character_metrics(char, material_change, show_details)
            
            for idx, (char, board) in enumerate(zip(team_b_active, team_b_boards)):
                if char["is_ko"] or char["is_dead"]:
                    continue
                
                if show_details:
                    logger.debug(f"  {char['name']} (Team B) turn")
                
                # Get material before move
                material_before = self._get_board_material(board)
                
                # Make move
                if board.turn == chess.WHITE:  # Only move if it's our turn
                    move = self.chess_system.select_move(board, char)
                    if move:
                        board.push(move)
                
                # Get material after move
                material_after = self._get_board_material(board)
                
                # Calculate material change
                material_change = material_after - material_before
                
                # Update character metrics
                self.combat_system.update_character_metrics(char, material_change, show_details)
            
            # Process convergences
            convergences = self.convergence_system.process_convergences(
                team_a_active, team_a_boards,
                team_b_active, team_b_boards,
                match_context, max_convergences_per_char,
                show_details
            )
            
            convergence_count += len(convergences)
            
            # Update trait cooldowns
            self.trait_system.update_cooldowns(team_a_active + team_b_active)
            
            # Apply end of round effects
            self.combat_system.apply_end_of_round_effects(team_a_active + team_b_active, match_context, show_details)
            
            # Update trait activation count
            trait_activations = len(match_context["trait_logs"])
            
            # Check for game end conditions
            if self._check_match_end(team_a_active, team_b_active, match_context):
                if show_details:
                    logger.info(f"Match ended in round {round_num}")
                break
        
        # Calculate match results
        match_result = self._calculate_match_result(team_a_active, team_b_active, match_context)
        
        # Update character stats
        for char in team_a_active:
            # Set final stats
            char["final_hp"] = char["HP"]
            char["final_stamina"] = char["stamina"]
            
            # Record match result
            result = "win" if match_result["winner"] == "Team A" else "loss"
            self.stat_tracker.record_match_result(char, result)
            
            # Record character result
            match_result["character_results"].append({
                "character_id": char["id"],
                "character_name": char["name"],
                "team": "A",
                "team_name": team_a_name,
                "role": char["role"],
                "is_ko": char.get("is_ko", False),
                "is_dead": char.get("is_dead", False),
                "was_active": char["was_active"],
                "final_hp": char["final_hp"],
                "final_stamina": char["final_stamina"],
                "rStats": char["rStats"]
            })
        
        for char in team_b_active:
            # Set final stats
            char["final_hp"] = char["HP"]
            char["final_stamina"] = char["stamina"]
            
            # Record match result
            result = "win" if match_result["winner"] == "Team B" else "loss"
            self.stat_tracker.record_match_result(char, result)
            
            # Record character result
            match_result["character_results"].append({
                "character_id": char["id"],
                "character_name": char["name"],
                "team": "B",
                "team_name": team_b_name,
                "role": char["role"],
                "is_ko": char.get("is_ko", False),
                "is_dead": char.get("is_dead", False),
                "was_active": char["was_active"],
                "final_hp": char["final_hp"],
                "final_stamina": char["final_stamina"],
                "rStats": char["rStats"]
            })
        
        # Add stats to match result
        match_result["convergence_count"] = convergence_count
        match_result["trait_activations"] = trait_activations
        match_result["convergence_logs"] = match_context["convergence_logs"]
        match_result["trait_logs"] = match_context["trait_logs"]
        
        # Generate reports
        match_result["summary_report"] = MatchVisualizer.generate_match_summary(match_result)
        match_result["narrative_report"] = MatchVisualizer.generate_narrative_report(match_result)
        
        # Save PGN
        try:
            pgn_path = self.pgn_tracker.record_match_games(team_a_active, team_a_boards, team_b_active, team_b_boards, match_context)
            match_result["pgn_path"] = pgn_path
        except Exception as e:
            logger.error(f"Error saving PGN: {e}")
            raise RuntimeError("Failed to save PGN. This is a fatal error as PGNs are required.")
        
        # Save reports
        try:
            summary_path, narrative_path = MatchVisualizer.save_match_report(match_result)
            match_result["summary_path"] = summary_path
            match_result["narrative_path"] = narrative_path
        except Exception as e:
            logger.error(f"Error saving reports: {e}")
        
        # Export stats
        try:
            stats_paths = self.stat_tracker.export_stats_to_csv()
            match_result["stats_paths"] = stats_paths
        except Exception as e:
            logger.error(f"Error exporting stats: {e}")
        
        if show_details:
            logger.info(f"Match finished: {team_a_name} {match_result['team_a_wins']} - {match_result['team_b_wins']} {team_b_name}")
            logger.info(f"Winner: {match_result['winning_team']}")
        
        return match_result
    
    def _get_board_material(self, board: chess.Board) -> float:
        """Calculate material value on a chess board
        
        Args:
            board: Chess board
            
        Returns:
            float: Material value (positive for white advantage)
        """
        # Piece values
        piece_values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0  # Not counting king
        }
        
        white_material = 0
        black_material = 0
        
        # Count pieces
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = piece_values.get(piece.piece_type, 0)
                if piece.color == chess.WHITE:
                    white_material += value
                else:
                    black_material += value
        
        # Return difference (positive = white advantage)
        return white_material - black_material
    
    def _check_match_end(self, team_a: List[Dict[str, Any]], team_b: List[Dict[str, Any]], 
                       match_context: Dict[str, Any]) -> bool:
        """Check if match end conditions are met
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            match_context: Match context
            
        Returns:
            bool: True if match should end
        """
        # Check KO counts
        team_a_ko_count = sum(1 for char in team_a if char.get("is_ko", False) or char.get("is_dead", False))
        team_b_ko_count = sum(1 for char in team_b if char.get("is_ko", False) or char.get("is_dead", False))
        
        # Check if team A Field Leader is KO'd
        team_a_fl_ko = any(char.get("is_ko", False) for char in team_a if char.get("role") == "FL")
        
        # Check if team B Field Leader is KO'd
        team_b_fl_ko = any(char.get("is_ko", False) for char in team_b if char.get("role") == "FL")
        
        # Check team health
        team_a_health = sum(char.get("HP", 0) for char in team_a) / (len(team_a) * 100) * 100
        team_b_health = sum(char.get("HP", 0) for char in team_b) / (len(team_b) * 100) * 100
        
        # Check KO threshold
        ko_threshold = CONFIG.simulation["ko_threshold"]
        team_a_ko_loss = team_a_ko_count >= ko_threshold
        team_b_ko_loss = team_b_ko_count >= ko_threshold
        
        # Check health threshold
        health_threshold = CONFIG.simulation["team_hp_threshold"]
        team_a_health_loss = team_a_health <= health_threshold
        team_b_health_loss = team_b_health <= health_threshold
        
        # Determine if match should end
        match_end = (
            team_a_fl_ko or team_b_fl_ko or  # Field Leader KO
            team_a_ko_loss or team_b_ko_loss or  # KO threshold
            team_a_health_loss or team_b_health_loss  # Health threshold
        )
        
        # Record reason for match end
        if match_end:
            if team_a_fl_ko:
                match_context["end_reason"] = "Team A Field Leader KO"
            elif team_b_fl_ko:
                match_context["end_reason"] = "Team B Field Leader KO"
            elif team_a_ko_loss:
                match_context["end_reason"] = f"Team A reached KO threshold ({team_a_ko_count}/{ko_threshold})"
            elif team_b_ko_loss:
                match_context["end_reason"] = f"Team B reached KO threshold ({team_b_ko_count}/{ko_threshold})"
            elif team_a_health_loss:
                match_context["end_reason"] = f"Team A health below threshold ({team_a_health:.1f}%/{health_threshold}%)"
            elif team_b_health_loss:
                match_context["end_reason"] = f"Team B health below threshold ({team_b_health:.1f}%/{health_threshold}%)"
            else:
                match_context["end_reason"] = "Unknown"
        
        return match_end
    
    def _calculate_match_result(self, team_a: List[Dict[str, Any]], team_b: List[Dict[str, Any]], 
                              match_context: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate match result
        
        Args:
            team_a: Team A characters
            team_b: Team B characters
            match_context: Match context
            
        Returns:
            dict: Match result
        """
        # Count individual wins for each team
        team_a_wins = 0
        team_b_wins = 0
        
        for char in team_a:
            if char.get("result") == "win":
                team_a_wins += 1
        
        for char in team_b:
            if char.get("result") == "win":
                team_b_wins += 1
        
        # Count KOs
        team_a_ko_count = sum(1 for char in team_a if char.get("is_ko", False))
        team_b_ko_count = sum(1 for char in team_b if char.get("is_ko", False))
        
        # Calculate team health
        team_a_health = sum(char.get("HP", 0) for char in team_a) / (len(team_a) * 100) * 100
        team_b_health = sum(char.get("HP", 0) for char in team_b) / (len(team_b) * 100) * 100
        
        # Determine winner
        winner = "Draw"
        winning_team = "None"
        
        if team_a_wins > team_b_wins:
            winner = "Team A"
            winning_team = match_context["team_a_name"]
        elif team_b_wins > team_a_wins:
            winner = "Team B"
            winning_team = match_context["team_b_name"]
        else:
            # If game wins tied, check KOs
            if team_a_ko_count < team_b_ko_count:
                winner = "Team A"
                winning_team = match_context["team_a_name"]
            elif team_b_ko_count < team_a_ko_count:
                winner = "Team B"
                winning_team = match_context["team_b_name"]
            else:
                # If KOs tied, check health
                if team_a_health > team_b_health:
                    winner = "Team A"
                    winning_team = match_context["team_a_name"]
                elif team_b_health > team_a_health:
                    winner = "Team B"
                    winning_team = match_context["team_b_name"]
        
        # Build result
        return {
            "team_a_id": match_context["team_a_id"],
            "team_b_id": match_context["team_b_id"],
            "team_a_name": match_context["team_a_name"],
            "team_b_name": match_context["team_b_name"],
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "team_a_ko_count": team_a_ko_count,
            "team_b_ko_count": team_b_ko_count,
            "team_a_health": team_a_health,
            "team_b_health": team_b_health,
            "winner": winner,
            "winning_team": winning_team,
            "end_reason": match_context.get("end_reason", "Match completed"),
            "character_results": []
        }
    
    def run_matchday(self, day_number: int = 1, lineup_file: Optional[str] = None, 
                    show_details: bool = True) -> List[Dict[str, Any]]:
        """Run all matches for a specific day
        
        Args:
            day_number: Day number to run
            lineup_file: Path to lineup file
            show_details: Whether to show detailed output
            
        Returns:
            list: List of match results
        """
        # Validate day
        if not CONFIG.is_valid_match_day(day_number):
            weekday = CONFIG.get_weekday_for_day(day_number)
            logger.error(f"Day {day_number} is not a valid match day (weekday {weekday})")
            raise ValueError(f"Day {day_number} is not a valid match day (weekday {weekday})")
        
        # Override lineup file if provided
        if lineup_file:
            CONFIG.paths["lineups_file"] = lineup_file
        
        # Get date
        match_date = CONFIG.get_date_for_day(day_number)
        
        if show_details:
            logger.info(f"Running matches for day {day_number} ({match_date})")
        
        # Load teams
        try:
            teams = DataLoader.load_lineups_from_excel(day_number)
        except Exception as e:
            logger.error(f"Error loading teams: {e}")
            raise
        
        # Load divisions
        try:
            team_divisions = DataLoader.load_divisions()
        except Exception as e:
            logger.error(f"Error loading divisions: {e}")
            raise
        
        # Create matchups
        try:
            matchups = DataLoader.get_matchups_for_day(day_number, team_divisions, teams)
        except Exception as e:
            logger.error(f"Error creating matchups: {e}")
            raise
        
        if show_details:
            logger.info(f"Running {len(matchups)} matchups:")
            for i, (team_a_id, team_b_id) in enumerate(matchups):
                team_a_name = teams[team_a_id][0]["team_name"]
                team_b_name = teams[team_b_id][0]["team_name"]
                logger.info(f"  {i+1}. {team_a_name} vs {team_b_name}")
        
        # Run simulations
        results = []
        
        for i, (team_a_id, team_b_id) in enumerate(matchups):
            if show_details:
                logger.info(f"Match {i+1}: {teams[team_a_id][0]['team_name']} vs {teams[team_b_id][0]['team_name']}")
            
            try:
                # Get active characters for each team
                team_a_active = [char for char in teams[team_a_id] if char.get("is_active", True)]
                team_b_active = [char for char in teams[team_b_id] if char.get("is_active", True)]
                
                # Ensure teams have exactly 8 active characters
                if len(team_a_active) != CONFIG.simulation["teams_per_match"]:
                    logger.warning(f"Team {team_a_id} has {len(team_a_active)} active characters, expected {CONFIG.simulation['teams_per_match']}")
                    
                    # Add or remove characters to match requirement
                    if len(team_a_active) < CONFIG.simulation["teams_per_match"]:
                        # Add inactive characters if needed
                        inactive = [char for char in teams[team_a_id] if not char.get("is_active", True)]
                        for char in inactive[:CONFIG.simulation["teams_per_match"] - len(team_a_active)]:
                            char["is_active"] = True
                            team_a_active.append(char)
                    else:
                        # Remove excess active characters
                        team_a_active = team_a_active[:CONFIG.simulation["teams_per_match"]]
                
                if len(team_b_active) != CONFIG.simulation["teams_per_match"]:
                    logger.warning(f"Team {team_b_id} has {len(team_b_active)} active characters, expected {CONFIG.simulation['teams_per_match']}")
                    
                    # Add or remove characters to match requirement
                    if len(team_b_active) < CONFIG.simulation["teams_per_match"]:
                        # Add inactive characters if needed
                        inactive = [char for char in teams[team_b_id] if not char.get("is_active", True)]
                        for char in inactive[:CONFIG.simulation["teams_per_match"] - len(team_b_active)]:
                            char["is_active"] = True
                            team_b_active.append(char)
                    else:
                        # Remove excess active characters
                        team_b_active = team_b_active[:CONFIG.simulation["teams_per_match"]]
                
                # Simulate match
                match_result = self.simulate_match(team_a_active, team_b_active, day_number, show_details=show_details)
                results.append(match_result)
                
                if show_details:
                    logger.info(f"  Result: {match_result['winning_team']} won ({match_result['team_a_wins']}-{match_result['team_b_wins']})")
            
            except Exception as e:
                logger.error(f"Error simulating match: {e}")
                # Continue with next match
        
        # Save match day results
        self._save_matchday_results(results, day_number, match_date)
        
        return results
    
    def _save_matchday_results(self, results: List[Dict[str, Any]], day_number: int, match_date: str) -> str:
        """Save match day results to file
        
        Args:
            results: List of match results
            day_number: Day number
            match_date: Match date
            
        Returns:
            str: Path to saved file
        """
        # Create output directory
        output_dir = CONFIG.paths["results_dir"]
        os.makedirs(output_dir, exist_ok=True)
        
        # Create filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"matchday_{day_number}_{timestamp}.json"
        file_path = os.path.join(output_dir, filename)
        
        # Create summary data
        summary = {
            "day": day_number,
            "date": match_date,
            "timestamp": timestamp,
            "matches": len(results),
            "results": []
        }
        
        # Add summarized results
        for result in results:
            summary["results"].append({
                "team_a_id": result["team_a_id"],
                "team_b_id": result["team_b_id"],
                "team_a_name": result["team_a_name"],
                "team_b_name": result["team_b_name"],
                "team_a_wins": result["team_a_wins"],
                "team_b_wins": result["team_b_wins"],
                "winner": result["winner"],
                "winning_team": result["winning_team"],
                "end_reason": result["end_reason"],
                "pgn_path": result.get("pgn_path", ""),
                "summary_path": result.get("summary_path", ""),
                "narrative_path": result.get("narrative_path", "")
            })
        
        # Save to file
        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Match day results saved to {file_path}")
        return file_path

#############################################################################
#                            MAIN EXECUTION                                 #
#############################################################################

def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description="META Fantasy League Simulator")
    parser.add_argument("--day", type=int, default=CONFIG.get_current_day(), help="Day number to simulate")
    parser.add_argument("--lineup", type=str, default=None, help="Path to lineup file")
    parser.add_argument("--config", type=str, default=None, help="Path to configuration file")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode (minimal output)")
    args = parser.parse_args()
    
    # Load custom configuration if provided
    if args.config:
        CONFIG = Config(args.config)
    
    try:
        # Initialize simulator
        simulator = MetaLeagueSimulator()
        
        # Run match day
        results = simulator.run_matchday(
            day_number=args.day,
            lineup_file=args.lineup,
            show_details=not args.quiet
        )
        
        # Print summary
        if not args.quiet:
            print(f"\nCompleted {len(results)} matches for day {args.day}")
            print(f"Results saved to {CONFIG.paths['results_dir']}")
    
    except Exception as e:
        logger.error(f"Error running simulator: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
    
    def _map_effect_type(self, effect_type: str) -> str:
        """Map trait effect types to standardized effects
        
        Args:
            effect_type: Original effect type
            
        Returns:
            str: Standardized effect type
        """
        # Map of formula keys to standardized effects
        effect_map = {
            "bonus_roll": "combat_bonus",
            "damage_reduction": "damage_reduction",
            "heal": "healing",
            "defense_bonus": "defense_bonus",
            "evasion": "evasion_bonus",
            "reroll": "reroll_dice",
            "trait_bonus": "trait_bonus"
        }
        
        return effect_map.get(effect_type, effect_type)
    
    def update_cooldowns(self, characters: List[Dict[str, Any]]) -> None:
        """Update trait cooldowns at end of round
        
        Args:
            characters: List of characters to update
        """
        for character in characters:
            if "trait_cooldowns" in character:
                # Reduce all cooldowns by 1
                for trait_id in list(character["trait_cooldowns"].keys()):
                    character["trait_cooldowns"][trait_id] -= 1
                    
                    # Remove expired cooldowns
                    if character["trait_cooldowns"][trait_id] <= 0:
                        del character["trait_cooldowns"][trait_id]
    
    def assign_traits_to_character(self, character: Dict[str, Any], division: str, role: str) -> List[str]:
        """Assign appropriate traits to a character based on division and role
        
        Args:
            character: Character to assign traits to
            division: Character's division ('o' or 'i')
            role: Character's role
            
        Returns:
            list: Assigned traits
        """
        # Define trait sets by division and role
        operations_traits = {
            "FL": ["tactical", "shield", "armor"],
            "VG": ["agile", "shield", "stretchy"],
            "EN": ["armor", "agile", "tactical"]
        }
        
        intelligence_traits = {
            "RG": ["genius", "agile", "spider-sense"],
            "GO": ["spider-sense", "agile", "stretchy"],
            "PO": ["genius", "spider-sense", "tactical"],
            "SV": ["genius", "tactical", "shield"]
        }
        
        # Get appropriate trait pool
        if division == "o":
            trait_pool = operations_traits.get(role, ["tactical", "armor"])
        else:
            trait_pool = intelligence_traits.get(role, ["genius", "spider-sense"])
        
        # Add healing trait based on DUR
        if character.get("aDUR", 5) >= 7:
            trait_pool.append("healing")
        
        # Select 2-3 traits based on character stats
        num_traits = min(3, max(2, (character.get("aOP", 5) + character.get("aAM", 5)) // 4))
        
        # Select random traits from pool
        selected_traits = random.sample(trait_pool, min(num_traits, len(trait_pool)))
        
        # Set traits on character
        character["traits"] = selected_traits
        
        return selected_traits