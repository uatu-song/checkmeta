#!/usr/bin/env python3
"""
META Simulator v4.2.1 Simple Monolith

This script creates a simple but complete monolith with enhanced PGN tracking
and stamina system integrated.
"""

import os
import sys
import shutil
import datetime
import json
import logging
import importlib.util

# Function to check if a file exists
def file_exists(path):
    return os.path.exists(path)

# Function to create enhanced PGN tracker
def create_enhanced_pgn_tracker():
    code = """
'''
Enhanced PGN Tracker for META Fantasy League simulations
'''

import os
import json
import datetime
import chess
import chess.pgn
import logging
from typing import Dict, List, Any, Optional, Tuple

class EnhancedPGNTracker:
    '''Enhanced PGN tracker for META Fantasy League simulations'''
    
    def __init__(self, config):
        '''Initialize the enhanced PGN tracker'''
        self.config = config
        self.logger = logging.getLogger("META_SIMULATOR.PGNTracker")
        
        # Get PGN generation options from config
        self.per_board_pgn = self.config.get("features.per_board_pgn", True)
        self.aggregate_match_pgn = self.config.get("features.aggregate_match_pgn", True)
        
        # Validate at least one format is enabled
        if not self.per_board_pgn and not self.aggregate_match_pgn:
            self.logger.warning("Both per_board_pgn and aggregate_match_pgn are disabled! Enabling per_board_pgn for backward compatibility.")
            self.per_board_pgn = True
        
        # Create PGN directory if it doesn't exist
        self.pgn_dir = self.config.get("paths.pgn_dir")
        os.makedirs(self.pgn_dir, exist_ok=True)
        
        self.logger.info(f"EnhancedPGNTracker initialized with per_board_pgn={self.per_board_pgn}, aggregate_match_pgn={self.aggregate_match_pgn}")
    
    def record_match_games(self, 
                           team_a: List[Dict[str, Any]], 
                           team_a_boards: List[chess.Board],
                           team_b: List[Dict[str, Any]], 
                           team_b_boards: List[chess.Board],
                           match_context: Dict[str, Any]) -> Tuple[str, str]:
        '''
        Record all games from a match in PGN format.
        
        Args:
            team_a: List of team A character dictionaries
            team_a_boards: List of chess boards for team A
            team_b: List of team B character dictionaries
            team_b_boards: List of chess boards for team B
            match_context: Match context dictionary
            
        Returns:
            Tuple[str, str]: Paths to PGN file and metadata file
        '''
        self.logger.info(f"Recording PGNs for match: {match_context['match_id']}")
        
        # Setup match metadata
        match_metadata = {
            "match_id": match_context["match_id"],
            "day": match_context["day"],
            "match_number": match_context["match_number"],
            "team_a_id": match_context["team_a_id"],
            "team_b_id": match_context["team_b_id"],
            "team_a_name": match_context["team_a_name"],
            "team_b_name": match_context["team_b_name"],
            "date": match_context["date"],
            "games": [],
            "convergence_logs": match_context.get("convergence_logs", []),
            "trait_logs": match_context.get("trait_logs", [])
        }
        
        # Store all games for possible aggregation
        all_game_pgns = []
        
        # Process each character's game
        for i, (char_a, board_a, char_b, board_b) in enumerate(
            zip(team_a, team_a_boards, team_b, team_b_boards)
        ):
            # Skip inactive characters
            if not char_a.get("is_active", True) or not char_b.get("is_active", True):
                continue
            
            # Create game index (1-based)
            game_idx = i + 1
            
            # Create game ID
            game_id = f"{match_context['match_id']}_game{game_idx}"
            
            try:
                # Generate PGN for this game
                pgn_text, game_metadata = self._generate_game_pgn(
                    game_id, board_a, char_a, char_b, match_context, game_idx
                )
                
                # Add to match metadata
                match_metadata["games"].append(game_metadata)
                
                # Save individual PGN if enabled
                individual_pgn_path = ""
                individual_metadata_path = ""
                
                if self.per_board_pgn:
                    individual_pgn_path, individual_metadata_path = self._save_individual_pgn(
                        game_id, pgn_text, game_metadata
                    )
                    self.logger.debug(f"Saved individual PGN for game {game_idx}: {individual_pgn_path}")
                
                # Store for possible aggregation
                all_game_pgns.append((game_id, pgn_text, game_metadata))
                
            except Exception as e:
                self.logger.error(f"Error generating PGN for game {game_idx}: {e}")
        
        # Save aggregated match PGN if enabled
        aggregated_pgn_path = ""
        aggregated_metadata_path = ""
        
        if self.aggregate_match_pgn and all_game_pgns:
            aggregated_pgn_path, aggregated_metadata_path = self._save_aggregated_pgn(
                match_context["match_id"], all_game_pgns, match_metadata
            )
            self.logger.info(f"Saved aggregated match PGN: {aggregated_pgn_path}")
        
        # Determine which paths to return based on configuration
        if self.aggregate_match_pgn:
            return aggregated_pgn_path, aggregated_metadata_path
        else:
            # For backward compatibility, return the first individual PGN
            if all_game_pgns:
                game_id, _, _ = all_game_pgns[0]
                return os.path.join(self.pgn_dir, f"{game_id}.pgn"), os.path.join(self.pgn_dir, f"{game_id}_metadata.json")
            else:
                return "", ""
    
    def _generate_game_pgn(self, 
                          game_id: str, 
                          board: chess.Board,
                          char_a: Dict[str, Any], 
                          char_b: Dict[str, Any],
                          match_context: Dict[str, Any],
                          game_idx: int) -> Tuple[str, Dict[str, Any]]:
        '''
        Generate PGN for a single game.
        
        Args:
            game_id: Game identifier
            board: Chess board with moves
            char_a: Character A dictionary
            char_b: Character B dictionary
            match_context: Match context dictionary
            game_idx: Game index (1-based)
            
        Returns:
            Tuple[str, Dict[str, Any]]: PGN text and game metadata
        '''
        # Create a new game from the board's move stack
        game = chess.pgn.Game()
        
        # Add headers
        game.headers["Event"] = f"META League Day {match_context['day']} Match {match_context['match_number']}"
        game.headers["Site"] = "META Fantasy League"
        game.headers["Date"] = datetime.datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = str(match_context.get("round", 1))
        game.headers["White"] = char_a.get("name", f"Player {char_a.get('id', 'Unknown')}")
        game.headers["Black"] = char_b.get("name", f"Player {char_b.get('id', 'Unknown')}")
        
        # Add game result
        result = "*"  # Default (game in progress)
        
        if board.is_checkmate():
            result = "1-0" if board.turn == chess.BLACK else "0-1"
        elif board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            result = "1/2-1/2"
            
        game.headers["Result"] = result
        
        # Add custom META headers
        game.headers["WhiteTeam"] = match_context["team_a_name"]
        game.headers["BlackTeam"] = match_context["team_b_name"]
        game.headers["WhiteID"] = char_a.get("id", "Unknown")
        game.headers["BlackID"] = char_b.get("id", "Unknown")
        game.headers["MatchID"] = match_context["match_id"]
        game.headers["GameIndex"] = str(game_idx)
        
        # Set up the moves from the board's move stack
        node = game
        for move in board.move_stack:
            node = node.add_variation(move)
        
        # Convert to PGN text
        pgn_text = str(game)
        
        # Create game metadata
        game_metadata = {
            "game_id": game_id,
            "white_id": char_a.get("id", "Unknown"),
            "white_name": char_a.get("name", "Unknown"),
            "black_id": char_b.get("id", "Unknown"),
            "black_name": char_b.get("name", "Unknown"),
            "result": result,
            "pgn_file": f"{game_id}.pgn",
            "metadata_file": f"{game_id}_metadata.json"
        }
        
        return pgn_text, game_metadata
    
    def _save_individual_pgn(self, 
                            game_id: str, 
                            pgn_text: str, 
                            game_metadata: Dict[str, Any]) -> Tuple[str, str]:
        '''
        Save an individual game PGN and metadata.
        
        Args:
            game_id: Game identifier
            pgn_text: PGN text to save
            game_metadata: Game metadata dictionary
            
        Returns:
            Tuple[str, str]: Paths to saved PGN and metadata files
        '''
        pgn_file = os.path.join(self.pgn_dir, f"{game_id}.pgn")
        metadata_file = os.path.join(self.pgn_dir, f"{game_id}_metadata.json")
        
        try:
            # Save PGN file
            with open(pgn_file, 'w') as f:
                f.write(pgn_text)
            
            # Save metadata file
            with open(metadata_file, 'w') as f:
                json.dump(game_metadata, f, indent=2)
            
            return pgn_file, metadata_file
        except Exception as e:
            self.logger.error(f"Error saving individual PGN for {game_id}: {e}")
            return "", ""
    
    def _save_aggregated_pgn(self, 
                            match_id: str, 
                            all_game_pgns: List[Tuple[str, str, Dict[str, Any]]], 
                            match_metadata: Dict[str, Any]) -> Tuple[str, str]:
        '''
        Save an aggregated match PGN and metadata.
        
        Args:
            match_id: Match identifier
            all_game_pgns: List of (game_id, pgn_text, game_metadata) tuples
            match_metadata: Match metadata dictionary
            
        Returns:
            Tuple[str, str]: Paths to saved aggregated PGN and metadata files
        '''
        aggregated_pgn_file = os.path.join(self.pgn_dir, f"{match_id}_combined.pgn")
        aggregated_metadata_file = os.path.join(self.pgn_dir, f"{match_id}_combined_metadata.json")
        
        try:
            # Create aggregated PGN content
            aggregated_pgn_content = ""
            
            for game_id, pgn_text, game_metadata in all_game_pgns:
                # Add a separator comment before each game
                aggregated_pgn_content += f"\n\n[{game_metadata['white_name']} vs {game_metadata['black_name']}]\n\n"
                aggregated_pgn_content += pgn_text
                aggregated_pgn_content += "\n\n"
            
            # Save aggregated PGN file
            with open(aggregated_pgn_file, 'w') as f:
                f.write(aggregated_pgn_content)
            
            # Update match metadata with path information
            match_metadata["aggregated_pgn_file"] = f"{match_id}_combined.pgn"
            match_metadata["aggregated_metadata_file"] = f"{match_id}_combined_metadata.json"
            
            # Save aggregated metadata file
            with open(aggregated_metadata_file, 'w') as f:
                json.dump(match_metadata, f, indent=2)
            
            return aggregated_pgn_file, aggregated_metadata_file
        except Exception as e:
            self.logger.error(f"Error saving aggregated PGN for {match_id}: {e}")
            return "", ""
"""
    return code

