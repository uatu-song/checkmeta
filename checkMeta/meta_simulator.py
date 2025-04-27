#!/usr/bin/env python3
"""
META Fantasy League Simulator - Complete Implementation
A streamlined, integrated version with stable core functionality
"""

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
from systems.initiative_randomizer import randomize_team_order, randomize_convergence_processing
from systems.buffered_damage import BufferedDamageSystem
from systems.enhanced_field_leader import FieldLeaderEnhancer
from systems.loss_conditions import LossConditionSystem
from systems.convergence_balancer import ConvergenceBalancer
from systems.momentum_system import MomentumSystem

# Create necessary directories
os.makedirs("results", exist_ok=True)
os.makedirs("results/pgn", exist_ok=True)
os.makedirs("results/reports", exist_ok=True)
os.makedirs("results/stats", exist_ok=True)

#####################################
# CORE SIMULATOR ENGINE
#####################################
class MetaLeagueSimulator:
    """
    META Fantasy League simulation engine with integrated components
    """
    def __init__(self, stockfish_path=None):
        """Initialize the simulator with all necessary components"""
        # Core settings
        self.current_day = 1
        self.MAX_MOVES = 30
        self.MAX_BATCH_SIZE = 5
        self.MAX_CONVERGENCES_PER_CHAR = 3
        self.stockfish_path = stockfish_path
        self.buffered_damage = BufferedDamageSystem(
            base_damage_reduction=self.BASE_DAMAGE_REDUCTION,
            max_damage_reduction=self.MAX_DAMAGE_REDUCTION,
            max_damage_per_hit=self.MAX_DAMAGE_PER_HIT
        )
        
        # Integrated tracking systems
        self.pgn_tracker = PGNTracker()
        self.stat_tracker = StatTracker()
        self.field_leader_enhancer = FieldLeaderEnhancer()
        self.loss_condition_system = LossConditionSystem()
        self.convergence_balancer = ConvergenceBalancer()
        self.momentum_system = MomentumSystem()

        # Battle parameters - tuned for balance
        self.DAMAGE_SCALING = 2.0       # Base multiplier for damage (reduced from 3)
        self.BASE_DAMAGE_REDUCTION = 35 # Base damage reduction percentage
        self.MAX_DAMAGE_REDUCTION = 75  # Maximum damage reduction percentage
        self.MAX_DAMAGE_PER_HIT = 30    # Safety cap on damage
        self.HP_REGEN_RATE = 3          # HP regeneration per turn
        self.STAMINA_REGEN_RATE = 5     # Stamina regeneration per turn
        self.CRITICAL_THRESHOLD = 25    # Threshold for critical hits
        
        # Trait definitions
        self.traits = self._create_trait_definitions()
        
        # Role-based openings
        self.role_openings = {
            "FL": ["e4", "d4", "c4"],         # Field Leader
            "RG": ["Nf3", "g3", "b3"],        # Ranger
            "VG": ["e4 e5 Nf3", "d4 d5 c4"],  # Vanguard
            "EN": ["c4", "d4 d5", "e4 c5"],   # Enforcer
            "GO": ["g3", "b3", "c4"],         # Ghost Operative
            "PO": ["d4 Nf6", "e4 e6", "c4 c5"], # Psi Operative
            "SV": ["e4 e5 Nf3 Nc6", "d4 d5 c4 e6"] # Sovereign
        }
        
        print(f"Initialized META Fantasy League Simulator")
        print(f"Max moves: {self.MAX_MOVES}, Damage scaling: {self.DAMAGE_SCALING}")
    
    def _create_trait_definitions(self):
        """Create definitions for character traits"""
        return {
            "genius": {
                "name": "Genius Intellect",
                "type": "combat",
                "triggers": ["convergence", "critical_hit"],
                "formula_key": "bonus_roll",
                "value": 15
            },
            "armor": {
                "name": "Power Armor",
                "type": "defense",
                "triggers": ["damage_taken"],
                "formula_key": "damage_reduction",
                "value": 25
            },
            "tactical": {
                "name": "Tactical Mastery",
                "type": "leadership",
                "triggers": ["convergence", "team_boost"],
                "formula_key": "bonus_roll",
                "value": 20
            },
            "shield": {
                "name": "Vibranium Shield",
                "type": "defense",
                "triggers": ["damage_taken", "convergence"],
                "formula_key": "damage_reduction",
                "value": 30
            },
            "agile": {
                "name": "Enhanced Agility",
                "type": "mobility",
                "triggers": ["convergence", "evasion"],
                "formula_key": "bonus_roll",
                "value": 15
            },
            "spider-sense": {
                "name": "Spider Sense",
                "type": "precognition",
                "triggers": ["combat", "danger"],
                "formula_key": "defense_bonus",
                "value": 20
            },
            "stretchy": {
                "name": "Polymorphic Body",
                "type": "mobility",
                "triggers": ["convergence", "positioning"],
                "formula_key": "bonus_roll",
                "value": 10
            },
            "healing": {
                "name": "Rapid Healing",
                "type": "regeneration",
                "triggers": ["end_of_turn", "damage_taken"],
                "formula_key": "heal",
                "value": 5
            }
        }
    
    def run_matchday(self, day_number=1, lineup_file="data/lineups/All Lineups 1.xlsx", show_details=True):
        """Run all matches for a specific day using real lineups"""
        self.current_day = day_number
        
        # Load team lineups
        print(f"Loading lineups from {lineup_file} for day {day_number}")
        try:
            teams = self.load_lineups_from_excel(lineup_file, f"{day_number}/7/25")
            print(f"Loaded {len(teams)} teams")
        except Exception as e:
            print(f"Error loading lineups: {e}")
            return []
        
        # Create matchups
        matchups = self.create_team_matchups(teams, day_number)
        print(f"Created {len(matchups)} matchups for day {day_number}")
        
        if not matchups:
            print("No valid matchups found. Check team IDs in lineup file.")
            return []
        
        # Run all matchups
        results = []
        for i, (team_a_id, team_b_id) in enumerate(matchups):
            try:
                print(f"\n=== Match {i+1}: {team_a_id} vs {team_b_id} ===")
                
                team_a = teams.get(team_a_id, [])
                team_b = teams.get(team_b_id, [])
                
                if not team_a or not team_b:
                    print(f"Error: Missing teams for matchup!")
                    continue
                
                print(f"Simulating: {team_a[0]['team_name']} vs {team_b[0]['team_name']}")
                
                # Run simulation for this matchup
                match_result = self.simulate_match(team_a, team_b, show_details=show_details)
                
                if match_result:
                    results.append(match_result)
                    print(f"Match complete: {match_result['team_a_wins']} - {match_result['team_b_wins']}")
                else:
                    print("Match failed to produce results!")
                
                time.sleep(1)  # Brief pause between matches
                
            except Exception as e:
                print(f"Error in match {i+1}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        # Save day results
        timestamp = int(time.time())
        results_file = f"results/day_{day_number}_results_{timestamp}.json"
        
        if results:
            with open(results_file, "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\nAll matches for day {day_number} completed")
            print(f"Results saved to {results_file}")
        else:
            print(f"No valid match results to save")
        
        return results
    
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
        # Create match context
        match_context = {
            "day": self.current_day,
            "team_a_id": team_a[0]["team_id"] if team_a else "unknown",
            "team_b_id": team_b[0]["team_id"] if team_b else "unknown",
            "team_a_name": team_a[0]["team_name"] if team_a else "Team A",
            "team_b_name": team_b[0]["team_name"] if team_b else "Team B",
            "round": 0,
            "trait_activations": [],
            "convergences": [],
            "damage_log": []
        }
        
        if show_details:
            print(f"Match: {match_context['team_a_name']} vs {match_context['team_b_name']}")
        
        # Register all characters with stat tracker
        for character in team_a + team_b:
            self.stat_tracker.register_character(character)
        
        # Initialize PGN tracker for this match
        self.pgn_tracker.start_match(
            team_a_name=match_context['team_a_name'],
            team_b_name=match_context['team_b_name'],
            team_a_id=match_context['team_a_id'],
            team_b_id=match_context['team_b_id'],
            day=self.current_day
        )

        # Enhance Field Leaders
        team_a, team_b = self.field_leader_enhancer.enhance_field_leaders(team_a, team_b)
      
        # Create chess boards for each character
        team_a_boards = [chess.Board() for _ in team_a]
        team_b_boards = [chess.Board() for _ in team_b]
        
        # Initialize momentum
        team_a_momentum = {"state": "stable", "value": 0}
        team_b_momentum = {"state": "stable", "value": 0}
        
        # Apply role-based openings
        self._apply_openings(team_a, team_a_boards)
        self._apply_openings(team_b, team_b_boards)
        
        # Track initial material values
        team_a_material = [self._calculate_material(board) for board in team_a_boards]
        team_b_material = [self._calculate_material(board) for board in team_b_boards]
        
        # Define batch size for processing
        batch_size = self.MAX_BATCH_SIZE  # Process moves in batches
        
        # Track team results for final tally
        team_a_wins = 0
        team_b_wins = 0
        character_results = []
        
        # Process in batches
        for batch_start in range(0, self.MAX_MOVES, batch_size):
            batch_end = min(batch_start + batch_size, self.MAX_MOVES)
            
            if show_details:
                print(f"\n--- PROCESSING BATCH: Moves {batch_start+1} to {batch_end} ---")
            
            # Process each move in this batch
            for move_num in range(batch_start, batch_end):
                match_context["round"] = move_num + 1
                
                if show_details:
                    print(f"\nRound {move_num + 1}:")
                
                # Process convergences between boards
                self._process_convergences(team_a, team_a_boards, team_b, team_b_boards, match_context, show_details)
                
                # Make moves for team A
                for i, (character, board) in enumerate(zip(team_a, team_a_boards)):
                    # Skip if character is KO'd or board is in terminal state
                    if character.get("is_ko", False) or board.is_game_over():
                        continue
                    
                    # Select and make move
                    move = self._select_move(board, character)
                    
                    if move:
                        if show_details:
                            print(f"{character['name']} moves: {board.san(move)}")
                        
                        # Make the move
                        board.push(move)
                        
                        # Update material and metrics
                        new_material = self._calculate_material(board)
                        material_change = new_material - team_a_material[i]
                        team_a_material[i] = new_material
                        
                        # Apply consequences of material change
                        if material_change != 0:
                            self._apply_material_effects(character, material_change, show_details)
                
                # Make moves for team B
                for i, (character, board) in enumerate(zip(team_b, team_b_boards)):
                    # Skip if character is KO'd or board is in terminal state
                    if character.get("is_ko", False) or board.is_game_over():
                        continue
                    
                    # Select and make move
                    move = self._select_move(board, character)
                    
                    if move:
                        if show_details:
                            print(f"{character['name']} moves: {board.san(move)}")
                        
                        # Make the move
                        board.push(move)
                        
                        # Update material and metrics
                        new_material = self._calculate_material(board)
                        material_change = new_material - team_b_material[i]
                        team_b_material[i] = new_material
                        
                        # Apply consequences of material change
                        if material_change != 0:
                            self._apply_material_effects(character, material_change, show_details)
                
                # Apply end-of-round effects
                self._apply_end_of_round_effects(team_a + team_b, match_context, show_details)
                
                # Check team loss conditions
                team_a_lost = self._check_team_loss_conditions(team_a)
                team_b_lost = self._check_team_loss_conditions(team_b)
                
                if team_a_lost or team_b_lost:
                    if show_details:
                        if team_a_lost:
                            print(f"\n*** {match_context['team_a_name']} LOST ***")
                        if team_b_lost:
                            print(f"\n*** {match_context['team_b_name']} LOST ***")
                    break
                
                # Check if match is effectively over
                active_a = sum(1 for char in team_a if not char.get("is_ko", False))
                active_b = sum(1 for char in team_b if not char.get("is_ko", False))
                
                if active_a == 0 or active_b == 0:
                    if show_details:
                        print(f"\nMatch effectively over: {active_a} active vs {active_b} active")
                    break
            
            # Record PGN data for this batch
            self._record_batch_pgn(team_a, team_a_boards, team_b, team_b_boards, match_context, batch_end)
            
            # Check if match is over after this batch
            if team_a_lost or team_b_lost or active_a == 0 or active_b == 0:
                break
        
        # Calculate final results
        for i, (character, board) in enumerate(zip(team_a, team_a_boards)):
            result = self._determine_game_result(board, character)
            
            if result == "win":
                team_a_wins += 1
                self.stat_tracker.record_match_result(character, "win")
            else:
                self.stat_tracker.record_match_result(character, result)
            
            character_results.append({
                "team": "A",
                "character_id": character.get("id", f"A{i}"),
                "character_name": character.get("name", f"Character A{i}"),
                "role": character.get("role", "Unknown"),
                "result": result,
                "final_hp": character.get("HP", 0),
                "final_stamina": character.get("stamina", 0),
                "is_ko": character.get("is_ko", False),
                "was_active": True,
                "rStats": character.get("rStats", {})
            })
        
        for i, (character, board) in enumerate(zip(team_b, team_b_boards)):
            result = self._determine_game_result(board, character)
            
            if result == "win":
                team_b_wins += 1
                self.stat_tracker.record_match_result(character, "win")
            else:
                self.stat_tracker.record_match_result(character, result)
            
            character_results.append({
                "team": "B",
                "character_id": character.get("id", f"B{i}"),
                "character_name": character.get("name", f"Character B{i}"),
                "role": character.get("role", "Unknown"),
                "result": result,
                "final_hp": character.get("HP", 0),
                "final_stamina": character.get("stamina", 0),
                "is_ko": character.get("is_ko", False),
                "was_active": True,
                "rStats": character.get("rStats", {})
            })
        
        # Determine match winner
        if team_a_wins > team_b_wins:
            winner = "Team A"
            winning_team = match_context["team_a_name"]
        elif team_b_wins > team_a_wins:
            winner = "Team B"
            winning_team = match_context["team_b_name"]
        else:
            winner = "Draw"
            winning_team = "None"
        
        if show_details:
            print(f"\nMatch Result: {match_context['team_a_name']} {team_a_wins} - {team_b_wins} {match_context['team_b_name']}")
            print(f"Winner: {winning_team}")
        
        # Generate final PGN file
        pgn_file = self.pgn_tracker.save_match_pgn()
        
        # Export stats
        stats_file = self.stat_tracker.export_stats(
            f"results/stats/match_{int(time.time())}"
        )
        
        # Create comprehensive match result
        match_result = {
            "team_a_name": match_context["team_a_name"],
            "team_b_name": match_context["team_b_name"],
            "team_a_id": match_context["team_a_id"],
            "team_b_id": match_context["team_b_id"],
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "winner": winner,
            "winning_team": winning_team,
            "character_results": character_results,
            "convergence_count": len(match_context["convergences"]),
            "trait_activations": len(match_context["trait_activations"]),
            "pgn_file": pgn_file,
            "stats_file": stats_file
        }
        
        # Generate narrative report
        report = self._generate_narrative_report(match_result)
        report_path = f"results/reports/{match_context['team_a_id']}_vs_{match_context['team_b_id']}_{int(time.time())}.txt"
        
        with open(report_path, "w") as f:
            f.write(report)
        
        match_result["report_file"] = report_path
        
        return match_result
    
    ###############################
    # HELPER METHODS
    ###############################
    
    def _apply_openings(self, characters, boards):
        """Apply role-based opening moves to boards"""
        for character, board in zip(characters, boards):
            role = character.get("role", "FL")
            
            if role in self.role_openings:
                # Choose a random opening for this role
                opening_sequence = random.choice(self.role_openings[role])
                moves = opening_sequence.split()
                
                # Apply opening moves
                for move_str in moves:
                    try:
                        move = None
                        if len(move_str) == 4 and move_str[0] in 'abcdefgh' and move_str[2] in 'abcdefgh':
                            # This is a UCI move
                            move = chess.Move.from_uci(move_str)
                        else:
                            # This is SAN notation
                            move = board.parse_san(move_str)
                        
                        if move and move in board.legal_moves:
                            board.push(move)
                    except:
                        continue  # Skip invalid moves
    
    def _calculate_material(self, board):
        """Calculate total material value on the board for white"""
        material = 0
        
        # Piece values (standard chess values)
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9
        }
        
        # Sum up material for white pieces
        for piece_type in values:
            material += len(board.pieces(piece_type, chess.WHITE)) * values[piece_type]
        
        return material
    
    def _select_move(self, board, character):
        """Select a move for a character based on their abilities"""
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        # Default to random selection if no other method available
        return random.choice(legal_moves)
    
    def _apply_material_effects(self, character, material_change, show_details=False):
        """Apply effects from material changes to a character"""
        # Material loss = damage
        if material_change < 0:
            base_damage = abs(material_change) * self.DAMAGE_SCALING
            
            # Safety cap on damage
            if base_damage > self.MAX_DAMAGE_PER_HIT:
                base_damage = self.MAX_DAMAGE_PER_HIT
            
            # Apply damage reduction from traits and stats
            reduction = self.BASE_DAMAGE_REDUCTION
            
            # DUR/RES bonus
            dur_bonus = max(0, character.get("aDUR", 5) - 5) * 3  # +3% per point above 5
            res_bonus = max(0, character.get("aRES", 5) - 5) * 2  # +2% per point above 5
            
            reduction += (dur_bonus + res_bonus)
            
            # Trait-based reduction
            for trait_name in character.get("traits", []):
                if trait_name in self.traits:
                    trait = self.traits[trait_name]
                    if "damage_reduction" in trait.get("formula_key", ""):
                        reduction += trait.get("value", 0)
            
            # Cap reduction
            reduction = min(reduction, self.MAX_DAMAGE_REDUCTION)
            
            # Apply reduction
            actual_damage = base_damage * (1 - reduction/100.0)
            
            # Apply to HP
            old_hp = character.get("HP", 100)
            new_hp = max(0, old_hp - actual_damage)
            character["HP"] = new_hp
            
            # Track damage in stats
            character.setdefault("rStats", {})
            character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + actual_damage
            
            # Handle stamina impact if HP is depleted
            if new_hp == 0:
                old_stamina = character.get("stamina", 100)
                # Use 30% of leftover damage against stamina
                stamina_damage = (actual_damage - old_hp) * 0.3
                new_stamina = max(0, old_stamina - stamina_damage)
                character["stamina"] = new_stamina
                
                # If both HP and stamina are zero, character is KO'd
                if new_stamina == 0:
                    character["is_ko"] = True
                    
                    if show_details:
                        print(f"  {character['name']} is KNOCKED OUT!")
            
            if show_details:
                print(f"  {character['name']} took {actual_damage:.1f} damage (HP: {new_hp:.1f})")
        
        # Material gain = damage dealt to opponent
        elif material_change > 0:
            # Track damage dealt for stats
            damage_equivalent = material_change * self.DAMAGE_SCALING
            
            character.setdefault("rStats", {})
            character["rStats"]["rDD"] = character["rStats"].get("rDD", 0) + damage_equivalent
            
            if show_details:
                print(f"  {character['name']} gained material advantage: +{material_change}")
        
        # Apply small stamina cost for moving
        stamina_cost = 1  # Base cost
        
        # Apply WIL bonus to reduce stamina cost
        wil_bonus = max(0, character.get("aWIL", 5) - 5) * 0.05  # 5% reduction per point above 5
        stamina_cost *= max(0.5, 1 - wil_bonus)  # Cap at 50% reduction
        
        character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
    
    def _process_convergences(self, team_a, team_a_boards, team_b, team_b_boards, match_context, show_details=False):
        """Process convergences between boards"""
        convergences = []
        
        # Track convergence counts per character
        char_convergence_counts = {char.get("id", f"A{i}"): 0 for i, char in enumerate(team_a)}
        char_convergence_counts.update({char.get("id", f"B{i}"): 0 for i, char in enumerate(team_b)})
        
        # Check for piece overlaps across boards
        for a_idx, (a_char, a_board) in enumerate(zip(team_a, team_a_boards)):
            # Skip KO'd characters
            if a_char.get("is_ko", False):
                continue
                
            # Skip if reached max convergences
            char_id_a = a_char.get("id", f"A{a_idx}")
            if char_convergence_counts[char_id_a] >= self.MAX_CONVERGENCES_PER_CHAR:
                continue
                
            for b_idx, (b_char, b_board) in enumerate(zip(team_b, team_b_boards)):
                # Skip KO'd characters
                if b_char.get("is_ko", False):
                    continue
                
                # Skip if reached max convergences
                char_id_b = b_char.get("id", f"B{b_idx}")
                if char_convergence_counts[char_id_b] >= self.MAX_CONVERGENCES_PER_CHAR:
                    continue
                
                # Check for non-pawn pieces on same square
                for square in chess.SQUARES:
                    a_piece = a_board.piece_at(square)
                    b_piece = b_board.piece_at(square)
                    
                    if (a_piece and b_piece and 
                        a_piece.piece_type != chess.PAWN and 
                        b_piece.piece_type != chess.PAWN):
                        
                        # Calculate combat rolls
                        a_roll = self._calculate_combat_roll(a_char, b_char)
                        b_roll = self._calculate_combat_roll(b_char, a_char)
                        
                        # Apply trait bonuses to rolls
                        a_bonus = self._apply_trait_bonus(a_char, "convergence")
                        b_bonus = self._apply_trait_bonus(b_char, "convergence")
                        
                        a_roll += a_bonus
                        b_roll += b_bonus
                        
                        # Determine winner
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
                        
                        # Calculate damage
                        base_damage = max(1, int(self.DAMAGE_SCALING * roll_diff / 10))
                        
                        # Apply damage reduction from traits
                        reduction = self.BASE_DAMAGE_REDUCTION
                        trait_reduction = self._apply_trait_bonus(loser, "damage_reduction")
                        
                        # Apply the loser's trait-based damage reduction
                        reduction += trait_reduction
                        reduction = min(reduction, self.MAX_DAMAGE_REDUCTION)
                        
                        # Apply reduction and calculate final damage
                        reduced_damage = base_damage * (1 - reduction/100.0)
                        
                        # Cap damage at maximum
                        reduced_damage = min(reduced_damage, self.MAX_DAMAGE_PER_HIT)
                        
                        # Apply damage to loser
                        self._apply_damage(loser, reduced_damage, source_character=winner, show_details=False)
                        
                        # Record convergence data
                        convergence_data = {
                            "square": chess.square_name(square),
                            "a_character": a_char.get("name", f"Character A{a_idx}"),
                            "b_character": b_char.get("name", f"Character B{b_idx}"),
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "winner": winner.get("name", "Unknown"),
                            "loser": loser.get("name", "Unknown"),
                            "damage": base_damage,
                            "reduced_damage": reduced_damage,
                            "outcome": outcome
                        }
                        
                        convergences.append(convergence_data)
                        match_context["convergences"].append(convergence_data)
                        
                        # Update convergence counts
                        char_convergence_counts[char_id_a] += 1
                        char_convergence_counts[char_id_b] += 1
                        
                        # Record stats
                        winner.setdefault("rStats", {})
                        loser.setdefault("rStats", {})
                        
                        # Ultimate move for critical success
                        if outcome == "critical_success":
                            winner["rStats"]["rULT"] = winner["rStats"].get("rULT", 0) + 1
                        
                        # Track in stats based on division
                        winner_division = winner.get("division", "o")
                        if winner_division == "o":
                            winner["rStats"]["rCVo"] = winner["rStats"].get("rCVo", 0) + 1
                        else:
                            winner["rStats"]["rMBi"] = winner["rStats"].get("rMBi", 0) + 1
                        
                        if show_details:
                            print(f"CONVERGENCE: {a_char.get('name', 'A')} ({a_roll}) vs {b_char.get('name', 'B')} ({b_roll}) at {chess.square_name(square)}")
                            print(f"  {winner.get('name', 'Winner')} wins! {loser.get('name', 'Loser')} takes {reduced_damage:.1f} damage")
                            if outcome == "critical_success":
                                print(f"  CRITICAL SUCCESS! {winner.get('name', 'Winner')} executed an Ultimate Move!")
        
        return convergences
    
    def _calculate_combat_roll(self, attacker, defender):
        """Calculate combat roll for convergence"""
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        str_val = attacker.get("aSTR", 5)
        fs_val = attacker.get("aFS", 5)
        
        # Each point above 5 adds 2 to the roll
        str_bonus = max(0, str_val - 5) * 2
        fs_bonus = max(0, fs_val - 5) * 2
        
        roll += str_bonus + fs_bonus
        
        # Scale by Power Potential
        op_factor = attacker.get("aOP", 5) / 5.0
        roll = int(roll * op_factor)
        
        # Role bonuses
        role = attacker.get("role", "")
        if role == "FL":  # Field Leader
            roll += 10  # +10 to rolls
        elif role == "VG":  # Vanguard
            roll += 5   # +5 to rolls
        elif role == "SV":  # Sovereign
            roll += 8   # +8 to rolls
        
        return roll
    
    def _apply_trait_bonus(self, character, trigger_type):
        """Apply trait bonuses for a given trigger"""
        bonus = 0
        
        for trait_name in character.get("traits", []):
            if trait_name in self.traits:
                trait = self.traits[trait_name]
                
                # Check if trait responds to this trigger
                if trigger_type in trait.get("triggers", []):
                    # Check formula key to determine bonus type
                    if trigger_type == "convergence" and trait.get("formula_key") == "bonus_roll":
                        bonus += trait.get("value", 0)
                    elif trigger_type == "damage_reduction" and trait.get("formula_key") == "damage_reduction":
                        bonus += trait.get("value", 0)
        
        return bonus
    
    def _apply_damage(self, character, damage, source_character=None, show_details=False):
        """Apply damage to a character"""
        # Apply to HP first
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - damage)
        character["HP"] = new_hp
        
        # Track damage in stats
        character.setdefault("rStats", {})
        character["rStats"]["rDS"] = character["rStats"].get("rDS", 0) + damage
        
        if source_character:
            source_character.setdefault("rStats", {})
            source_character["rStats"]["rDD"] = source_character["rStats"].get("rDD", 0) + damage
        
        # Check for KO
        if new_hp == 0:
            # Apply damage to stamina (30% of overflow)
            stamina_damage = (damage - current_hp) * 0.3
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # If both HP and stamina are zero, character is KO'd
            if new_stamina == 0:
                character["is_ko"] = True
                
                # Record KO in stats
                if source_character:
                    source_character.setdefault("rStats", {})
                    source_character["rStats"]["rOTD"] = source_character["rStats"].get("rOTD", 0) + 1
                
                if show_details:
                    print(f"  {character.get('name', 'Character')} is KNOCKED OUT!")
        
        return {
            "damage": damage,
            "new_hp": new_hp,
            "is_ko": character.get("is_ko", False)
        }
    
    def _apply_end_of_round_effects(self, characters, match_context, show_details=False):
        """Apply end-of-round effects to all characters"""
        for character in characters:
            # Skip KO'd characters
            if character.get("is_ko", False):
                continue
            
            # HP regeneration
            hp_regen = self.HP_REGEN_RATE
            
            # Healing from traits
            trait_healing = 0
            for trait_name in character.get("traits", []):
                if trait_name in self.traits:
                    trait = self.traits[trait_name]
                    if "end_of_turn" in trait.get("triggers", []) and trait.get("formula_key") == "heal":
                        trait_healing += trait.get("value", 0)
                        
                        # Track trait activation
                        match_context["trait_activations"].append({
                            "round": match_context["round"],
                            "character": character.get("name", "Unknown"),
                            "trait": trait.get("name", trait_name),
                            "effect": "healing"
                        })
            
            # Apply healing
            total_healing = hp_regen + trait_healing
            if character["HP"] < 100:
                old_hp = character.get("HP", 0)
                character["HP"] = min(100, old_hp + total_healing)
                
                if trait_healing > 0:
                    character.setdefault("rStats", {})
                    character["rStats"]["rHLG"] = character["rStats"].get("rHLG", 0) + trait_healing
            
            # Stamina regeneration
            stamina_regen = self.STAMINA_REGEN_RATE
            
            # Apply willpower bonus to stamina regen
            wil_bonus = max(0, character.get("aWIL", 5) - 5) * 0.8  # +0.8 per point above 5
            stamina_regen += wil_bonus
            
            character["stamina"] = min(100, character.get("stamina", 0) + stamina_regen)
            
            if show_details and (total_healing > 0 or stamina_regen > 0):
                print(f"  {character.get('name', 'Character')} recovered HP: +{total_healing:.1f}, Stamina: +{stamina_regen:.1f}")
    
    def _check_team_loss_conditions(self, team):
        """Check if a team has met any loss conditions"""
        # Condition 1: Field Leader KO'd
        field_leader = next((char for char in team if char.get("role") == "FL"), None)
        if field_leader and field_leader.get("is_ko", False):
            return True
        
        # Condition 2: KO count >= 3
        ko_count = sum(1 for char in team if char.get("is_ko", False))
        if ko_count >= 3:  # Reduced from 5 to make matches shorter
            return True
        
        return False
    
    def _determine_game_result(self, board, character):
        """Determine the result of a chess game"""
        # If character is KO'd, they lose
        if character.get("is_ko", False):
            return "loss"
            
        # Check chess rules for game over
        if board.is_checkmate():
            return "win" if board.turn == chess.BLACK else "loss"
        elif board.is_stalemate() or board.is_insufficient_material():
            return "draw"
        
        # Otherwise, use material advantage to estimate result
        material = self._calculate_material(board)
        starting_material = 39  # Standard starting material
        
        if material > starting_material * 0.7:
            return "win"
        elif material < starting_material * 0.3:
            return "loss"
        else:
            return "draw"
    
    def _record_batch_pgn(self, team_a, team_a_boards, team_b, team_b_boards, match_context, batch_end):
        """Record PGN data for the current batch"""
        # Record games for team A
        for character, board in zip(team_a, team_a_boards):
            # Skip if dead
            if character.get("is_dead", False):
                continue
            
            # Determine result status
            if character.get("is_ko", False):
                result = "loss"
            elif board.is_checkmate():
                result = "win" if board.turn == chess.BLACK else "loss"
            elif board.is_stalemate():
                result = "draw"
            else:
                result = "ongoing"
            
            # Record the game
            self.pgn_tracker.record_game(
                board, 
                character, 
                opponent_name=f"{match_context['team_b_name']} AI", 
                result=result
            )
        
        # Record games for team B
        for character, board in zip(team_b, team_b_boards):
            # Skip if dead
            if character.get("is_dead", False):
                continue
            
            # Determine result status
            if character.get("is_ko", False):
                result = "loss"
            elif board.is_checkmate():
                result = "win" if board.turn == chess.BLACK else "loss"
            elif board.is_stalemate():
                result = "draw"
            else:
                result = "ongoing"
            
            # Record the game
            self.pgn_tracker.record_game(
                board, 
                character, 
                opponent_name=f"{match_context['team_a_name']} AI", 
                result=result
            )
    
    def _generate_narrative_report(self, match_result):
        """Generate a narrative report for the match"""
        team_a_name = match_result["team_a_name"]
        team_b_name = match_result["team_b_name"]
        team_a_wins = match_result["team_a_wins"]
        team_b_wins = match_result["team_b_wins"]
        winner = match_result["winner"]
        winning_team = match_result["winning_team"]
        
        # Create report sections
        if abs(team_a_wins - team_b_wins) <= 1:
            match_type = "close"
            intro = f"In a nail-biting contest, {winning_team} narrowly claimed victory."
        else:
            match_type = "decisive"
            intro = f"{winning_team} demonstrated clear dominance in this match."
        
        # Find key performers
        top_damage = {"name": "Unknown", "damage": 0}
        top_kos = {"name": "Unknown", "kos": 0}
        
        for char in match_result["character_results"]:
            # Check damage
            damage = 0
            if "rStats" in char:
                damage = char["rStats"].get("rDD", 0)
            
            if damage > top_damage["damage"]:
                top_damage = {"name": char["character_name"], "damage": damage}
            
            # Check KOs
            kos = 0
            if "rStats" in char:
                kos = char["rStats"].get("rOTD", 0)
            
            if kos > top_kos["kos"]:
                top_kos = {"name": char["character_name"], "kos": kos}
        
        # Build report
        report = f"""
=== META FANTASY LEAGUE MATCH REPORT ===
{team_a_name} vs {team_b_name}
Final Score: {team_a_wins}-{team_b_wins}

{intro}

KEY PERFORMERS:
- {top_damage['name']} led the offensive charge with {top_damage['damage']:.0f} damage dealt
- {top_kos['name']} secured {top_kos['kos']} takedowns, a crucial contribution to the match

MATCH STATISTICS:
- Convergences: {match_result['convergence_count']}
- Trait Activations: {match_result['trait_activations']}

CHARACTER OUTCOMES:
"""
        
        # Add character summaries
        team_a_chars = [c for c in match_result["character_results"] if c["team"] == "A"]
        team_b_chars = [c for c in match_result["character_results"] if c["team"] == "B"]
        
        report += f"{team_a_name}:\n"
        for char in team_a_chars:
            status = "KO'd" if char["is_ko"] else "Active"
            hp = char["final_hp"]
            report += f"- {char['character_name']} ({char['role']}): {status}, HP: {hp:.1f}\n"
        
        report += f"\n{team_b_name}:\n"
        for char in team_b_chars:
            status = "KO'd" if char["is_ko"] else "Active"
            hp = char["final_hp"]
            report += f"- {char['character_name']} ({char['role']}): {status}, HP: {hp:.1f}\n"
        
        # Add conclusion
        if match_type == "close":
            conclusion = f"Both teams showcased exceptional skill and strategy, with {winning_team} securing victory by the narrowest of margins."
        else:
            conclusion = f"The decisive performance by {winning_team} firmly established their superiority in this contest."
        
        report += f"\nCONCLUSION:\n{conclusion}\n"
        
        return report
    
    ###############################
    # DATA LOADING METHODS
    ###############################
    
    def load_lineups_from_excel(self, file_path, day_sheet="4/7/25"):
        """Load character lineups from an Excel file"""
        try:
            print(f"Attempting to load from: {file_path}")
            
            # First check if file exists
            if not os.path.exists(file_path):
                print(f"Error: File '{file_path}' does not exist")
                raise FileNotFoundError(f"File '{file_path}' does not exist")
            
            # Get sheet names
            xls = pd.ExcelFile(file_path)
            available_sheets = xls.sheet_names
            print(f"Available sheets: {available_sheets}")
            
            # Find a matching sheet
            day_sheet_clean = day_sheet.replace('/', '')
            matching_sheets = [s for s in available_sheets if day_sheet_clean in s.replace('/', '').replace('-', '')]
            
            if day_sheet in available_sheets:
                selected_sheet = day_sheet
            elif matching_sheets:
                selected_sheet = matching_sheets[0]
            else:
                # Fall back to first sheet
                selected_sheet = available_sheets[0]
            
            print(f"Using sheet: {selected_sheet}")
            
            # Load data
            df = pd.read_excel(file_path, sheet_name=selected_sheet)
            print(f"Columns: {df.columns.tolist()}")
            
            # Map columns
            column_mapping = {
                'team_id': ['Team', 'team_id', 'team', 'team id', 'teamid', 'tid'],
                'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name'],
                'role': ['Position', 'PositionFull', 'role', 'position', 'char_role', 'character_role']
            }
            
            # Find required columns
            for required_col, possible_cols in column_mapping.items():
                found = False
                for col in possible_cols:
                    if col in df.columns:
                        print(f"Mapping '{col}' to '{required_col}'")
                        df[required_col] = df[col]
                        found = True
                        break
                
                if not found:
                    raise ValueError(f"Could not find column for '{required_col}'")
            
            # Organize by teams
            teams = {}
            
            for _, row in df.iterrows():
                # Skip empty rows
                if pd.isna(row.get('team_id', None)) or pd.isna(row.get('name', None)):
                    continue
                
                team_id = str(row.get('team_id', '')).strip()
                
                # Clean team_id
                if team_id.endswith('.0'):
                    team_id = team_id[:-2]
                
                # Ensure team_id starts with 't'
                if not team_id.lower().startswith('t'):
                    team_id = 't' + team_id
                
                # Initialize team if needed
                if team_id not in teams:
                    teams[team_id] = []
                
                # Get character attributes
                char_name = str(row.get('name', f"Character {len(teams[team_id])}")).strip()
                role = str(row.get('role', 'FL')).strip()
                
                # Get team name
                if 'Team' in df.columns and not pd.isna(row.get('Team')):
                    team_name = f"Team {row.get('Team')}"
                else:
                    team_name = f"Team {team_id[1:]}"
                
                # Map role to standardized code
                role = self._map_position_to_role(role)
                division = self._get_division_from_role(role)
                
                # Create character
                character = {
                    'id': f"{team_id}_{len(teams[team_id])}",
                    'name': char_name,
                    'team_id': team_id,
                    'team_name': team_name,
                    'role': role,
                    'division': division,
                    'HP': 100,
                    'stamina': 100,
                    'life': 100,
                    'morale': 50,
                    'traits': [],
                    'rStats': {},
                    'xp_total': 0
                }
                
                # Add stats
                for stat in ['STR', 'SPD', 'FS', 'LDR', 'DUR', 'RES', 'WIL', 'OP', 'AM', 'SBY']:
                    character[f"a{stat}"] = 5
                
                # Try to get Rank for stats
                if 'Rank' in df.columns and not pd.isna(row.get('Rank')):
                    try:
                        rank = int(row.get('Rank'))
                        stat_value = min(10, max(1, rank))
                        character["aSTR"] = stat_value
                        character["aSPD"] = stat_value
                        character["aOP"] = stat_value
                    except:
                        pass
                
                # Assign traits
                if 'Primary Type' in df.columns and not pd.isna(row.get('Primary Type')):
                    primary_type = str(row.get('Primary Type')).lower()
                    
                    # Map types to traits
                    type_to_trait = {
                        'tech': ['genius', 'armor'],
                        'energy': ['genius', 'tactical'],
                        'cosmic': ['shield', 'healing'],
                        'mutant': ['agile', 'stretchy'],
                        'bio': ['agile', 'spider-sense'],
                        'mystic': ['tactical', 'healing'],
                        'skill': ['tactical', 'spider-sense']
                    }
                    
                    for type_key, traits in type_to_trait.items():
                        if type_key in primary_type:
                            character['traits'] = traits
                            break
                    
                    if not character['traits']:
                        character['traits'] = ['genius', 'tactical']
                else:
                    character['traits'] = ['genius', 'tactical']
                
                teams[team_id].append(character)
            
            print(f"Loaded {sum(len(team) for team in teams.values())} characters across {len(teams)} teams")
            
            return teams
            
        except Exception as e:
            print(f"Error loading lineups: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _map_position_to_role(self, position):
        """Map position to standardized role code"""
        position = str(position).upper().strip()
        
        position_map = {
            "FIELD LEADER": "FL",
            "VANGUARD": "VG",
            "ENFORCER": "EN",
            "RANGER": "RG",
            "GHOST OPERATIVE": "GO",
            "PSI OPERATIVE": "PO",
            "SOVEREIGN": "SV"
        }
        
        if position in position_map:
            return position_map[position]
        
        for key, value in position_map.items():
            if key in position:
                return value
        
        valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
        if position in valid_roles:
            return position
        
        return "FL"
    
    def _get_division_from_role(self, role):
        """Map role to division"""
        operations_roles = ["FL", "VG", "EN"]
        intelligence_roles = ["RG", "GO", "PO", "SV"]
        
        if role in operations_roles:
            return "o"
        elif role in intelligence_roles:
            return "i"
        
        return "o"
    
    def create_team_matchups(self, teams, day_number=1, randomize=False):
        """Create balanced team matchups for simulation"""
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
            # Day-based matchups
            day_matchups = {
                1: [
                    ("t001", "t002"),
                    ("t004", "t003"),
                    ("t005", "t006"),
                    ("t008", "t007"),
                    ("t009", "t010")
                ],
                # Day 2: Rotate for different matchups
                2: [
                    ("t001", "t003"),
                    ("t004", "t006"),
                    ("t005", "t007"),
                    ("t008", "t010"),
                    ("t009", "t002")
                ],
                # Day 3: Another rotation
                3: [
                    ("t001", "t006"),
                    ("t004", "t007"),
                    ("t005", "t010"),
                    ("t008", "t002"),
                    ("t009", "t003")
                ],
                # Day 4
                4: [
                    ("t001", "t007"),
                    ("t004", "t010"),
                    ("t005", "t002"),
                    ("t008", "t003"),
                    ("t009", "t006")
                ],
                # Day 5
                5: [
                    ("t001", "t010"),
                    ("t004", "t002"),
                    ("t005", "t003"),
                    ("t008", "t006"),
                    ("t009", "t007")
                ]
            }
            
            # Use day-based matchups if available, otherwise fall back to random
            if day_number in day_matchups:
                matchups = []
                for a, b in day_matchups[day_number]:
                    # Normalize team IDs
                    a = a.lower()
                    b = b.lower()
                    
                    # Only add matchup if both teams exist
                    if a in all_team_ids and b in all_team_ids:
                        matchups.append((a, b))
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

#####################################
# PGN TRACKING SYSTEM
#####################################
class PGNTracker:
    """System for recording chess games in PGN format with character metadata"""
    
    def __init__(self, output_dir="results/pgn"):
        """Initialize the PGN tracker"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        self.game_count = 0
        self.current_match = None
    
    def start_match(self, team_a_name, team_b_name, team_a_id, team_b_id, day=1):
        """Start tracking a new match"""
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
        print(f"PGNTracker: Started match {team_a_name} vs {team_b_name}")
    
    def record_game(self, board, character_data, opponent_name="AI Opponent", result="unknown"):
        """Record a chess game in PGN format"""
        if not self.current_match:
            print("ERROR: No active match. Call start_match() first")
            return ""
        
        # Create a new game
        game = chess.pgn.Game()
        
        # Set headers
        game.headers["Event"] = f"META Fantasy League - Day {self.current_match['day']}"
        game.headers["Site"] = "META League Arena"
        game.headers["Date"] = self.current_match["date"].strftime("%Y.%m.%d")
        game.headers["Round"] = str(self.game_count + 1)
        game.headers["White"] = character_data.get("name", "Unknown")
        game.headers["Black"] = opponent_name
        
        # Set result
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
        
        # Add custom tags
        game.headers["CharacterID"] = character_data.get("id", "Unknown")
        game.headers["TeamID"] = character_data.get("team_id", "Unknown")
        
        # Add character stats
        game.headers["InitialHP"] = str(100)
        game.headers["InitialStamina"] = str(100)
        game.headers["FinalHP"] = str(character_data.get("HP", 0))
        game.headers["FinalStamina"] = str(character_data.get("stamina", 0))
        
        # Add comment
        char_info = f"Character: {character_data.get('name', 'Unknown')}, "
        char_info += f"Role: {character_data.get('role', 'Unknown')}, "
        char_info += f"Team: {character_data.get('team_name', 'Unknown')}"
        game.comment = char_info
        
        # Add moves from board history
        if board.move_stack:
            node = game
            for move in board.move_stack:
                node = node.add_variation(move)
        else:
            print(f"WARNING: No moves in board for {character_data.get('name', 'Unknown')}")
        
        # Convert to PGN text
        pgn_string = io.StringIO()
        exporter = chess.pgn.FileExporter(pgn_string)
        game.accept(exporter)
        pgn_text = pgn_string.getvalue()
        
        # Store game
        self.current_match["games"].append({
            "character_id": character_data.get("id", "Unknown"),
            "character_name": character_data.get("name", "Unknown"),
            "pgn": pgn_text,
            "result": result
        })
        
        self.game_count += 1
        
        return pgn_text
    
    def save_match_pgn(self, filename=None):
        """Save all games to a PGN file"""
        if not self.current_match:
            print("ERROR: No active match to save")
            return "error_no_active_match.pgn"
        
        # Generate filename
        if not filename:
            team_a_id = self.current_match["team_a_id"]
            team_b_id = self.current_match["team_b_id"]
            filename = f"day{self.current_match['day']}_{team_a_id}_vs_{team_b_id}_{int(time.time())}.pgn"
        
        # Ensure .pgn extension
        if not filename.endswith(".pgn"):
            filename += ".pgn"
        
        # Create full path
        file_path = os.path.join(self.output_dir, filename)
        
        # Write games to file
        with open(file_path, "w") as f:
            # Write header
            f.write(f"% META Fantasy League - Day {self.current_match['day']} - Complete Match\n")
            f.write(f"% {self.current_match['team_a_name']} vs {self.current_match['team_b_name']}\n")
            f.write(f"% Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Write each game
            for game in self.current_match["games"]:
                f.write(game["pgn"])
                f.write("\n\n")
        
        print(f"Saved {self.game_count} games to {file_path}")
        return file_path

#####################################
# STAT TRACKING SYSTEM
#####################################
class StatTracker:
    """System for tracking character and team statistics"""
    
    def __init__(self):
        """Initialize the stat tracker"""
        self.character_stats = {}
        self.team_stats = {}
    
    def register_character(self, character):
        """Register a character for stat tracking"""
        char_id = character.get("id", "unknown")
        
        if char_id not in self.character_stats:
            # Continuing from where we left off in the StatTracker class
            self.character_stats[char_id] = {
                "id": char_id,
                "name": character.get("name", "Unknown"),
                "team_id": character.get("team_id", "unknown"),
                "role": character.get("role", "Unknown"),
                "division": character.get("division", "o"),
                "matches": 0,
                "wins": 0,
                "losses": 0,
                "draws": 0
            }
            
            # Register team if needed
            team_id = character.get("team_id", "unknown")
            if team_id not in self.team_stats:
                self.team_stats[team_id] = {
                    "team_id": team_id,
                    "team_name": character.get("team_name", "Unknown Team"),
                    "matches": 0,
                    "wins": 0,
                    "losses": 0,
                    "draws": 0,
                    "characters": []
                }
            
            # Add character to team roster
            if char_id not in self.team_stats[team_id]["characters"]:
                self.team_stats[team_id]["characters"].append(char_id)
    
    def record_match_result(self, character, result):
        """Record match result for a character"""
        char_id = character.get("id", "unknown")
        team_id = character.get("team_id", "unknown")
        
        # Update character stats
        if char_id in self.character_stats:
            self.character_stats[char_id]["matches"] += 1
            
            if result == "win":
                self.character_stats[char_id]["wins"] += 1
            elif result == "loss":
                self.character_stats[char_id]["losses"] += 1
            elif result == "draw":
                self.character_stats[char_id]["draws"] += 1
        
        # Update team stats
        if team_id in self.team_stats:
            # Team match results are tracked separately based on team-level outcomes
            pass
    
    def record_team_result(self, team_id, result):
        """Record match result for a team"""
        if team_id in self.team_stats:
            self.team_stats[team_id]["matches"] += 1
            
            if result == "win":
                self.team_stats[team_id]["wins"] += 1
            elif result == "loss":
                self.team_stats[team_id]["losses"] += 1
            elif result == "draw":
                self.team_stats[team_id]["draws"] += 1
    
    def update_character_stat(self, char_id, stat_name, value, operation="add"):
        """Update a specific stat for a character"""
        # Ensure rStat names start with 'r'
        if not stat_name.startswith('r'):
            stat_name = 'r' + stat_name
        
        if char_id in self.character_stats:
            if operation == "add":
                if stat_name not in self.character_stats[char_id]:
                    self.character_stats[char_id][stat_name] = 0
                self.character_stats[char_id][stat_name] += value
            elif operation == "set":
                self.character_stats[char_id][stat_name] = value
            elif operation == "max":
                if stat_name not in self.character_stats[char_id]:
                    self.character_stats[char_id][stat_name] = value
                else:
                    self.character_stats[char_id][stat_name] = max(
                        self.character_stats[char_id][stat_name],
                        value
                    )
    
    def update_team_stat(self, team_id, stat_name, value, operation="add"):
        """Update a specific stat for a team"""
        # Ensure team stat names start with 't'
        if not stat_name.startswith('t'):
            stat_name = 't' + stat_name
        
        if team_id in self.team_stats:
            if operation == "add":
                if stat_name not in self.team_stats[team_id]:
                    self.team_stats[team_id][stat_name] = 0
                self.team_stats[team_id][stat_name] += value
            elif operation == "set":
                self.team_stats[team_id][stat_name] = value
            elif operation == "max":
                if stat_name not in self.team_stats[team_id]:
                    self.team_stats[team_id][stat_name] = value
                else:
                    self.team_stats[team_id][stat_name] = max(
                        self.team_stats[team_id][stat_name],
                        value
                    )
    
    def export_stats(self, output_path=None):
        """Export all stats to CSV files"""
        # Create default output path if needed
        timestamp = int(time.time())
        if output_path is None:
            output_path = f"results/stats/stats_{timestamp}"
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Export character stats
        char_path = f"{output_path}_characters.csv"
        
        with open(char_path, "w", newline="") as f:
            # Get all stat fields
            all_fields = set()
            for stats in self.character_stats.values():
                all_fields.update(stats.keys())
            
            # Remove basic fields that should come first
            base_fields = ["id", "name", "team_id", "role", "division", "matches", "wins", "losses", "draws"]
            stat_fields = sorted([f for f in all_fields if f not in base_fields])
            
            # Create writer with all fields
            import csv
            writer = csv.DictWriter(f, fieldnames=base_fields + stat_fields)
            writer.writeheader()
            
            # Write character stats
            for char_id, stats in self.character_stats.items():
                writer.writerow(stats)
        
        # Export team stats
        team_path = f"{output_path}_teams.csv"
        
        with open(team_path, "w", newline="") as f:
            # Get all stat fields
            all_fields = set()
            for stats in self.team_stats.values():
                all_fields.update(stats.keys())
            
            # Remove basic fields that should come first
            base_fields = ["team_id", "team_name", "matches", "wins", "losses", "draws"]
            stat_fields = sorted([f for f in all_fields if f not in base_fields and f != "characters"])
            
            # Create writer with all fields
            import csv
            writer = csv.DictWriter(f, fieldnames=base_fields + stat_fields)
            writer.writeheader()
            
            # Write team stats
            for team_id, stats in self.team_stats.items():
                # Create a copy without the characters list
                row = {k: v for k, v in stats.items() if k != "characters"}
                writer.writerow(row)
        
        print(f"Exported stats to {char_path} and {team_path}")
        return char_path

#####################################
# COMMAND LINE INTERFACE
#####################################
def main():
    """Main entry point with command line argument parsing"""
    import argparse
    
    parser = argparse.ArgumentParser(description="META Fantasy League Simulator")
    parser.add_argument("--day", type=int, default=1, help="Match day number (1-5)")
    parser.add_argument("--lineup", type=str, default="data/lineups/All Lineups 1.xlsx", 
                        help="Path to lineup Excel file")
    parser.add_argument("--stockfish", type=str, default=None,
                        help="Path to Stockfish engine executable")
    parser.add_argument("--quiet", action="store_true", 
                        help="Hide detailed output")
    parser.add_argument("--randomize", action="store_true",
                        help="Use randomized matchups instead of day-based ones")
    
    args = parser.parse_args()
    
    # Initialize simulator
    simulator = MetaLeagueSimulator(stockfish_path=args.stockfish)
    
    # Run matchday
    simulator.run_matchday(
        day_number=args.day,
        lineup_file=args.lineup,
        show_details=not args.quiet
    )

if __name__ == "__main__":
    main()