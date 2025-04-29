"""
Data Loader for META League Simulator
Handles loading teams, players, traits, and generating matchups
"""

import os
import json
import csv
import logging
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

class DataLoader:
    """Data loader for META League Simulator that handles all data file access"""
    
    def __init__(self, config):
        """Initialize the data loader"""
        self.config = config
        self.logger = logging.getLogger("DATA_LOADER")
        
        # Base data directory
        self.data_dir = config.get("paths.data_dir", "data")
        
        # Cache for loaded data
        self._teams_cache = None
        self._players_cache = None
        self._traits_cache = None
        self._divisions_cache = None
        self._matchups_cache = None
        self._player_traits_cache = None
        
        self.logger.info("Data loader initialized")
    
    def load_teams(self) -> Dict[str, Dict[str, Any]]:
        """Load team data from teams.csv"""
        if self._teams_cache is not None:
            return self._teams_cache
            
        teams_file = os.path.join(self.data_dir, "teams.csv")
        
        try:
            teams_data = {}
            with open(teams_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    team_id = row['team_id']
                    teams_data[team_id] = {
                        'team_name': row['team_name'],
                        'division': row['division'],
                        'coach_name': row['coach_name'],
                        'home_court_advantage': float(row['home_court_advantage'])
                    }
            
            self._teams_cache = teams_data
            self.logger.info(f"Loaded {len(teams_data)} teams")
            return teams_data
        except Exception as e:
            self.logger.error(f"Error loading teams: {e}")
            raise
    
    def load_players(self) -> Dict[str, Dict[str, Any]]:
        """Load player data from players.csv"""
        if self._players_cache is not None:
            return self._players_cache
            
        players_file = os.path.join(self.data_dir, "players.csv")
        
        try:
            players_data = {}
            with open(players_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_id = row['player_id']
                    players_data[player_id] = {
                        'id': player_id,
                        'name': row['name'],
                        'team_id': row['team_id'],
                        'role': row['role'],
                        'division': row['division'],
                        'base_HP': int(row['base_HP']),
                        'aSTR': int(row['aSTR']),
                        'aSPD': int(row['aSPD']),
                        'aFS': int(row['aFS']),
                        'aLDR': int(row['aLDR']),
                        'aDUR': int(row['aDUR']),
                        'aRES': int(row['aRES']),
                        'aWIL': int(row['aWIL']),
                        'HP': int(row['base_HP']),  # Initialize HP to base_HP
                        'stamina': 100,  # Initialize stamina
                        'morale': 100,  # Initialize morale
                        'is_active': True,
                        'is_ko': False,
                        'is_injured': False,
                        'injury_duration': 0,
                        'injury_type': None,
                        'traits': []  # Will be populated later
                    }
            
            self._players_cache = players_data
            self.logger.info(f"Loaded {len(players_data)} players")
            return players_data
        except Exception as e:
            self.logger.error(f"Error loading players: {e}")
            raise
    
    def load_traits(self) -> Dict[str, Dict[str, Any]]:
        """Load trait data from traits.csv"""
        if self._traits_cache is not None:
            return self._traits_cache
            
        traits_file = os.path.join(self.data_dir, "traits.csv")
        
        try:
            traits_data = {}
            with open(traits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    trait_id = row['trait_id']
                    traits_data[trait_id] = {
                        'id': trait_id,
                        'name': row['name'],
                        'type': row['type'],
                        'triggers': row['triggers'],
                        'formula_key': row['formula_key'],
                        'formula_expr': row['formula_expr'],
                        'bound_nbid': row['bound_nbid'],
                        'stamina_cost': int(row['stamina_cost']),
                        'cooldown': int(row['cooldown']) if row['cooldown'] else 0,
                        'description': row['description'],
                        'current_cooldown': 0  # Initialize cooldown
                    }
            
            self._traits_cache = traits_data
            self.logger.info(f"Loaded {len(traits_data)} traits")
            return traits_data
        except Exception as e:
            self.logger.error(f"Error loading traits: {e}")
            raise
    
    def load_divisions(self) -> Dict[str, Dict[str, Any]]:
        """Load division data from divisions.csv"""
        if self._divisions_cache is not None:
            return self._divisions_cache
            
        divisions_file = os.path.join(self.data_dir, "divisions.csv")
        
        try:
            divisions_data = {}
            with open(divisions_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    division_id = row['division_id']
                    divisions_data[row['division_name']] = {
                        'id': division_id,
                        'name': row['division_name'],
                        'bonus_type': row['bonus_type'],
                        'bonus_value': float(row['bonus_value'])
                    }
            
            self._divisions_cache = divisions_data
            self.logger.info(f"Loaded {len(divisions_data)} divisions")
            return divisions_data
        except Exception as e:
            self.logger.error(f"Error loading divisions: {e}")
            raise
    
    def load_player_traits(self) -> Dict[str, List[str]]:
        """Load player trait assignments from player_traits.csv"""
        if self._player_traits_cache is not None:
            return self._player_traits_cache
            
        player_traits_file = os.path.join(self.data_dir, "player_traits.csv")
        
        try:
            player_traits_data = {}
            with open(player_traits_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    player_id = row['player_id']
                    trait_ids = [trait_id.strip() for trait_id in row['trait_ids'].split(',')]
                    player_traits_data[player_id] = trait_ids
            
            self._player_traits_cache = player_traits_data
            self.logger.info(f"Loaded trait assignments for {len(player_traits_data)} players")
            return player_traits_data
        except Exception as e:
            self.logger.error(f"Error loading player traits: {e}")
            raise
    
    def load_matchups(self) -> Dict[int, List[Tuple[str, str]]]:
        """Load matchup data from matchups.csv"""
        if self._matchups_cache is not None:
            return self._matchups_cache
            
        matchups_file = os.path.join(self.data_dir, "matchups.csv")
        
        try:
            matchups_data = {}
            with open(matchups_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    day = int(row['day'])
                    if day not in matchups_data:
                        matchups_data[day] = []
                    
                    matchups_data[day].append((row['team_a_id'], row['team_b_id']))
            
            self._matchups_cache = matchups_data
            self.logger.info(f"Loaded matchups for {len(matchups_data)} days")
            return matchups_data
        except Exception as e:
            self.logger.error(f"Error loading matchups: {e}")
            raise
    
    def get_matchups(self, day_number: int, lineups: Dict[str, List[Dict[str, Any]]]) -> List[Tuple[str, str]]:
        """Get matchups for a specific day, validating against lineup data"""
        # Load predefined matchups if available
        all_matchups = self.load_matchups()
        
        if day_number in all_matchups:
            self.logger.info(f"Using predefined matchups for day {day_number}")
            return all_matchups[day_number]
        
        # If no predefined matchups, generate them based on division constraints
        self.logger.info(f"Generating matchups for day {day_number}")
        
        # Load teams if needed
        teams = self.load_teams()
        
        # Group teams by division
        teams_by_division = {}
        for team_id, team_data in teams.items():
            division = team_data["division"]
            if division not in teams_by_division:
                teams_by_division[division] = []
            teams_by_division[division].append(team_id)
        
        # Generate cross-division matchups
        matchups = []
        undercurrent_teams = teams_by_division.get("Undercurrent", [])
        overlay_teams = teams_by_division.get("Overlay", [])
        
        # Simple rotation pattern based on day number
        rotate_amount = (day_number - 1) % min(len(undercurrent_teams), len(overlay_teams))
        
        # Rotate one of the divisions
        rotated_overlay = overlay_teams[rotate_amount:] + overlay_teams[:rotate_amount]
        
        # Pair teams
        for i in range(min(len(undercurrent_teams), len(rotated_overlay))):
            if i < 5:  # Only generate 5 matchups per day
                # Home advantage alternates
                if day_number % 2 == 1:
                    matchups.append((undercurrent_teams[i], rotated_overlay[i]))
                else:
                    matchups.append((rotated_overlay[i], undercurrent_teams[i]))
        
        # Ensure we have exactly 5 matchups
        if len(matchups) != 5:
            self.logger.error(f"Generated {len(matchups)} matchups, expected 5")
            raise ValueError(f"Generated {len(matchups)} matchups, expected 5")
        
        return matchups
    
    def load_lineups(self, day_number: int) -> Dict[str, List[Dict[str, Any]]]:
        """Load lineup data for a specific day"""
        lineup_file = os.path.join(self.data_dir, f"lineups_day{day_number}.csv")
        
        # If day-specific lineup doesn't exist, fall back to previous day or default
        if not os.path.exists(lineup_file):
            # Try to find the latest available lineup file
            for prev_day in range(day_number - 1, 0, -1):
                prev_lineup_file = os.path.join(self.data_dir, f"lineups_day{prev_day}.csv")
                if os.path.exists(prev_lineup_file):
                    lineup_file = prev_lineup_file
                    self.logger.info(f"Using lineup from day {prev_day} for day {day_number}")
                    break
            else:
                # If no previous lineup found, use default
                default_lineup_file = os.path.join(self.data_dir, "lineups_day1.csv")
                if os.path.exists(default_lineup_file):
                    lineup_file = default_lineup_file
                    self.logger.info(f"Using default lineup for day {day_number}")
                else:
                    self.logger.error(f"No lineup data found for day {day_number}")
                    raise FileNotFoundError(f"No lineup data found for day {day_number}")
        
        # Load player and trait data
        players = self.load_players()
        traits = self.load_traits()
        player_traits = self.load_player_traits()
        
        # Read lineups
        lineups = {}
        try:
            with open(lineup_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    team_id = row['team_id']
                    player_ids = [pid.strip() for pid in row['player_ids'].split(',')]
                    
                    # Create lineup for this team
                    team_lineup = []
                    
                    for player_id in player_ids:
                        if player_id in players:
                            # Create a copy of player data with traits
                            player_data = players[player_id].copy()
                            
                            # Set HP to base HP at start of day
                            player_data['HP'] = player_data['base_HP']
                            
                            # Initialize other stats if needed
                            player_data.setdefault('stamina', 100)
                            player_data.setdefault('morale', 100)
                            
                            # Add traits
                            player_data['traits'] = []
                            if player_id in player_traits:
                                for trait_id in player_traits[player_id]:
                                    if trait_id in traits:
                                        trait_data = traits[trait_id].copy()
                                        trait_data['current_cooldown'] = 0  # Reset cooldown
                                        player_data['traits'].append(trait_data)
                            
                            team_lineup.append(player_data)
                    
                    # Ensure exactly 8 players per team (non-negotiable rule)
                    if len(team_lineup) < 8:
                        self.logger.error(f"Team {team_id} has only {len(team_lineup)} players, 8 required")
                        raise ValueError(f"Team {team_id} has only {len(team_lineup)} players, 8 required")
                    
                    lineups[team_id] = team_lineup
            
            self.logger.info(f"Loaded lineups for {len(lineups)} teams from {os.path.basename(lineup_file)}")
            return lineups
        except Exception as e:
            self.logger.error(f"Error loading lineups: {e}")
            raise
    
    def get_team_name(self, team_id: str) -> Optional[str]:
        """Get team name by ID"""
        teams = self.load_teams()
        if team_id in teams:
            return teams[team_id]['team_name']
        return None
    
    def get_team_division(self, team_id: str) -> Optional[str]:
        """Get team division by ID"""
        teams = self.load_teams()
        if team_id in teams:
            return teams[team_id]['division']
        return None
    
    def validate_data_integrity(self) -> bool:
        """Validate the integrity of all data files"""
        try:
            # Check all required files exist
            required_files = [
                os.path.join(self.data_dir, "teams.csv"),
                os.path.join(self.data_dir, "players.csv"),
                os.path.join(self.data_dir, "traits.csv"),
                os.path.join(self.data_dir, "divisions.csv"),
                os.path.join(self.data_dir, "player_traits.csv"),
                os.path.join(self.data_dir, "lineups_day1.csv")
            ]
            
            for file_path in required_files:
                if not os.path.exists(file_path):
                    self.logger.error(f"Required file missing: {file_path}")
                    return False
            
            # Load all data to check integrity
            teams = self.load_teams()
            players = self.load_players()
            traits = self.load_traits()
            divisions = self.load_divisions()
            player_traits = self.load_player_traits()
            
            # Check team divisions
            for team_id, team_data in teams.items():
                division = team_data['division']
                if division not in divisions:
                    self.logger.error(f"Team {team_id} has invalid division: {division}")
                    return False
            
            # Check player team assignments
            for player_id, player_data in players.items():
                team_id = player_data['team_id']
                if team_id not in teams:
                    self.logger.error(f"Player {player_id} assigned to non-existent team: {team_id}")
                    return False
            
            # Check player trait assignments
            for player_id, trait_ids in player_traits.items():
                if player_id not in players:
                    self.logger.error(f"Traits assigned to non-existent player: {player_id}")
                    return False
                
                for trait_id in trait_ids:
                    if trait_id not in traits:
                        self.logger.error(f"Player {player_id} has invalid trait: {trait_id}")
                        return False
            
            # Check default lineup
            day1_lineup = self.load_lineups(1)
            for team_id, lineup in day1_lineup.items():
                if team_id not in teams:
                    self.logger.error(f"Lineup contains non-existent team: {team_id}")
                    return False
                
                if len(lineup) != 8:
                    self.logger.error(f"Team {team_id} does not have exactly 8 players in lineup")
                    return False
            
            self.logger.info("Data integrity validation passed")
            return True
        except Exception as e:
            self.logger.error(f"Data integrity validation failed: {e}")
            return False