# Function to create stamina system
def create_stamina_system():
    code = """
'''
Stamina System for META Fantasy League simulations
'''

import os
import json
import logging
import math
import datetime
from typing import Dict, List, Any, Optional, Tuple, Union

class StaminaSystem:
    '''Stamina system for META Fantasy League simulations'''
    
    def __init__(self, config):
        '''Initialize the stamina system'''
        self.config = config
        self.logger = logging.getLogger("META_SIMULATOR.StaminaSystem")
        
        # Load stamina configuration
        self.stamina_decay_per_round_multiplier = self.config.get(
            "stamina_settings.stamina_decay_per_round_multiplier", 1.15)
        
        self.low_stamina_extra_damage_taken_percent = self.config.get(
            "stamina_settings.low_stamina_extra_damage_taken_percent", 20)
        
        self.base_stamina_value = self.config.get(
            "stamina_settings.base_stamina_value", 100)
        
        self.base_stamina_decay_per_round = self.config.get(
            "stamina_settings.base_stamina_decay_per_round", 5)
        
        self.base_stamina_recovery_per_day = self.config.get(
            "stamina_settings.base_stamina_recovery_per_day", 15)
        
        self.low_stamina_threshold = self.config.get(
            "stamina_settings.low_stamina_threshold", 35)
        
        # Storage for persistent stamina data
        self.stamina_data = {}
        self.stamina_history = {}
        
        # Load existing stamina data if available
        self._load_stamina_data()
        
        self.logger.info("StaminaSystem initialized successfully")
    
    def _load_stamina_data(self):
        '''Load existing stamina data from disk'''
        # Determine stamina data path
        data_dir = self.config.get("paths.data_dir")
        stamina_file = os.path.join(data_dir, "stamina_data.json")
        
        # Load if exists
        if os.path.exists(stamina_file):
            try:
                with open(stamina_file, 'r') as f:
                    data = json.load(f)
                    self.stamina_data = data.get("character_stamina", {})
                    self.stamina_history = data.get("stamina_history", {})
                self.logger.info(f"Loaded stamina data for {len(self.stamina_data)} characters")
            except Exception as e:
                self.logger.error(f"Error loading stamina data: {e}")
                # Initialize empty data
                self.stamina_data = {}
                self.stamina_history = {}
        else:
            self.logger.info("No existing stamina data found, starting fresh")
            self.stamina_data = {}
            self.stamina_history = {}
    
    def save_stamina_data(self):
        '''Save current stamina data to disk'''
        # Determine stamina data path
        data_dir = self.config.get("paths.data_dir")
        os.makedirs(data_dir, exist_ok=True)
        stamina_file = os.path.join(data_dir, "stamina_data.json")
        
        # Prepare data
        data = {
            "character_stamina": self.stamina_data,
            "stamina_history": self.stamina_history,
            "last_updated": datetime.datetime.now().isoformat()
        }
        
        # Save to file
        try:
            with open(stamina_file, 'w') as f:
                json.dump(data, f, indent=2)
            self.logger.info(f"Saved stamina data for {len(self.stamina_data)} characters")
        except Exception as e:
            self.logger.error(f"Error saving stamina data: {e}")
    
    def initialize_character_stamina(self, character: Dict[str, Any]) -> None:
        '''
        Initialize or reset a character's stamina if not already tracked.
        
        Args:
            character: Character dictionary
        '''
        char_id = character.get("id", "unknown")
        
        # Check if character already has stamina
        if char_id not in self.stamina_data:
            # Initialize with base value
            self.stamina_data[char_id] = {
                "current": self.base_stamina_value,
                "max": self.base_stamina_value,
                "last_updated": datetime.datetime.now().isoformat()
            }
            
            # Include character attributes that might affect stamina
            if "aDUR" in character:
                # Adjust max stamina based on Durability attribute
                durability_factor = character["aDUR"] / 100.0  # Normalize to 0-1 range
                stamina_bonus = math.floor(self.base_stamina_value * durability_factor * 0.5)  # Up to +50% base
                
                self.stamina_data[char_id]["max"] = self.base_stamina_value + stamina_bonus
                self.stamina_data[char_id]["current"] = self.stamina_data[char_id]["max"]
        
        # Set character's stamina value
        character["stamina"] = self.stamina_data[char_id]["current"]
        character["max_stamina"] = self.stamina_data[char_id]["max"]
        character["is_low_stamina"] = character["stamina"] < self.low_stamina_threshold
    
    def apply_stamina_decay(self, 
                           character: Dict[str, Any], 
                           decay_amount: Optional[float] = None,
                           match_context: Optional[Dict[str, Any]] = None) -> None:
        '''
        Apply stamina decay to a character.
        
        Args:
            character: Character dictionary
            decay_amount: Optional specific decay amount, otherwise uses base decay
            match_context: Optional match context for logging
        '''
        char_id = character.get("id", "unknown")
        
        # Skip if knocked out or inactive
        if character.get("is_ko", False) or not character.get("is_active", True):
            return
        
        # Verify character in stamina data
        if char_id not in self.stamina_data:
            self.initialize_character_stamina(character)
        
        # Calculate decay amount
        if decay_amount is None:
            # Calculate from base rates and multipliers
            decay_amount = self.base_stamina_decay_per_round * self.stamina_decay_per_round_multiplier
            
            # Apply trait modifiers if character has relevant traits
            if "traits" in character:
                for trait in character.get("traits", []):
                    if trait.get("type") == "stamina":
                        if trait.get("effect_type") == "decay_reduction":
                            reduction = trait.get("effect_value", 0)
                            decay_amount *= (1.0 - reduction)
        
        # Apply decay (ensure it doesn't go below 0)
        current_stamina = self.stamina_data[char_id]["current"]
        new_stamina = max(0, current_stamina - decay_amount)
        self.stamina_data[char_id]["current"] = new_stamina
        
        # Update character's stamina value
        character["stamina"] = new_stamina
        character["max_stamina"] = self.stamina_data[char_id]["max"]
        character["is_low_stamina"] = character["stamina"] < self.low_stamina_threshold
        
        # Log stamina decay
        self.logger.debug(f"Stamina decay for {char_id}: {current_stamina} -> {new_stamina}")
        
        # Record in history if match context provided
        if match_context:
            match_id = match_context.get("match_id", "unknown")
            
            if char_id not in self.stamina_history:
                self.stamina_history[char_id] = []
            
            self.stamina_history[char_id].append({
                "type": "decay",
                "match_id": match_id,
                "day": match_context.get("day", 0),
                "round": match_context.get("round", 0),
                "previous": current_stamina,
                "new": new_stamina,
                "timestamp": datetime.datetime.now().isoformat()
            })
    
    def apply_stamina_recovery(self, 
                              character: Dict[str, Any], 
                              recovery_amount: Optional[float] = None,
                              reason: str = "rest",
                              match_context: Optional[Dict[str, Any]] = None) -> None:
        '''
        Apply stamina recovery to a character.
        
        Args:
            character: Character dictionary
            recovery_amount: Optional specific recovery amount, otherwise uses base recovery
            reason: Reason for recovery ("rest", "trait", "item", etc.)
            match_context: Optional match context for logging
        '''
        char_id = character.get("id", "unknown")
        
        # Verify character in stamina data
        if char_id not in self.stamina_data:
            self.initialize_character_stamina(character)
        
        # Calculate recovery amount
        if recovery_amount is None:
            # Calculate from base rates
            recovery_amount = self.base_stamina_recovery_per_day
            
            # Apply trait modifiers if character has relevant traits
            if "traits" in character:
                for trait in character.get("traits", []):
                    if trait.get("type") == "stamina":
                        if trait.get("effect_type") == "recovery_boost":
                            boost = trait.get("effect_value", 0)
                            recovery_amount *= (1.0 + boost)
        
        # Apply recovery (ensure it doesn't exceed max)
        current_stamina = self.stamina_data[char_id]["current"]
        max_stamina = self.stamina_data[char_id]["max"]
        new_stamina = min(max_stamina, current_stamina + recovery_amount)
        self.stamina_data[char_id]["current"] = new_stamina
        
        # Update character's stamina value
        character["stamina"] = new_stamina
        character["max_stamina"] = max_stamina
        character["is_low_stamina"] = character["stamina"] < self.low_stamina_threshold
        
        # Log stamina recovery
        self.logger.debug(f"Stamina recovery for {char_id}: {current_stamina} -> {new_stamina} ({reason})")
        
        # Record in history if match context provided
        if match_context:
            match_id = match_context.get("match_id", "unknown")
            
            if char_id not in self.stamina_history:
                self.stamina_history[char_id] = []
            
            self.stamina_history[char_id].append({
                "type": "recovery",
                "reason": reason,
                "match_id": match_id,
                "day": match_context.get("day", 0),
                "round": match_context.get("round", 0),
                "previous": current_stamina,
                "new": new_stamina,
                "timestamp": datetime.datetime.now().isoformat()
            })
    
    def apply_end_of_round_recovery(self, 
                                   characters: List[Dict[str, Any]], 
                                   match_context: Dict[str, Any]) -> None:
        '''
        Apply end of round stamina effects to all characters.
        
        Args:
            characters: List of character dictionaries
            match_context: Match context dictionary
        '''
        for character in characters:
            # Skip knocked out or inactive characters
            if character.get("is_ko", False) or not character.get("is_active", True):
                continue
            
            # Apply stamina decay first
            self.apply_stamina_decay(character, match_context=match_context)
    
    def process_day_change(self, day_number: int) -> Dict[str, List[str]]:
        '''
        Process day change stamina recovery for all tracked characters.
        
        Args:
            day_number: Current day number
            
        Returns:
            Dict with lists of character IDs by recovery amount
        '''
        self.logger.info(f"Processing day change stamina recovery for day {day_number}")
        
        # Track characters by recovery groups
        result = {
            "full_recovery": [],
            "partial_recovery": [],
            "no_recovery": []
        }
        
        # Process each character
        for char_id, stamina_info in self.stamina_data.items():
            current_stamina = stamina_info["current"]
            max_stamina = stamina_info["max"]
            
            # Skip characters already at max
            if current_stamina >= max_stamina:
                result["full_recovery"].append(char_id)
                continue
            
            # Calculate recovery amount
            recovery_amount = self.base_stamina_recovery_per_day
            new_stamina = min(max_stamina, current_stamina + recovery_amount)
            
            # Apply recovery
            stamina_info["current"] = new_stamina
            
            # Record in appropriate category
            if new_stamina >= max_stamina:
                result["full_recovery"].append(char_id)
            else:
                result["partial_recovery"].append(char_id)
            
            # Record in history
            if char_id not in self.stamina_history:
                self.stamina_history[char_id] = []
            
            self.stamina_history[char_id].append({
                "type": "day_recovery",
                "day": day_number,
                "previous": current_stamina,
                "new": new_stamina,
                "timestamp": datetime.datetime.now().isoformat()
            })
        
        # Save updated data
        self.save_stamina_data()
        
        # Log summary
        self.logger.info(f"Day change stamina recovery complete: {len(result['full_recovery'])} full, "
                        f"{len(result['partial_recovery'])} partial")
        
        return result
    
    def calculate_stamina_damage_modifier(self, character: Dict[str, Any]) -> float:
        '''
        Calculate damage modifier based on stamina level.
        
        Args:
            character: Character dictionary
            
        Returns:
            Float damage modifier (1.0 = normal, >1.0 = more damage, <1.0 = less damage)
        '''
        # Skip if not tracking stamina
        if "stamina" not in character:
            return 1.0
        
        current_stamina = character["stamina"]
        
        # Check if below low stamina threshold
        if current_stamina < self.low_stamina_threshold:
            # Calculate how far below threshold (as percentage)
            threshold_diff = self.low_stamina_threshold - current_stamina
            threshold_pct = threshold_diff / self.low_stamina_threshold
            
            # Apply damage increase (up to low_stamina_extra_damage_taken_percent)
            extra_damage_pct = threshold_pct * self.low_stamina_extra_damage_taken_percent / 100.0
            return 1.0 + extra_damage_pct
        
        return 1.0
"""
    return code

