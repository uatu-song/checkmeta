"""
META Fantasy League Simulator v5.0
Enhanced simulation engine for META League matches with advanced statistics and tracking

Major improvements:
- PGN Generation Fix: Support for both individual per-board PGNs and aggregated match PGNs
- Robust Stamina System: Comprehensive stamina tracking that persists across matches
- Combat Calibration: Enhanced combat mechanics following calibration plan
- Enhanced Trait System: Improved trait activation and effects
- Unified Data Architecture: Consistent data loading and validation
"""

import os
import sys
import time
import json
import random
import datetime
import logging
import math
import chess
import chess.pgn
import chess.engine
import pandas as pd
import traceback
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

# System base imports
from system_base import SystemBase
from system_registry import SystemRegistry
from config_manager import ConfigurationManager

class MetaLeagueSimulatorV5:
    """Main simulator class for META Fantasy League simulations v5.0"""
    
    VERSION = "5.0.0"
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the simulator v5.0"""
        # Create banner
        self._print_banner()
        
        # Create configuration
        self.config = ConfigurationManager(config_file)
        
        # Set up logging
        self._setup_logging()
        
        # Create registry
        self.registry = SystemRegistry()
        
        # Validate system integrity
        if not self._validate_system_integrity():
            raise RuntimeError("System validation failed. Fix errors before continuing.")
        
        # Initialize subsystems
        self._initialize_subsystems()
        
        # Apply combat calibration if enabled
        if self.config.get("features.combat_calibration_enabled", True):
            self._apply_combat_calibration()
        
        self.logger.info(f"META Fantasy League Simulator v{self.VERSION} initialized successfully")
    
    def _print_banner(self):
        """Print simulator banner"""
        banner = f"""
