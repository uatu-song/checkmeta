"""
META Fantasy League Simulator - Core Simulator Patch
Fixes indentation issues and integrates configuration system
"""

# This patch should be applied to meta_simulator.py
# It fixes the indentation errors in the __init__ method and integrates the config module

# 1. Imports section - add this at the top
import os
import sys
import time
import json
import random
import datetime
import chess
import chess.pgn
import io
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

# Add new imports
from config import get_config, Config
from systems.initiative_randomizer import randomize_team_order
from systems.buffered_damage import BufferedDamageSystem
from systems.enhanced_field_leader import FieldLeaderEnhancer
from systems.loss_conditions import LossConditionSystem
from systems.convergence_balancer import ConvergenceBalancer
from systems.momentum_system import MomentumSystem

# Conditionally import SynergyTracker
try:
    from systems.synergy_tracker import SynergyTracker
    SYNERGY_AVAILABLE = True
except ImportError:
    SYNERGY_AVAILABLE = False

# 2. Replace the __init__ method with this fixed version
def __init__(self, stockfish_path=None, enable_advanced_features=True):
    """Initialize the META Fantasy League simulator
    
    Args:
        stockfish_path: Path to Stockfish executable
        enable_advanced_features: Whether to enable advanced features
    """
    # Load configuration
    self.config = get_config()
    
    # Core settings
    self.current_day = self.config.date["current_day"]
    self.MAX_MOVES = self.config.simulation["max_moves"]
    self.MAX_BATCH_SIZE = self.config.simulation["max_batch_size"]
    self.MAX_CONVERGENCES_PER_CHAR = self.config.simulation["max_convergences_per_char"]
    
    # Override stockfish path if provided
    self.stockfish_path = stockfish_path or self.config.paths["stockfish_path"]
    self.advanced_features_enabled = enable_advanced_features
    self.advanced_feature_manager = None
    
    if enable_advanced_features:
        self.activate_advanced_features()
    
    # Initialize core systems
    self.buffered_damage = BufferedDamageSystem(
        base_damage_reduction=self.config.simulation["base_damage_reduction"],
        max_damage_reduction=self.config.simulation["max_damage_reduction"],
        max_damage_per_hit=self.config.simulation["max_damage_per_hit"]
    )
    
    # Integrated tracking systems
    self.pgn_tracker = PGNTracker(output_dir=self.config.paths["pgn_dir"])
    self.stat_tracker = StatTracker()
    self.field_leader_enhancer = FieldLeaderEnhancer()
    self.loss_condition_system = LossConditionSystem()
    self.convergence_balancer = ConvergenceBalancer()
    self.momentum_system = MomentumSystem()
    
    # Initialize synergy tracker (stub in v3.2)
    self.synergy_tracker = None
    if SYNERGY_AVAILABLE:
        self.synergy_tracker = SynergyTracker()
    
    # Battle parameters from config
    self.DAMAGE_SCALING = self.config.simulation["damage_scaling"]
    self.BASE_DAMAGE_REDUCTION = self.config.simulation["base_damage_reduction"]
    self.MAX_DAMAGE_REDUCTION = self.config.simulation["max_damage_reduction"]
    self.MAX_DAMAGE_PER_HIT = self.config.simulation["max_damage_per_hit"]
    self.HP_REGEN_RATE = self.config.simulation["hp_regen_rate"]
    self.STAMINA_REGEN_RATE = self.config.simulation["stamina_regen_rate"]
    self.CRITICAL_THRESHOLD = self.config.simulation["critical_threshold"]
    
    # Trait definitions - load from config in future versions
    self.traits = self._create_trait_definitions()
    
    # Role-based openings from config
    self.role_openings = self.config.chess["role_openings"]
    
    print(f"Initialized META Fantasy League Simulator")
    print(f"Max moves: {self.MAX_MOVES}, Damage scaling: {self.DAMAGE_SCALING}")

# 3. Replace the activate_advanced_features method with this fixed version
def activate_advanced_features(self):
    """Activate all advanced features
    
    Returns:
        dict: Activation results
    """
    try:
        from systems.advanced_feature_manager import AdvancedFeatureManager
        self.advanced_feature_manager = AdvancedFeatureManager(self)
        return self.advanced_feature_manager.activate_all_features()
    except ImportError:
        print("Advanced features not available. Using standard systems.")
        return {"traits": False, "xp": False, "stockfish": False, "morale": False, "synergy": False}

# 4. Update the simulate_match method to use timestamps from config
# This is a partial update for the beginning of the method
def simulate_match(self, team_a, team_b, show_details=True):
    """
    Simulate a match between two teams with integrated batch processing
    
    Args:
        team_a: List of characters for team A
        team_b: List of characters for team B
        show_details: Whether to show detailed output
    
    Returns:
        dict: Match result data
    """
    # Create match context with timestamp from config
    timestamp = self.config.get_timestamp()
    
    match_context = {
        "timestamp": timestamp,
        "day": self.current_day,
        "team_a_id": team_a[0]["team_id"] if team_a else "unknown",
        "team_b_id": team_b[0]["team_id"] if team_b else "unknown",
        "team_a_name": team_a[0]["team_name"] if team_a else "Team A",
        "team_b_name": team_b[0]["team_name"] if team_b else "Team B",
        "round": 0,
        "trait_activations": [],
        "convergences": [],
        "damage_log": [],
        "synergy_activations": []  # Added for future synergy system
    }
    
    # Initialize synergy tracker if available
    if self.synergy_tracker:
        self.synergy_tracker = SynergyTracker(match_context)
    
    # Rest of the method remains unchanged...
    