# Function to create config settings
def create_config_settings():
    settings = """
# Add these settings to your configuration file

"features": {
    "per_board_pgn": True,      # Generate individual PGN files per board
    "aggregate_match_pgn": True, # Generate aggregated match PGN file
    "stamina_enabled": True      # Enable stamina system
},
"stamina_settings": {
    "stamina_decay_per_round_multiplier": 1.15,
    "low_stamina_extra_damage_taken_percent": 20,
    "base_stamina_value": 100,
    "base_stamina_decay_per_round": 5,
    "base_stamina_recovery_per_day": 15,
    "low_stamina_threshold": 35
}
"""
    return settings

# Function to create integration instructions
def create_integration_instructions():
    instructions = """
# META Simulator v4.2.1 Integration Guide

## 1. Add Enhanced PGN Tracker

1. Make sure `enhanced_pgn_tracker.py` is in your project directory
2. Find where your PGN tracker is initialized (search for `PGNTracker`)
3. Replace with:
   
```python
# Initialize PGN tracker with enhanced version
from enhanced_pgn_tracker import EnhancedPGNTracker
pgn_tracker = EnhancedPGNTracker(self.config)
self.registry.register("pgn_tracker", pgn_tracker)
```

## 2. Add Stamina System 

1. Make sure `stamina_system.py` is in your project directory
2. Find where your subsystems are initialized
3. Add:

```python
# Initialize stamina system
from stamina_system import StaminaSystem
if self.config.get("features.stamina_enabled", True):
    stamina_system = StaminaSystem(self.config)
    self.registry.register("stamina_system", stamina_system)
```

## 3. Add Stamina Integration to Match Simulation

1. Find where characters are prepared for a match
2. Add character stamina initialization:

```python
# Initialize character stamina
if self.config.get("features.stamina_enabled", True):
    stamina_system = self.registry.get("stamina_system")
    if stamina_system:
        for char in team_a_active + team_b_active:
            stamina_system.initialize_character_stamina(char)
```

3. Add stamina effects to end of round processing:

```python
# Apply stamina round effects
if self.config.get("features.stamina_enabled", True):
    stamina_system = self.registry.get("stamina_system")
    if stamina_system:
        stamina_system.apply_end_of_round_recovery(
            team_a_active + team_b_active,
            match_context
        )
```

## 4. Add Stamina Recovery to Day Simulation

1. Find the day simulation method
2. Add:

```python
# Process stamina recovery
if self.config.get("features.stamina_enabled", True):
    stamina_system = self.registry.get("stamina_system")
    if stamina_system:
        stamina_report = stamina_system.process_day_change(day_number)
```

## 5. Add Stamina Data Persistence

1. Find where you save persistent data
2. Add:

```python
# Save stamina data
stamina_system = self.registry.get("stamina_system")
if stamina_system and hasattr(stamina_system, "save_stamina_data"):
    stamina_system.save_stamina_data()
```

## 6. Add Stamina Combat Effects

1. Find where damage is calculated
2. Add:

```python
# Apply stamina modifier
if self.config.get("features.stamina_enabled", True):
    stamina_system = self.registry.get("stamina_system")
    if stamina_system and defender:
        stamina_modifier = stamina_system.calculate_stamina_damage_modifier(defender)
        damage *= stamina_modifier
```

## 7. Update Configuration

Make sure your configuration includes:

```python
"features": {
    "per_board_pgn": True,
    "aggregate_match_pgn": True,
    "stamina_enabled": True
},
"stamina_settings": {
    "stamina_decay_per_round_multiplier": 1.15,
    "low_stamina_extra_damage_taken_percent": 20,
    "base_stamina_value": 100,
    "base_stamina_decay_per_round": 5,
    "base_stamina_recovery_per_day": 15,
    "low_stamina_threshold": 35
}
```
"""
    return instructions

