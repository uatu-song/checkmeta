"""
META Fantasy League Simulator v4.2.1
Enhanced simulation engine for META League matches with advanced statistics and tracking

Major improvements:
- PGN Generation Fix: Support for both individual per-board PGNs and aggregated match PGNs
- Robust Stamina System: Comprehensive stamina tracking that persists across matches
- Combat Calibration: Enhanced combat mechanics following calibration plan
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
from typing import Dict, List, Any, Optional, Tuple, Union, Set
from collections import defaultdict

# Import system base
from system_base import SystemBase
from system_registry import SystemRegistry
from configuration_manager_wrapper import ConfigurationManager
from config_utils import load_config


class MetaLeagueSimulatorV4_2_1:
    """Main simulator class for META Fantasy League simulations v4.2.1"""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the simulator v4.2.1"""
        # Create banner
        self._print_banner()
        
        # Create configuration
        self.config = ConfigurationManager(config_file)
        

        # Manually set config paths if missing
        self.config.DATA_DIR = os.path.join(os.getcwd(), "data")
        self.config.RESULTS_DIR = os.path.join(os.getcwd(), "results")
        self.config.LOGS_DIR = os.path.join(os.getcwd(), "logs")

        # Set up logging
        self._setup_logging()
        
        # Create registry
        self.registry = SystemRegistry()
        
        # Validate system integrity
        if not self._validate_system_integrity():
            raise RuntimeError("System validation failed. Fix errors before continuing.")
        
        # Initialize subsystems
        self._initialize_subsystems()
        
        self.logger.info("META Fantasy League Simulator v4.2.1 initialized successfully")
    
    def _print_banner(self):
        """Print simulator banner"""
        banner = """
╔══════════════════════════════════════════════════════╗
║                                                      ║
║   ███╗   ███╗███████╗████████╗ █████╗    ██╗  ██╗    ║
║   ████╗ ████║██╔════╝╚══██╔══╝██╔══██╗   ██║  ██║    ║
║   ██╔████╔██║█████╗     ██║   ███████║   ██║  ██║    ║
║   ██║╚██╔╝██║██╔══╝     ██║   ██╔══██║   ╚██╗██╔╝    ║
║   ██║ ╚═╝ ██║███████╗   ██║   ██║  ██║    ╚███╔╝     ║
║                                         v4.2.1       ║
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
        return gatekeeper.run_all_checks()
    
    def _initialize_subsystems(self):
        """Initialize all simulation subsystems"""
        # Initialize core systems
        # Each of these would be imported from their respective files
        
        # Initialize data loader (already done in validation)
        data_loader = self.registry.get("data_loader")
        
        # Initialize trait system
        from trait_system import TraitSystem
        trait_system = TraitSystem(self.config)
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
        
        # Initialize stamina system if enabled
        if self.config.get("features.stamina_enabled"):
            from stamina_system import StaminaSystem
            stamina_system = StaminaSystem(self.config)
            self.registry.register("stamina_system", stamina_system)
            self.logger.info("Stamina system enabled and initialized")
        
        # Initialize injury system if enabled
        if self.config.get("features.injury_enabled"):
            from injury_system import InjurySystem
            injury_system = InjurySystem(self.config)
            self.registry.register("injury_system", injury_system)
            self.logger.info("Injury system enabled and initialized")
        
        # Initialize PGN tracker with enhanced version
        from enhanced_pgn_tracker import EnhancedPGNTracker
        pgn_tracker = EnhancedPGNTracker(self.config)
        self.registry.register("pgn_tracker", pgn_tracker)
        self.logger.info(f"Enhanced PGN tracker initialized with per_board_pgn={self.config.get('features.per_board_pgn', True)}, aggregate_match_pgn={self.config.get('features.aggregate_match_pgn', True)}")
        
        # Initialize stat tracker
        from stat_tracker import StatTracker
        stat_tracker = StatTracker(self.config)
        self.registry.register("stat_tracker", stat_tracker)
        
        # Initialize match visualizer
        from match_visualizer import MatchVisualizer
        match_visualizer = MatchVisualizer(self.config)
        self.registry.register("match_visualizer", match_visualizer)
        
        # Initialize XP system if enabled
        if self.config.get("features.xp_enabled"):
            from xp_system import XPSystem
            xp_system = XPSystem(self.config)
            self.registry.register("xp_system", xp_system)
            self.logger.info("XP system enabled and initialized")
        
        # Initialize synergy system if enabled
        if self.config.get("features.synergy_enabled"):
            from synergy_system import SynergySystem
            synergy_system = SynergySystem(self.config)
            self.registry.register("synergy_system", synergy_system)
            self.logger.info("Synergy system enabled and initialized")
        
        # Initialize morale system if enabled
        if self.config.get("features.morale_enabled"):
            from morale_system import MoraleSystem
            morale_system = MoraleSystem(self.config)
            self.registry.register("morale_system", morale_system)
            self.logger.info("Morale system enabled and initialized")
        
        # Activate all systems
        for system_name in self.registry._systems:
            self.registry.activate(system_name)
            
        self.logger.info("All subsystems initialized and activated")
    
    def simulate_match(self, team_a: List[Dict[str, Any]], team_b: List[Dict[str, Any]], 
                      day_number: int = 1, match_number: int = 1, 
                      show_details: bool = True) -> Dict[str, Any]:
        """Simulate a match between two teams"""
        self.logger.info(f"Starting match simulation - Day {day_number}, Match {match_number}")
        
        # Validate teams
        if not team_a or not team_b:
            raise ValueError("Both teams must have characters")
        
        teams_per_match = self.config.get("simulation.teams_per_match")
        
        # Extract active characters only
        team_a_active = [char for char in team_a if char.get("is_active", True)][:teams_per_match]
        team_b_active = [char for char in team_b if char.get("is_active", True)][:teams_per_match]
        
        # Check team sizes
        if len(team_a_active) < teams_per_match or len(team_b_active) < teams_per_match:
            self.logger.warning(f"Team sizes are less than required {teams_per_match}")
        
        # Get team IDs and names
        team_a_id = team_a_active[0].get("team_id", "unknown") if team_a_active else "unknown"
        team_b_id = team_b_active[0].get("team_id", "unknown") if team_b_active else "unknown"
        
        team_a_name = f"Team {team_a_id[1:]}" if team_a_id.startswith('t') else team_a_id
        team_b_name = f"Team {team_b_id[1:]}" if team_b_id.startswith('t') else team_b_id
        
        # Create match context
        match_context = {
            "match_id": f"day{day_number}_match{match_number}_{team_a_id}_vs_{team_b_id}",
            "day": day_number,
            "match_number": match_number,
            "team_a_id": team_a_id,
            "team_b_id": team_b_id,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "date": datetime.datetime.now().isoformat(),
            "round": 1,
            "trait_logs": [],
            "convergence_logs": [],
            "stamina_logs": []
        }
        
        # Initialize stamina for all characters if system is enabled
        stamina_system = self.registry.get("stamina_system")
        if stamina_system:
            for char in team_a_active + team_b_active:
                stamina_system.initialize_character_stamina(char)
        
        # Apply injuries if enabled
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
        is_home_day_a = day_number % 2 == 0
        if is_home_day_a:
            # Even day: team_a is home
            self._apply_home_advantage(team_a_active)
            self.logger.info(f"Home advantage applied to {team_a_name}")
        else:
            # Odd day: team_b is home
            self._apply_home_advantage(team_b_active)
            self.logger.info(f"Home advantage applied to {team_b_name}")
        
        # Apply team synergies if enabled
        synergy_system = self.registry.get("synergy_system")
        if synergy_system:
            synergy_system.apply_team_synergies(team_a_active, team_a_id)
            synergy_system.apply_team_synergies(team_b_active, team_b_id)
        
        # Main simulation loop
        max_rounds = self.config.get("simulation.max_moves", 30)
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
            
            ko_threshold = self.config.get("simulation.ko_threshold")
            
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
            
            team_hp_threshold = self.config.get("simulation.team_hp_threshold")
            
            if team_a_hp_pct < team_hp_threshold or team_b_hp_pct < team_hp_threshold:
                match_complete = True
                self.logger.info(f"Match complete by HP threshold: A={team_a_hp_pct:.1f}%, B={team_b_hp_pct:.1f}%")
                
                if show_details:
                    if team_a_hp_pct < team_hp_threshold:
                        print(f"\n{team_a_name} has been defeated by HP threshold!")
                    if team_b_hp_pct < team_hp_threshold:
                        print(f"\n{team_b_name} has been defeated by HP threshold!")
            
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
        
        # Also account for KO'd characters
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
        # Otherwise compare wins
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
        
        if show_details:
            print(f"\nFinal score: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}")
            print(f"Winner: {winning_team}")
        
        self.logger.info(f"Match result: {winning_team} wins {team_a_wins}-{team_b_wins}")
        
        # Record match results
        for char in team_a_active:
            # Record result in stat tracker
            if stat_tracker:
                stat_tracker.record_match_result(char, match_result, match_context)
            
            # Check for injuries if enabled
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
            
            # Check for injuries if enabled
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
        pgn_file, metadata_file = "", ""
        if pgn_tracker:
            pgn_file, metadata_file = pgn_tracker.record_match_games(
                team_a_active, team_a_boards,
                team_b_active, team_b_boards,
                match_context
            )
            self.logger.info(f"PGNs generated: {pgn_file}")
        
        # Create character results for reporting
        character_results = []
        
        for char in team_a_active:
            character_results.append({
                "character_id": char.get("id", "unknown"),
                "character_name": char.get("name", "Unknown"),
                "team": "A",
                "role": char.get("role", "Unknown"),
                "division": char.get("division", "Unknown"),
                "was_active": True,
                "is_ko": char.get("is_ko", False),
                "HP": char.get("HP", 0),
                "stamina": char.get("stamina", 0),
                "result": char.get("result", "unknown"),
                "rStats": char.get("rStats", {})
            })
        
        for char in team_b_active:
            character_results.append({
                "character_id": char.get("id", "unknown"),
                "character_name": char.get("name", "Unknown"),
                "team": "B",
                "role": char.get("role", "Unknown"),
                "division": char.get("division", "Unknown"),
                "was_active": True,
                "is_ko": char.get("is_ko", False),
                "HP": char.get("HP", 0),
                "stamina": char.get("stamina", 0),
                "result": char.get("result", "unknown"),
                "rStats": char.get("rStats", {})
            })