╔═══════════════════════════════════════════════════════╗
║                                                       ║
║   ███╗   ███╗███████╗████████╗ █████╗     ██╗  ██╗   ║
║   ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗   ██║  ██║   ║
║   ██╔████╔██║█████╗     ██║   ███████║   ██║  ██║   ║
║   ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║   ╚██╗██╔╝   ║
║   ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║    ╚███╔╝    ║
║                                          v{self.VERSION}      ║
║                                                      ║
║   Fantasy League Simulator                           ║
╚══════════════════════════════════════════════════════╝
        """
        print(banner)
    
    def _setup_logging(self):
        """Set up logging system"""
        log_dir = self.config.get("paths.logs_dir")
        os.makedirs(log_dir, exist_ok=True)
        
        log_level_name = self.config.get("logging.level", "INFO")
        log_level = getattr(logging, log_level_name)
        
        log_file = os.path.join(
            log_dir, 
            f"meta_simulator_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        
        logging.basicConfig(
            level=log_level,
            format=self.config.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("META_SIMULATOR")
        self.logger.info(f"Logging initialized at level {log_level_name}")
    
    def _validate_system_integrity(self):
        """Validate system integrity before starting"""
        # Initialize the gatekeeper and data loader first for validation
        from gatekeeper import Gatekeeper
        from data_loader import DataLoader
        
        data_loader = DataLoader(self.config)
        
        # Register in registry
        self.registry.register("data_loader", data_loader)
        
        # Create and run gatekeeper
        gatekeeper = Gatekeeper(self.config, data_loader)
        
        # Register in registry
        self.registry.register("gatekeeper", gatekeeper)
        
        # Run validation
        validity = gatekeeper.run_all_checks()
        
        if validity:
            self.logger.info("System validation passed")
        else:
            self.logger.error("System validation failed")
            
        return validity
    
    def _initialize_subsystems(self):
        """Initialize all simulation subsystems"""
        self.logger.info("Initializing subsystems...")
        
        # Initialize data loader (already done in validation)
        data_loader = self.registry.get("data_loader")
        
        # Initialize trait system with enhanced version
        from enhanced_trait_loader import EnhancedTraitSystem
        trait_system = EnhancedTraitSystem(self.config)
        self.registry.register("trait_system", trait_system)
        
        # Initialize chess system
        from chess_system import ChessSystem
        chess_system = ChessSystem(self.config)
        self.registry.register("chess_system", chess_system)
        
        # Initialize combat system
        from combat_system import CombatSystem
        combat_system = CombatSystem(self.config, trait_system)
        self.registry.register("combat_system", combat_system)
        
        # Initialize convergence system
        from convergence_system import ConvergenceSystem
        convergence_system = ConvergenceSystem(self.config, trait_system, combat_system)
        self.registry.register("convergence_system", convergence_system)
        
        # Initialize stamina system - always enabled in v5.0
        from stamina_system import StaminaSystem
        stamina_system = StaminaSystem(self.config)
        self.registry.register("stamina_system", stamina_system)
        self.logger.info("Stamina system initialized")
        
        # Initialize injury system - always enabled in v5.0
        from injury_system import InjurySystem
        injury_system = InjurySystem(self.config)
        self.registry.register("injury_system", injury_system)
        self.logger.info("Injury system initialized")
        
        # Initialize PGN tracker with enhanced version
        from enhanced_pgn_tracker import EnhancedPGNTracker
        pgn_tracker = EnhancedPGNTracker(self.config)
        self.registry.register("pgn_tracker", pgn_tracker)
        self.logger.info(f"Enhanced PGN tracker initialized with per_board_pgn={self.config.get('features.per_board_pgn', True)}, aggregate_match_pgn={self.config.get('features.aggregate_match_pgn', True)}")
        
        # Initialize stat tracker with enhanced version
        from enhanced_stats_system import EnhancedStatTracker
        stat_tracker = EnhancedStatTracker(self.config)
        self.registry.register("stat_tracker", stat_tracker)
        
        # Initialize match visualizer
        from match_visualizer import MatchVisualizer
        match_visualizer = MatchVisualizer(self.config)
        self.registry.register("match_visualizer", match_visualizer)
        
        # Initialize XP system
        from xp_system import XPSystem
        xp_system = XPSystem(self.config)
        self.registry.register("xp_system", xp_system)
        self.logger.info("XP system initialized")
        
        # Initialize synergy system
        from synergy_system import SynergySystem
        synergy_system = SynergySystem(self.config)
        self.registry.register("synergy_system", synergy_system)
        self.logger.info("Synergy system initialized")
        
        # Initialize morale system
        from morale_system import MoraleSystem
        morale_system = MoraleSystem(self.config)
        self.registry.register("morale_system", morale_system)
        self.logger.info("Morale system initialized")
        
        # Activate all systems
        for system_name in self.registry.get_all_systems():
            self.registry.activate(system_name)
            
        self.logger.info("All subsystems initialized and activated")
    
    def _apply_combat_calibration(self):
        """Apply combat calibration settings from the configuration"""
        self.logger.info("Applying combat calibration settings...")
        
        # Default combat calibration settings if not in config
        combat_defaults = {
            "health_settings": {
                "base_hp_multiplier": 1.0
            },
            "damage_settings": {
                "base_damage_multiplier": 1.25
            },
            "stamina_settings": {
                "stamina_decay_per_round_multiplier": 1.15,
                "low_stamina_extra_damage_taken_percent": 20
            },
            "morale_settings": {
                "morale_loss_per_ko_multiplier": 1.10,
                "morale_collapse_enabled": True,
                "morale_collapse_threshold_percent": 30
            },
            "convergence_settings": {
                "convergence_damage_multiplier": 2.0
            },
            "injury_settings": {
                "injury_enabled": True,
                "injury_trigger_stamina_threshold_percent": 35
            }
        }
        
        # Get calibration settings from config or use defaults
        combat_settings = self.config.get("combat_calibration", combat_defaults)
        
        # Apply settings to respective systems
        
        # Apply to combat system
        combat_system = self.registry.get("combat_system")
        if combat_system:
            combat_system.set_hp_multiplier(combat_settings["health_settings"]["base_hp_multiplier"])
            combat_system.set_damage_multiplier(combat_settings["damage_settings"]["base_damage_multiplier"])
            
        # Apply to stamina system
        stamina_system = self.registry.get("stamina_system")
        if stamina_system:
            stamina_system.set_decay_multiplier(combat_settings["stamina_settings"]["stamina_decay_per_round_multiplier"])
            stamina_system.set_low_stamina_damage_percent(combat_settings["stamina_settings"]["low_stamina_extra_damage_taken_percent"])
            
        # Apply to morale system
        morale_system = self.registry.get("morale_system")
        if morale_system:
            morale_system.set_ko_loss_multiplier(combat_settings["morale_settings"]["morale_loss_per_ko_multiplier"])
            morale_system.set_collapse_enabled(combat_settings["morale_settings"]["morale_collapse_enabled"])
            morale_system.set_collapse_threshold(combat_settings["morale_settings"]["morale_collapse_threshold_percent"])
            
        # Apply to convergence system
        convergence_system = self.registry.get("convergence_system")
        if convergence_system:
            convergence_system.set_damage_multiplier(combat_settings["convergence_settings"]["convergence_damage_multiplier"])
            
        # Apply to injury system
        injury_system = self.registry.get("injury_system")
        if injury_system:
            injury_system.set_enabled(combat_settings["injury_settings"]["injury_enabled"])
            injury_system.set_stamina_threshold(combat_settings["injury_settings"]["injury_trigger_stamina_threshold_percent"])
            
        self.logger.info("Combat calibration settings applied successfully")
    
    def simulate_match(self, team_a: List[Dict[str, Any]], team_b: List[Dict[str, Any]], 
                      day_number: int = 1, match_number: int = 1, 
                      show_details: bool = True) -> Dict[str, Any]:
        """Simulate a match between two teams"""
        self.logger.info(f"Starting match simulation - Day {day_number}, Match {match_number}")
        
        # Validate teams
        if not team_a or not team_b:
            raise ValueError("Both teams must have characters")
        
        players_per_team = 8  # Non-negotiable rule: 8v8 Team Lineups
        
        # Extract active characters only
        team_a_active = [char for char in team_a if char.get("is_active", True)][:players_per_team]
        team_b_active = [char for char in team_b if char.get("is_active", True)][:players_per_team]
        
        # Check team sizes
        if len(team_a_active) < players_per_team or len(team_b_active) < players_per_team:
            self.logger.warning(f"Team sizes are less than required {players_per_team}. Team A: {len(team_a_active)}, Team B: {len(team_b_active)}")
            # Do not proceed if team sizes are incorrect - non-negotiable rule
            if len(team_a_active) < players_per_team:
                raise ValueError(f"Team A has {len(team_a_active)} active players but {players_per_team} are required")
            if len(team_b_active) < players_per_team:
                raise ValueError(f"Team B has {len(team_b_active)} active players but {players_per_team} are required")
        
        # Get team IDs and names
        team_a_id = team_a_active[0].get("team_id", "unknown") if team_a_active else "unknown"
        team_b_id = team_b_active[0].get("team_id", "unknown") if team_b_active else "unknown"
        
        data_loader = self.registry.get("data_loader")
        team_a_name = data_loader.get_team_name(team_a_id) or f"Team {team_a_id[1:]}" if team_a_id.startswith('t') else team_a_id
        team_b_name = data_loader.get_team_name(team_b_id) or f"Team {team_b_id[1:]}" if team_b_id.startswith('t') else team_b_id
        
        # Check division constraints
        division_a = data_loader.get_team_division(team_a_id)
        division_b = data_loader.get_team_division(team_b_id)
        
        if division_a == division_b:
            raise ValueError(f"Teams from the same division cannot play each other (both in {division_a})")
        
        # Create match context
        match_context = {
            "match_id": f"day{day_number}_match{match_number}_{team_a_id}_vs_{team_b_id}",
            "day": day_number,
            "match_number": match_number,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_division": division_a,
            "team_b_division": division_b,
            "date": datetime.datetime.now().isoformat(),
            "round": 1,
            "trait_logs": [],
            "convergence_logs": [],
            "stamina_logs": [],
            "morale_logs": []
        }
        
        # Initialize stamina for all characters
        stamina_system = self.registry.get("stamina_system")
        if stamina_system:
            for char in team_a_active + team_b_active:
                stamina_system.initialize_character_stamina(char)
        
        # Apply injuries
        injury_system = self.registry.get("injury_system")
        if injury_system:
            for char in team_a_active + team_b_active:
                injury_system.apply_injuries_to_character(char)
        
        # Register characters with stat tracker
        stat_tracker = self.registry.get("stat_tracker")
        if stat_tracker:
            for char in team_a_active + team_b_active:
                stat_tracker.register_character(char)
        
        # Set up chess boards
        chess_system = self.registry.get("chess_system")
        team_a_boards = [chess_system.create_board() for _ in range(len(team_a_active))]
        team_b_boards = [chess_system.create_board() for _ in range(len(team_b_active))]
        
        # Apply home advantage based on day number (even days: team_a is home, odd days: team_b is home)
        # Non-negotiable rule: Alternate Home/Away
        is_home_day_a = day_number % 2 == 0
        if is_home_day_a:
            # Even day: team_a is home
            self._apply_home_advantage(team_a_active)
            self.logger.info(f"Home advantage applied to {team_a_name}")
        else:
            # Odd day: team_b is home
            self._apply_home_advantage(team_b_active)
            self.logger.info(f"Home advantage applied to {team_b_name}")
        
        # Apply team synergies
        synergy_system = self.registry.get("synergy_system")
        if synergy_system:
            synergy_system.apply_team_synergies(team_a_active, team_a_id)
            synergy_system.apply_team_synergies(team_b_active, team_b_id)
        
        # Main simulation loop
        max_rounds = self.config.get("simulation.max_rounds", 30)
        match_complete = False
        round_number = 1
        
        if show_details:
            print(f"\n=== MATCH: {team_a_name} vs {team_b_name} ===")
        
        self.logger.info(f"Starting match: {team_a_name} vs {team_b_name}")
        
        while not match_complete and round_number <= max_rounds:
            if show_details and round_number % 5 == 1:
                print(f"\n-- Round {round_number} --")
                
            self.logger.info(f"Round {round_number}")
            match_context["round"] = round_number
            
            # Simulate chess moves for each character
            self._simulate_chess_round(
                team_a_active, team_a_boards, 
                team_b_active, team_b_boards,
                match_context
            )
            
            # Process convergences
            self._process_convergences(
                team_a_active, team_a_boards,
                team_b_active, team_b_boards, 
                match_context
            )
            
            # Apply end of round effects
            self._apply_end_of_round_effects(
                team_a_active + team_b_active,
                match_context
            )
            
            # Check if match is complete
            team_a_ko_count = sum(1 for char in team_a_active if char.get("is_ko", False))
            team_b_ko_count = sum(1 for char in team_b_active if char.get("is_ko", False))
            
            ko_threshold = self.config.get("simulation.ko_threshold", 4)
            
            if team_a_ko_count >= ko_threshold or team_b_ko_count >= ko_threshold:
                match_complete = True
                self.logger.info(f"Match complete by KO threshold: A={team_a_ko_count}, B={team_b_ko_count}")
                
                if show_details:
                    if team_a_ko_count >= ko_threshold:
                        print(f"\n{team_a_name} has been defeated!")
                    if team_b_ko_count >= ko_threshold:
                        print(f"\n{team_b_name} has been defeated!")
            
            # Check for team HP threshold
            team_a_hp_pct = sum(char.get("HP", 0) for char in team_a_active) / (len(team_a_active) * 100) * 100
            team_b_hp_pct = sum(char.get("HP", 0) for char in team_b_active) / (len(team_b_active) * 100) * 100
            
            team_hp_threshold = self.config.get("simulation.team_hp_threshold", 30)
            
            if team_a_hp_pct < team_hp_threshold or team_b_hp_pct < team_hp_threshold:
                match_complete = True
                self.logger.info(f"Match complete by HP threshold: A={team_a_hp_pct:.1f}%, B={team_b_hp_pct:.1f}%")
                
                if show_details:
                    if team_a_hp_pct < team_hp_threshold:
                        print(f"\n{team_a_name} has been defeated by HP threshold!")
                    if team_b_hp_pct < team_hp_threshold:
                        print(f"\n{team_b_name} has been defeated by HP threshold!")
            
            # Check morale collapse (new in v5.0)
            morale_system = self.registry.get("morale_system")
            if morale_system and morale_system.is_collapse_enabled():
                team_a_morale_collapse = morale_system.check_team_morale_collapse(team_a_active)
                team_b_morale_collapse = morale_system.check_team_morale_collapse(team_b_active)
                
                if team_a_morale_collapse or team_b_morale_collapse:
                    match_complete = True
                    self.logger.info(f"Match complete by morale collapse: A={team_a_morale_collapse}, B={team_b_morale_collapse}")
                    
                    if show_details:
                        if team_a_morale_collapse:
                            print(f"\n{team_a_name} morale has collapsed!")
                        if team_b_morale_collapse:
                            print(f"\n{team_b_name} morale has collapsed!")
            
            # Increment round
            round_number += 1
        
        # Determine match result
        team_a_wins = 0
        team_b_wins = 0
        
        # Count chess results
        for char, board in zip(team_a_active, team_a_boards):
            if board.is_game_over():
                if board.is_checkmate():
                    if board.turn == chess.BLACK:  # White won (team A)
                        team_a_wins += 1
                        char["result"] = "win"
                    else:  # Black won (opponent)
                        team_b_wins += 1
                        char["result"] = "loss"
                elif board.is_stalemate() or board.is_insufficient_material():
                    # Draw counts as half point for each team
                    team_a_wins += 0.5
                    team_b_wins += 0.5
                    char["result"] = "draw"
            elif not char.get("is_ko", False):
                # Not KO'd and game not over - count as active
                char["result"] = "active"
        
        for char, board in zip(team_b_active, team_b_boards):
            if board.is_game_over():
                if board.is_checkmate():
                    if board.turn == chess.BLACK:  # White won (team B)
                        team_b_wins += 1
                        char["result"] = "win"
                    else:  # Black won (opponent)
                        team_a_wins += 1
                        char["result"] = "loss"
                elif board.is_stalemate() or board.is_insufficient_material():
                    # Draw counts as half point for each team
                    team_a_wins += 0.5
                    team_b_wins += 0.5
                    char["result"] = "draw"
            elif not char.get("is_ko", False):
                # Not KO'd and game not over - count as active
                char["result"] = "active"
        
        # Determine match outcome based on all factors
        if team_a_ko_count >= ko_threshold:
            match_result = "loss"
            winning_team = team_b_name
            losing_team = team_a_name
        elif team_b_ko_count >= ko_threshold:
            match_result = "win"
            winning_team = team_a_name
            losing_team = team_b_name
        elif team_a_hp_pct < team_hp_threshold:
            match_result = "loss"
            winning_team = team_b_name
            losing_team = team_a_name
        elif team_b_hp_pct < team_hp_threshold:
            match_result = "win" 
            winning_team = team_a_name
            losing_team = team_b_name
        elif morale_system and morale_system.is_collapse_enabled():
            if morale_system.check_team_morale_collapse(team_a_active):
                match_result = "loss"
                winning_team = team_b_name
                losing_team = team_a_name
            elif morale_system.check_team_morale_collapse(team_b_active):
                match_result = "win"
                winning_team = team_a_name
                losing_team = team_b_name
            elif team_a_wins > team_b_wins:
                match_result = "win"
                winning_team = team_a_name
                losing_team = team_b_name
            elif team_b_wins > team_a_wins:
                match_result = "loss"
                winning_team = team_b_name
                losing_team = team_a_name
            else:
                # In case of tie
                match_result = "draw"
                winning_team = "Draw"
                losing_team = "Draw"
        else:
            # Otherwise compare wins
            if team_a_wins > team_b_wins:
                match_result = "win"
                winning_team = team_a_name
                losing_team = team_b_name
            elif team_b_wins > team_a_wins:
                match_result = "loss"
                winning_team = team_b_name
                losing_team = team_a_name
            else:
                # In case of tie
                match_result = "draw"
                winning_team = "Draw"
                losing_team = "Draw"
        
        if show_details:
            print(f"\nFinal score: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}")
            print(f"Winner: {winning_team}")
        
        self.logger.info(f"Match result: {winning_team} wins {team_a_wins}-{team_b_wins}")
        
        # Record match results
        for char in team_a_active:
            # Record result in stat tracker
            if stat_tracker:
                stat_tracker.record_match_result(char, match_result, match_context)
            
            # Check for injuries
            if injury_system:
                # Higher chance if KO'd
                if char.get("is_ko", False):
                    injury_system.check_for_injury(char, "ko", match_context)
                elif char.get("HP", 100) < 30:
                    injury_system.check_for_injury(char, "low_hp", match_context)
                else:
                    injury_system.check_for_injury(char, "end_of_match", match_context)
        
        for char in team_b_active:
            # Record result in stat tracker
            if stat_tracker:
                stat_tracker.record_match_result(char, "win" if match_result == "loss" else ("loss" if match_result == "win" else "draw"), match_context)
            
            # Check for injuries
            if injury_system:
                # Higher chance if KO'd
                if char.get("is_ko", False):
                    injury_system.check_for_injury(char, "ko", match_context)
                elif char.get("HP", 100) < 30:
                    injury_system.check_for_injury(char, "low_hp", match_context)
                else:
                    injury_system.check_for_injury(char, "end_of_match", match_context)
        
        # Update team stats
        if stat_tracker:
            if match_result == "win":
                stat_tracker.update_team_stat(team_a_id, "WINS", 1, "add", match_context)
                stat_tracker.update_team_stat(team_b_id, "LOSSES", 1, "add", match_context)
            elif match_result == "loss":
                stat_tracker.update_team_stat(team_a_id, "LOSSES", 1, "add", match_context)
                stat_tracker.update_team_stat(team_b_id, "WINS", 1, "add", match_context)
            else:
                stat_tracker.update_team_stat(team_a_id, "DRAWS", 1, "add", match_context)
                stat_tracker.update_team_stat(team_b_id, "DRAWS", 1, "add", match_context)
        
        # Save PGNs - use enhanced PGN tracker
        pgn_tracker = self.registry.get("pgn_tracker")
        pgn_files, metadata_files = [], []
        if pgn_tracker:
            pgn_files, metadata_files = pgn_tracker.record_match_games(
                team_a_active, team_a_boards,
                team_b_active, team_b_boards,
                match_context
            )
            self.logger.info(f"PGNs generated: {pgn_files}")
        
        # Record performance metrics
        match_metrics = {
            "rounds_played": round_number - 1,
            "team_a_ko_count": team_a_ko_count,
            "team_b_ko_count": team_b_ko_count,
            "team_a_hp_percent": team_a_hp_pct,
            "team_b_hp_percent": team_b_hp_pct,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins
        }
        
        # Create character results for reporting
        character_results = []
        
        for char in team_a_active:
            character_results.append({
                "character_id": char.get("id", "unknown"),
                "character_name": char.get("name", "Unknown"),
                "team": "A",
                "team_id": team_a_id,
                "role": char.get("role", "Unknown"),
                "division": char.get("division", "Unknown"),
                "was_active": True,
                "is_ko": char.get("is_ko", False),
                "HP": char.get("HP", 0),
                "stamina": char.get("stamina", 0),
                "morale": char.get("morale", 0) if morale_system else None,
                "result": char.get("result", "unknown"),
                "rStats": char.get("rStats", {})
            })
        
        for char in team_b_active:
            character_results.append({
                "character_id": char.get("id", "unknown"),
                "character_name": char.get("name", "Unknown"),
                "team": "B",
                "team_id": team_b_id,
                "role": char.get("role", "Unknown"),
                "division": char.get("division", "Unknown"),
                "was_active": True,
                "is_ko": char.get("is_ko", False),
                "HP": char.get("HP", 0),
                "stamina": char.get("stamina", 0),
                "morale": char.get("morale", 0) if morale_system else None,
                "result": char.get("result", "unknown"),
                "rStats": char.get("rStats", {})
            })
        
        # Generate match report
        match_visualizer = self.registry.get("match_visualizer")
        report_files = []
        if match_visualizer and self.config.get("reporting.generate_match_reports", True):
            # Create result dictionary
            match_result_data = {
                "match_id": match_context["match_id"],
                "day": day_number,
                "match_number": match_number,
                "team_a_name": team_a_name,
                "team_b_name": team_b_name,
                "team_a_id": team_a_id,
                "team_b_id": team_b_id,
                "team_a_division": division_a,
                "team_b_division": division_b,
                "team_a_wins": team_a_wins,
                "team_b_wins": team_b_wins,
                "result": match_result,
                "winning_team": winning_team,
                "losing_team": losing_team,
                "rounds_played": round_number - 1,
                "convergence_count": len(match_context.get("convergence_logs", [])),
                "trait_activations": len(match_context.get("trait_logs", [])),
                "character_results": character_results,
                "convergence_logs": match_context.get("convergence_logs", []),
                "trait_logs": match_context.get("trait_logs", []),
                "stamina_logs": match_context.get("stamina_logs", []),
                "morale_logs": match_context.get("morale_logs", []),
                "pgn_files": pgn_files,
                "metadata_files": metadata_files,
                "metrics": match_metrics
            }
            
            # Generate reports
            report_files = match_visualizer.generate_match_reports(match_result_data)
            self.logger.info(f"Match reports generated: {report_files}")
        
        # Generate visualizations if enabled
        if self.config.get("reporting.generate_charts", True):
            # Check if we have the enhanced stat tracker
            if stat_tracker and hasattr(stat_tracker, "generate_visualization"):
                # Generate team comparison chart
                try:
                    stat_tracker.generate_visualization("team_history", "WINS", team_a_id)
                    stat_tracker.generate_visualization("team_history", "WINS", team_b_id)
                except Exception as e:
                    self.logger.error(f"Error generating team visualizations: {e}")
        
        # Apply experience to characters
        xp_system = self.registry.get("xp_system")
        if xp_system:
            for char in team_a_active + team_b_active:
                xp_system.award_match_experience(char, match_context)
        
        # Apply morale effects
        if morale_system:
            for char in team_a_active:
                morale_system.update_morale(char, match_result == "win", match_context)
            
            for char in team_b_active:
                morale_system.update_morale(char, match_result == "loss", match_context)
        
        # Save persistent data
        self._save_persistent_data()
        
        # Return match results
        return {
            "match_id": match_context["match_id"],
            "day": day_number,
            "match_number": match_number,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "team_a_division": division_a,
            "team_b_division": division_b,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "result": match_result,
            "winning_team": winning_team,
            "rounds_played": round_number - 1,
            "pgn_files": pgn_files,
            "metadata_files": metadata_files,
            "report_files": report_files,
            "metrics": match_metrics
        }
    
    def _apply_home_advantage(self, team: List[Dict[str, Any]]) -> None:
        """Apply home team advantage to a team"""
        advantage_factor = self.config.get("simulation.home_advantage_factor", 0.1)
        
        for char in team:
            # Apply small boost to base stats
            for stat in ["aSTR", "aSPD", "aFS", "aLDR", "aDUR", "aRES", "aWIL"]:
                if stat in char:
                    # Store original value if not already stored
                    orig_key = f"original_{stat}"
                    if orig_key not in char:
                        char[orig_key] = char[stat]
                    
                    # Apply percentage boost
                    char[stat] = char[orig_key] * (1 + advantage_factor)
            
            # Set home flag
            char["is_home"] = True
    
    def _simulate_chess_round(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board],
                            team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board],
                            match_context: Dict[str, Any]) -> None:
        """Simulate a round of chess moves for all characters"""
        chess_system = self.registry.get("chess_system")
        combat_system = self.registry.get("combat_system")
        trait_system = self.registry.get("trait_system")
        
        if not chess_system or not combat_system:
            raise ValueError("Chess system or Combat system not available")
        
        # Process team A moves
        for i, (char, board) in enumerate(zip(team_a, team_a_boards)):
            # Skip knocked out characters
            if char.get("is_ko", False) or not char.get("is_active", True):
                continue
                
            try:
                # Check for pre-move trait activations
                if trait_system:
                    trait_system.check_pre_move_traits(char, board, match_context)
                
                # Select and make move
                move = chess_system.select_move(board, char)
                if move:
                    # Calculate material before move
                    material_before = chess_system.calculate_material_value(board, chess.WHITE)
                    
                    # Make the move
                    board.push(move)
                    
                    # Calculate material after move
                    material_after = chess_system.calculate_material_value(board, chess.WHITE)
                    material_change = material_after - material_before
                    
                    # Update character metrics based on material change
                    combat_system.update_character_metrics(char, material_change, match_context)
                    
                    # Log the move
                    self.logger.debug(f"Team A - {char['name']} moved {move.uci()}, material change: {material_change}")
                    
                    # Check for post-move trait activations
                    if trait_system:
                        trait_system.check_post_move_traits(char, board, match_context)
            except Exception as e:
                self.logger.error(f"Error processing Team A move: {e}")
        
        # Process team B moves
        for i, (char, board) in enumerate(zip(team_b, team_b_boards)):
            # Skip knocked out characters
            if char.get("is_ko", False) or not char.get("is_active", True):
                continue
                
            try:
                # Check for pre-move trait activations
                if trait_system:
                    trait_system.check_pre_move_traits(char, board, match_context)
                
                # Select and make move
                move = chess_system.select_move(board, char)
                if move:
                    # Calculate material before move
                    material_before = chess_system.calculate_material_value(board, chess.WHITE)
                    
                    # Make the move
                    board.push(move)
                    
                    # Calculate material after move
                    material_after = chess_system.calculate_material_value(board, chess.WHITE)
                    material_change = material_after - material_before
                    
                    # Update character metrics based on material change
                    combat_system.update_character_metrics(char, material_change, match_context)
                    
                    # Log the move
                    self.logger.debug(f"Team B - {char['name']} moved {move.uci()}, material change: {material_change}")
                    
                    # Check for post-move trait activations
                    if trait_system:
                        trait_system.check_post_move_traits(char, board, match_context)
            except Exception as e:
                self.logger.error(f"Error processing Team B move: {e}")
    
    def _process_convergences(self, team_a: List[Dict[str, Any]], team_a_boards: List[chess.Board],
                            team_b: List[Dict[str, Any]], team_b_boards: List[chess.Board],
                            match_context: Dict[str, Any]) -> None:
        """Process convergences between boards"""
        convergence_system = self.registry.get("convergence_system")
        
        if not convergence_system:
            raise ValueError("Convergence system not available")
        
        max_per_char = self.config.get("simulation.max_convergences_per_char", 3)
        
        # Process convergences
        convergences = convergence_system.process_convergences(
            team_a, team_a_boards,
            team_b, team_b_boards,
            match_context,
            max_per_char
        )
        
        # Log convergence count
        self.logger.info(f"Processed {len(convergences)} convergences")
    
    def _apply_end_of_round_effects(self, characters: List[Dict[str, Any]], 
                                   match_context: Dict[str, Any]) -> None:
        """Apply end of round effects to all characters"""
        combat_system = self.registry.get("combat_system")
        trait_system = self.registry.get("trait_system")
        stamina_system = self.registry.get("stamina_system")
        morale_system = self.registry.get("morale_system")
        
        if not combat_system:
            raise ValueError("Combat system not available")
        
        # Apply combat system effects
        combat_system.apply_end_of_round_effects(characters, match_context)
        
        # Update trait cooldowns
        if trait_system:
            trait_system.update_cooldowns(characters)
        
        # Apply stamina effects
        if stamina_system:
            stamina_system.apply_end_of_round_effects(characters, match_context)
        
        # Apply morale effects
        if morale_system:
            morale_system.apply_end_of_round_effects(characters, match_context)
    
    def _save_persistent_data(self) -> None:
        """Save persistent data for all systems"""
        systems_to_save = [
            "trait_system", 
            "injury_system", 
            "stat_tracker", 
            "xp_system", 
            "morale_system", 
            "stamina_system"
        ]
        
        for system_name in systems_to_save:
            system = self.registry.get(system_name)
            if system and hasattr(system, "save_persistent_data"):
                try:
                    system.save_persistent_data()
                except Exception as e:
                    self.logger.error(f"Error saving persistent data for {system_name}: {e}")
    
    def simulate_day(self, day_number: int, show_details: bool = True) -> Dict[str, Any]:
        """Simulate a full day of matches"""
        self.logger.info(f"Starting simulation for day {day_number}")
        
        # Check if this is a valid match day (Monday-Friday)
        if not self._is_valid_match_day(day_number):
            raise ValueError(f"Day {day_number} is not a valid match day (must be Mon-Fri)")
        
        # Load data for this day
        data_loader = self.registry.get("data_loader")
        if not data_loader:
            raise ValueError("Data loader not available")
            
        # Load lineups for this day
        try:
            lineups = data_loader.load_lineups(day_number)
            self.logger.info(f"Loaded lineups for day {day_number}: {len(lineups)} teams")
        except Exception as e:
            self.logger.error(f"Error loading lineups for day {day_number}: {e}")
            raise
        
        # Generate matchups
        matches_per_day = 5  # Non-negotiable rule: 5 Matches per Day
        try:
            matchups = data_loader.get_matchups(day_number, lineups)
            self.logger.info(f"Generated matchups for day {day_number}: {matchups}")
        except Exception as e:
            self.logger.error(f"Error generating matchups for day {day_number}: {e}")
            raise
        
        # Check matchup count
        if len(matchups) != matches_per_day:
            self.logger.error(f"Invalid matchup count: {len(matchups)}, expected {matches_per_day}")
            raise ValueError(f"Invalid matchup count: {len(matchups)}, expected {matches_per_day}")
        
        # Process injuries if enabled
        injury_system = self.registry.get("injury_system")
        if injury_system:
            injury_report = injury_system.process_day_change(day_number)
            self.logger.info(f"Processed injuries: {len(injury_report.get('recovered', []))} recovered, {len(injury_report.get('still_injured', []))} still injured")
        
        # Simulate each match
        match_results = []
        
        for match_number, (team_a_id, team_b_id) in enumerate(matchups, 1):
            self.logger.info(f"Starting match {match_number}: {team_a_id} vs {team_b_id}")
            
            # Get team lineups
            team_a = lineups.get(team_a_id, [])
            team_b = lineups.get(team_b_id, [])
            
            # Simulate the match
            try:
                result = self.simulate_match(team_a, team_b, day_number, match_number, show_details)
                match_results.append(result)
                self.logger.info(f"Match {match_number} completed: {result['winning_team']}")
            except Exception as e:
                self.logger.error(f"Error simulating match {match_number}: {e}")
                if self.config.get("development.dump_state_on_error", True):
                    self._dump_error_state(day_number, match_number, team_a_id, team_b_id, e)
                raise
        
        # Generate day summary
        day_results = self._generate_day_summary(day_number, match_results, lineups)
        
        # Record day stats
        stat_tracker = self.registry.get("stat_tracker")
        if stat_tracker and hasattr(stat_tracker, "record_day_summary"):
            stat_tracker.record_day_summary(day_number, day_results)
        
        # Generate day report if enabled
        report_file = None
        if self.config.get("reporting.generate_day_reports", True):
            report_file = self._generate_day_report(day_number, day_results)
        
        # Create backup if configured
        auto_backup_frequency = self.config.get("advanced.auto_backup_frequency", 5)
        if auto_backup_frequency > 0 and day_number % auto_backup_frequency == 0:
            self._create_backup(f"day{day_number}")
            self.logger.info(f"Created backup for day {day_number}")
        
        # Add report file to results
        day_results["report_file"] = report_file
        
        return day_results
    
    def _is_valid_match_day(self, day_number: int) -> bool:
        """Check if a day number is a valid match day (Mon-Fri)"""
        # First day is Monday (4/7/2025)
        # Day 1-5 is week 1, Day 6-10 is week 2, etc.
        # So we need to check if (day_number - 1) % 7 < 5
        return (day_number - 1) % 7 < 5
    
    def _generate_day_summary(self, day_number: int, match_results: List[Dict[str, Any]], 
                             lineups: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """Generate a summary of the day's results"""
        # Calculate team standings
        team_standings = {}
        
        for match in match_results:
            team_a_id = match["team_a_id"]
            team_b_id = match["team_b_id"]
            
            # Initialize team records if not exists
            if team_a_id not in team_standings:
                team_standings[team_a_id] = {"wins": 0, "losses": 0, "draws": 0}
            if team_b_id not in team_standings:
                team_standings[team_b_id] = {"wins": 0, "losses": 0, "draws": 0}
                
            # Update based on result
            if match["result"] == "win":
                team_standings[team_a_id]["wins"] += 1
                team_standings[team_b_id]["losses"] += 1
            elif match["result"] == "loss":
                team_standings[team_a_id]["losses"] += 1
                team_standings[team_b_id]["wins"] += 1
            else:
                team_standings[team_a_id]["draws"] += 1
                team_standings[team_b_id]["draws"] += 1
        
        # Calculate team data
        team_data = {}
        
        data_loader = self.registry.get("data_loader")
        
        for team_id, team_chars in lineups.items():
            team_data[team_id] = {
                "name": data_loader.get_team_name(team_id) if data_loader else f"Team {team_id[1:]}" if team_id.startswith('t') else team_id,
                "division": data_loader.get_team_division(team_id) if data_loader else "Unknown",
                "active_count": sum(1 for char in team_chars if char.get("is_active", True)),
                "injured_count": sum(1 for char in team_chars if char.get("is_injured", False)),
                "total_count": len(team_chars)
            }
        
        # Get calendar date for this day
        calendar_date = self._get_calendar_date(day_number)
        
        # Create summary
        return {
            "day": day_number,
            "date": calendar_date,
            "weekday": self._get_weekday_name(day_number),
            "matches": match_results,
            "standings": team_standings,
            "teams": team_data
        }
    
    def _get_calendar_date(self, day_number: int) -> str:
        """Get calendar date for a given day number"""
        # Start date is April 7, 2025 (Day 1)
        start_date = datetime.date(2025, 4, 7)
        target_date = start_date + datetime.timedelta(days=day_number - 1)
        return target_date.strftime("%Y-%m-%d")
    
    def _get_weekday_name(self, day_number: int) -> str:
        """Get weekday name for a given day number"""
        # Start date is April 7, 2025 (Day 1, Monday)
        weekday_index = (day_number - 1) % 7
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        return weekdays[weekday_index]
    
    def _generate_day_report(self, day_number: int, day_results: Dict[str, Any]) -> str:
        """Generate a report for the day's matches"""
        match_visualizer = self.registry.get("match_visualizer")
        if not match_visualizer:
            self.logger.warning("Match visualizer not available, cannot generate day report")
            return None
        
        try:
            report_file = match_visualizer.generate_day_report(day_number, day_results)
            self.logger.info(f"Day report generated: {report_file}")
            return report_file
        except Exception as e:
            self.logger.error(f"Error generating day report: {e}")
            return None
    
    def _create_backup(self, snapshot_name: str) -> str:
        """Create a backup of the current state"""
        backup_dir = self.config.get("paths.backups_dir", "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"{snapshot_name}_{timestamp}")
        os.makedirs(backup_path, exist_ok=True)
        
        # Save configuration
        config_file = os.path.join(backup_path, "config.json")
        with open(config_file, 'w') as f:
            json.dump(self.config.to_dict(), f, indent=2)
        
        # Save system states
        systems_to_backup = [
            "trait_system", 
            "injury_system", 
            "stat_tracker", 
            "xp_system", 
            "morale_system", 
            "stamina_system"
        ]
        
        for system_name in systems_to_backup:
            system = self.registry.get(system_name)
            if system and hasattr(system, "export_state"):
                try:
                    state_file = os.path.join(backup_path, f"{system_name}_state.json")
                    state = system.export_state()
                    with open(state_file, 'w') as f:
                        json.dump(state, f, indent=2)
                except Exception as e:
                    self.logger.error(f"Error backing up {system_name}: {e}")
        
        self.logger.info(f"Backup created at {backup_path}")
        return backup_path
    
    def _dump_error_state(self, day: int, match: int, team_a_id: str, team_b_id: str, 
                         error: Exception) -> None:
        """Dump simulation state on errors"""
        try:
            # Create dump directory
            dump_dir = os.path.join(self.config.get("paths.logs_dir", "logs"), "error_dumps")
            os.makedirs(dump_dir, exist_ok=True)
            
            # Create dump filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            dump_file = os.path.join(dump_dir, f"error_day{day}_match{match}_{timestamp}.json")
            
            # Create error data
            error_data = {
                "timestamp": timestamp,
                "day": day,
                "match": match,
                "team_a_id": team_a_id,
                "team_b_id": team_b_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "traceback": traceback.format_exc(),
                "simulator_version": self.VERSION,
                "config": self.config.to_dict()
            }
            
            # Write error data
            with open(dump_file, 'w') as f:
                json.dump(error_data, f, indent=2)
                
            self.logger.info(f"Error state dumped to {dump_file}")
        except Exception as e:
            self.logger.error(f"Error dumping error state: {e}")
    
    def simulate_week(self, starting_day: int, show_details: bool = True) -> Dict[str, Any]:
        """Simulate a full week (5 days) of matches"""
        self.logger.info(f"Starting week simulation from day {starting_day}")
        
        # Validate starting day aligns with start of week (Monday)
        if (starting_day - 1) % 7 != 0:
            raise ValueError(f"Starting day {starting_day} is not the first day of a week (must be a Monday)")
            
        # Calculate week number (1-indexed)
        week_number = (starting_day - 1) // 7 + 1
        
        if show_details:
            print(f"\n=== SIMULATING WEEK {week_number} (DAYS {starting_day}-{starting_day+4}) ===\n")
        
        # Simulate each day (Monday-Friday)
        day_results = []
        
        for day_offset in range(5):  # Mon-Fri
            day_number = starting_day + day_offset
            
            if show_details:
                weekday = self._get_weekday_name(day_number)
                print(f"\n--- Day {day_number} ({weekday}) ---\n")
            
            try:
                result = self.simulate_day(day_number, show_details)
                day_results.append(result)
                self.logger.info(f"Day {day_number} completed")
            except Exception as e:
                self.logger.error(f"Error simulating day {day_number}: {e}")
                # Continue with next day if possible
        
        # Generate week summary
        week_results = self._generate_week_summary(week_number, day_results)
        
        # Generate week report if enabled
        report_file = None
        if self.config.get("reporting.generate_week_reports", True):
            report_file = self._generate_week_report(week_number, week_results)
        
        # Add report file to results
        week_results["report_file"] = report_file
        
        return week_results
    
    def _generate_week_summary(self, week_number: int, day_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the week's results"""
        # Calculate overall standings
        team_standings = {}
        division_standings = {}
        
        data_loader = self.registry.get("data_loader")
        
        for day in day_results:
            for team_id, standings in day.get("standings", {}).items():
                if team_id not in team_standings:
                    team_standings[team_id] = {"wins": 0, "losses": 0, "draws": 0}
                
                team_standings[team_id]["wins"] += standings.get("wins", 0)
                team_standings[team_id]["losses"] += standings.get("losses", 0)
                team_standings[team_id]["draws"] += standings.get("draws", 0)
                
                # Get division for team if available
                if data_loader:
                    division = data_loader.get_team_division(team_id)
                    if division:
                        if division not in division_standings:
                            division_standings[division] = {}
                        
                        if team_id not in division_standings[division]:
                            division_standings[division][team_id] = {"wins": 0, "losses": 0, "draws": 0}
                        
                        division_standings[division][team_id]["wins"] += standings.get("wins", 0)
                        division_standings[division][team_id]["losses"] += standings.get("losses", 0)
                        division_standings[division][team_id]["draws"] += standings.get("draws", 0)
        
        # Calculate stats for each team
        for team_id, standings in team_standings.items():
            # Calculate total games and points
            total_games = standings["wins"] + standings["losses"] + standings["draws"]
            standings["total_games"] = total_games
            standings["points"] = standings["wins"] * 3 + standings["draws"]
            
            # Calculate win percentage
            if total_games > 0:
                standings["win_pct"] = standings["wins"] / total_games
            else:
                standings["win_pct"] = 0.0
        
        # Do the same for division standings
        for division, teams in division_standings.items():
            for team_id, standings in teams.items():
                # Calculate total games and points
                total_games = standings["wins"] + standings["losses"] + standings["draws"]
                standings["total_games"] = total_games
                standings["points"] = standings["wins"] * 3 + standings["draws"]
                
                # Calculate win percentage
                if total_games > 0:
                    standings["win_pct"] = standings["wins"] / total_games
                else:
                    standings["win_pct"] = 0.0
        
        # Sort standings by points
        sorted_standings = sorted(
            team_standings.items(),
            key=lambda x: (x[1]["points"], x[1]["wins"], -x[1]["losses"]),
            reverse=True
        )
        
        # Sort division standings
        sorted_division_standings = {}
        for division, teams in division_standings.items():
            sorted_division_standings[division] = sorted(
                teams.items(),
                key=lambda x: (x[1]["points"], x[1]["wins"], -x[1]["losses"]),
                reverse=True
            )
        
        # Calculate date range
        first_day = day_results[0]["date"] if day_results else None
        last_day = day_results[-1]["date"] if day_results else None
        date_range = f"{first_day} to {last_day}" if first_day and last_day else "Unknown"
        
        # Create summary
        return {
            "week": week_number,
            "days": [day.get("day") for day in day_results],
            "date_range": date_range,
            "days_completed": len(day_results),
            "standings": sorted_standings,
            "division_standings": sorted_division_standings
        }
    
    def _generate_week_report(self, week_number: int, week_results: Dict[str, Any]) -> str:
        """Generate a report for the week's matches"""
        match_visualizer = self.registry.get("match_visualizer")
        if not match_visualizer:
            self.logger.warning("Match visualizer not available, cannot generate week report")
            return None
        
        try:
            report_file = match_visualizer.generate_week_report(week_number, week_results)
            self.logger.info(f"Week report generated: {report_file}")
            return report_file
        except Exception as e:
            self.logger.error(f"Error generating week report: {e}")
            return None
    
    def simulate_season(self, show_details: bool = True) -> Dict[str, Any]:
        """Simulate a full season of matches"""
        self.logger.info("Starting season simulation")
        
        # Season length is configurable (default 10 weeks)
        weeks_per_season = self.config.get("simulation.weeks_per_season", 10)
        starting_day = 1
        
        if show_details:
            print(f"\n=== SIMULATING FULL {weeks_per_season}-WEEK SEASON ===\n")
        
        # Simulate each week
        week_results = []
        
        for week_number in range(1, weeks_per_season + 1):
            if show_details:
                print(f"\n==== WEEK {week_number} ====\n")
                
            try:
                day_number = starting_day + (week_number - 1) * 7
                result = self.simulate_week(day_number, show_details)
                week_results.append(result)
                self.logger.info(f"Week {week_number} completed")
            except Exception as e:
                self.logger.error(f"Error simulating week {week_number}: {e}")
                # Continue with next week if possible
        
        # Generate season summary
        season_results = self._generate_season_summary(week_results)
        
        # Generate season report if enabled
        report_file = None
        if self.config.get("reporting.generate_season_reports", True):
            report_file = self._generate_season_report(season_results)
        
        # Add report file to results
        season_results["report_file"] = report_file
        
        return season_results
    
    def _generate_season_summary(self, week_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the season's results"""
        # Calculate overall standings
        team_standings = {}
        division_standings = {}
        
        data_loader = self.registry.get("data_loader")
        
        # Collect all team IDs and initialize standings
        for week in week_results:
            for team_id, _ in week.get("standings", []):
                if team_id not in team_standings:
                    team_standings[team_id] = {"wins": 0, "losses": 0, "draws": 0, "points": 0}
                
                # Get division for team if available
                if data_loader:
                    division = data_loader.get_team_division(team_id)
                    if division:
                        if division not in division_standings:
                            division_standings[division] = {}
                        
                        if team_id not in division_standings[division]:
                            division_standings[division][team_id] = {"wins": 0, "losses": 0, "draws": 0, "points": 0}
        
        # Aggregate results from all weeks
        for week in week_results:
            for team_id, standings in week.get("standings", []):
                team_standings[team_id]["wins"] += standings.get("wins", 0)
                team_standings[team_id]["losses"] += standings.get("losses", 0)
                team_standings[team_id]["draws"] += standings.get("draws", 0)
                team_standings[team_id]["points"] += standings.get("points", 0)
                
                # Update division standings
                if data_loader:
                    division = data_loader.get_team_division(team_id)
                    if division and division in division_standings and team_id in division_standings[division]:
                        division_standings[division][team_id]["wins"] += standings.get("wins", 0)
                        division_standings[division][team_id]["losses"] += standings.get("losses", 0)
                        division_standings[division][team_id]["draws"] += standings.get("draws", 0)
                        division_standings[division][team_id]["points"] += standings.get("points", 0)
        
        # Calculate stats for each team
        for team_id, standings in team_standings.items():
            # Calculate total games
            total_games = standings["wins"] + standings["losses"] + standings["draws"]
            standings["total_games"] = total_games
            
            # Calculate win percentage
            if total_games > 0:
                standings["win_pct"] = standings["wins"] / total_games
            else:
                standings["win_pct"] = 0.0
            
            # Get team name
            if data_loader:
                standings["name"] = data_loader.get_team_name(team_id)
                standings["division"] = data_loader.get_team_division(team_id)
        
        # Do the same for division standings
        for division, teams in division_standings.items():
            for team_id, standings in teams.items():
                # Calculate total games
                total_games = standings["wins"] + standings["losses"] + standings["draws"]
                standings["total_games"] = total_games
                
                # Calculate win percentage
                if total_games > 0:
                    standings["win_pct"] = standings["wins"] / total_games
                else:
                    standings["win_pct"] = 0.0
                
                # Get team name
                if data_loader:
                    standings["name"] = data_loader.get_team_name(team_id)
        
        # Sort standings by points
        sorted_standings = sorted(
            team_standings.items(),
            key=lambda x: (x[1]["points"], x[1]["wins"], -x[1]["losses"]),
            reverse=True
        )
        
        # Sort division standings
        sorted_division_standings = {}
        for division, teams in division_standings.items():
            sorted_division_standings[division] = sorted(
                teams.items(),
                key=lambda x: (x[1]["points"], x[1]["wins"], -x[1]["losses"]),
                reverse=True
            )
        
        # Determine division champions
        division_champions = {}
        for division, teams in sorted_division_standings.items():
            if teams:  # If there are teams in the division
                champion_id, champion_stats = teams[0]  # Top team
                division_champions[division] = {
                    "team_id": champion_id,
                    "name": champion_stats.get("name", f"Team {champion_id}"),
                    "wins": champion_stats["wins"],
                    "losses": champion_stats["losses"],
                    "draws": champion_stats["draws"],
                    "points": champion_stats["points"],
                    "win_pct": champion_stats["win_pct"]
                }
        
        # Determine overall champion (top team in sorted standings)
        overall_champion = None
        if sorted_standings:
            champion_id, champion_stats = sorted_standings[0]
            overall_champion = {
                "team_id": champion_id,
                "name": champion_stats.get("name", f"Team {champion_id}"),
                "division": champion_stats.get("division", "Unknown"),
                "wins": champion_stats["wins"],
                "losses": champion_stats["losses"],
                "draws": champion_stats["draws"],
                "points": champion_stats["points"],
                "win_pct": champion_stats["win_pct"]
            }
        
        # Determine date range of season
        first_week = week_results[0] if week_results else {}
        last_week = week_results[-1] if week_results else {}
        first_day = first_week.get("date_range", "").split(" to ")[0] if first_week else None
        last_day = last_week.get("date_range", "").split(" to ")[-1] if last_week else None
        date_range = f"{first_day} to {last_day}" if first_day and last_day else "Unknown"
        
        # Create summary
        return {
            "weeks_completed": len(week_results),
            "date_range": date_range,
            "standings": sorted_standings,
            "division_standings": sorted_division_standings,
            "division_champions": division_champions,
            "overall_champion": overall_champion
        }
    
    def _generate_season_report(self, season_results: Dict[str, Any]) -> str:
        """Generate a report for the season's results"""
        match_visualizer = self.registry.get("match_visualizer")
        if not match_visualizer:
            self.logger.warning("Match visualizer not available, cannot generate season report")
            return None
        
        try:
            report_file = match_visualizer.generate_season_report(season_results)
            self.logger.info(f"Season report generated: {report_file}")
            return report_file
        except Exception as e:
            self.logger.error(f"Error generating season report: {e}")
            return None

# Main execution code
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description=f"META Fantasy League Simulator v5.0")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--day", type=int, help="Simulate a specific day")
    parser.add_argument("--week", type=int, help="Simulate a specific week (must be a Monday)")
    parser.add_argument("--season", action="store_true", help="Simulate a full season")
    parser.add_argument("--match", type=int, help="Match number to run (requires --day)")
    parser.add_argument("--quiet", action="store_true", help="Run in quiet mode (minimal output)")
    parser.add_argument("--validate", action="store_true", help="Run validation only")
    parser.add_argument("--backup", action="store_true", help="Create a backup before running")
    
    args = parser.parse_args()
    
    try:
        # Initialize simulator
        simulator = MetaLeagueSimulatorV5(args.config)
        
        # Run backup if requested
        if args.backup:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            simulator._create_backup(f"manual_{timestamp}")
            print(f"Backup created successfully")
        
        # Run validation only if requested
        if args.validate:
            print("Validation completed successfully")
            sys.exit(0)
        
        # Determine what to simulate
        show_details = not args.quiet
        
        if args.day and args.match:
            # Simulate specific match on specific day
            print(f"Simulating day {args.day}, match {args.match}")
            # This would require additional code to set up the specific match
            print("Feature not yet implemented")
        elif args.season:
            print(f"Simulating full season")
            simulator.simulate_season(show_details)
        elif args.week:
            print(f"Simulating week starting at day {args.week}")
            simulator.simulate_week(args.week, show_details)
        elif args.day:
            print(f"Simulating day {args.day}")
            simulator.simulate_day(args.day, show_details)
        else:
            print("No simulation mode specified. Use --day, --week, or --season")
    except Exception as e:
        print(f"Error: {e}")
        # Print traceback if in development mode
        if args.config:
            config = ConfigurationManager(args.config)
            if config.get("development.debug_mode", False):
                import traceback
                traceback.print_exc()