def main():
    """Create the necessary files for META Simulator v4.2.1"""
    print("META Simulator v4.2.1 Simple Integration")
    print("---------------------------------------")
    
    # Create the enhanced PGN tracker file
    pgn_file = "enhanced_pgn_tracker.py"
    if not file_exists(pgn_file):
        with open(pgn_file, 'w') as f:
            f.write(create_enhanced_pgn_tracker())
        print(f"✓ Created {pgn_file}")
    else:
        print(f"! {pgn_file} already exists, skipping")
    
    # Create the stamina system file
    stamina_file = "stamina_system.py"
    if not file_exists(stamina_file):
        with open(stamina_file, 'w') as f:
            f.write(create_stamina_system())
        print(f"✓ Created {stamina_file}")
    else:
        print(f"! {stamina_file} already exists, skipping")
    
    # Create configuration settings file
    config_file = "v4.2.1_config_settings.txt"
    with open(config_file, 'w') as f:
        f.write(create_config_settings())
    print(f"✓ Created {config_file}")
    
    # Create integration instructions
    instructions_file = "integration_instructions.txt"
    with open(instructions_file, 'w') as f:
        f.write(create_integration_instructions())
    print(f"✓ Created {instructions_file}")
    
    print("\nDone! Follow the integration instructions to complete the setup.")

if __name__ == "__main__":
    main()