# 5. Update the run_matchday method to use config for file operations
# This is a partial update focusing on the path handling
def run_matchday(self, day_number=None, lineup_file=None, show_details=True):
    """Run all matches for a specific day using real lineups
    
    Args:
        day_number: Day number (defaults to current_day in config)
        lineup_file: Path to lineup file (defaults to value in config)
        show_details: Whether to show detailed output
        
    Returns:
        List: Match results
    """
    # Use config values if not provided
    if day_number is None:
        day_number = self.config.date["current_day"]
    
    self.current_day = day_number
    
    if lineup_file is None:
        lineup_file = self.config.paths["default_lineup_file"]
    
    # Load team lineups
    print(f"Loading lineups from {lineup_file} for day {day_number}")
    try:
        teams = self.load_lineups_from_excel(lineup_file, f"{day_number}/7/25")
        print(f"Loaded {len(teams)} teams")
    except Exception as e:
        print(f"Error loading lineups: {e}")
        return []
    
    # Create matchups from config
    matchups = self.create_team_matchups(teams, day_number)
    print(f"Created {len(matchups)} matchups for day {day_number}")
    
    if not matchups:
        print("No valid matchups found. Check team IDs in lineup file.")
        return []
    
    # Run all matchups
    results = []
    
    # Rest of the method remains mostly unchanged...
    
    # Save day results with timestamped filename
    timestamp = self.config.get_timestamp()
    results_dir = self.config.paths["results_dir"]
    results_file = os.path.join(results_dir, f"day_{day_number}_results_{timestamp}.json")
    
    if results:
        # Ensure directory exists
        os.makedirs(os.path.dirname(results_file), exist_ok=True)
        
        try:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\nAll matches for day {day_number} completed")
            print(f"Results saved to {results_file}")
        except Exception as e:
            print(f"Error saving results: {e}")
            # Attempt backup save
            backup_file = os.path.join(results_dir, f"day_{day_number}_results_backup_{timestamp}.json")
            try:
                with open(backup_file, "w") as f:
                    json.dump(results, f, indent=2)
                print(f"Backup results saved to {backup_file}")
            except:
                print("Unable to save results")
    else:
        print(f"No valid match results to save")
    
    return results

# 6. Update the create_team_matchups method to use config
def create_team_matchups(self, teams, day_number=1, randomize=False):
    """Create balanced team matchups for simulation
    
    Args:
        teams: Dictionary of teams by team_id
        day_number: Day number for scheduling
        randomize: Whether to use random matchups
        
    Returns:
        List: List of matchups (team_a_id, team_b_id)
    """
    all_team_ids = list(teams.keys())
    print(f"Available teams: {all_team_ids}")
    
    if len(all_team_ids) < 2:
        print("Not enough teams for matchups (minimum 2 required)")
        return []
    
    if randomize:
        # Random matchups
        random.shuffle(all_team_ids)
        matchups = []
        for i in range(0, len(all_team_ids), 2):
            if i + 1 < len(all_team_ids):
                matchups.append((all_team_ids[i], all_team_ids[i+1]))
    else:
        # Get matchups from config
        config_matchups = self.config.get_matchups_for_day(day_number)
        
        if config_matchups:
            matchups = []
            for a, b in config_matchups:
                # Normalize team IDs
                a = a.lower()
                b = b.lower()
                
                # Only add matchup if both teams exist
                if any(a_id.lower() == a for a_id in all_team_ids) and any(b_id.lower() == b for b_id in all_team_ids):
                    # Find actual team IDs with correct case
                    actual_a = next((a_id for a_id in all_team_ids if a_id.lower() == a), a)
                    actual_b = next((b_id for b_id in all_team_ids if b_id.lower() == b), b)
                    matchups.append((actual_a, actual_b))
                else:
                    print(f"Skipping matchup {a} vs {b} as one or both teams don't exist")
        else:
            # Fall back to random matchups
            print(f"No predefined matchups for day {day_number}, using random matchups")
            random.shuffle(all_team_ids)
            matchups = []
            for i in range(0, len(all_team_ids), 2):
                if i + 1 < len(all_team_ids):
                    matchups.append((all_team_ids[i], all_team_ids[i+1]))
    
    print(f"Created {len(matchups)} matchups")
    return matchups

# 7. Update helper methods to use config
def _map_position_to_role(self, position):
    """Map position to standardized role code"""
    return self.config.map_position_to_role(position)

def _get_division_from_role(self, role):
    """Map role to division"""
    return self.config.get_division_from_role(role)