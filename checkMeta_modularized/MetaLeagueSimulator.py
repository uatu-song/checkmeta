"""
META Fantasy League Simulator - Core Implementation
A simulation system for superhero team battles using chess as the underlying mechanic.
"""

import chess
import chess.engine
import random
import json
import os
import datetime
import math
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
import copy

# Utility functions
def get_division_from_role(role: str) -> str:
    """Map role codes to divisions (operations or intelligence)"""
    operations_roles = ["FL", "VG", "EN"]
    intelligence_roles = ["RG", "GO", "PO", "SV"]
    
    if role in operations_roles:
        return "o"
    elif role in intelligence_roles:
        return "i"
    else:
        return "o"  # Default to operations

def map_position_to_role(position: str) -> str:
    """Map position names to standardized role codes"""
    position = str(position).upper().strip()
    
    # Standard position mappings
    position_map = {
        "FIELD LEADER": "FL",
        "VANGUARD": "VG",
        "ENFORCER": "EN",
        "RANGER": "RG",
        "GHOST OPERATIVE": "GO",
        "PSI OPERATIVE": "PO",
        "SOVEREIGN": "SV"
    }
    
    # Check for exact matches
    if position in position_map:
        return position_map[position]
    
    # Check for partial matches
    for key, value in position_map.items():
        if key in position:
            return value
    
    # Check if already a valid role code
    valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    if position in valid_roles:
        return position
    
    # Default
    return "FL"


class MetaLeagueSimulator:
    def __init__(self, stockfish_path="/usr/local/bin/stockfish"):
        """Initialize the simulator and load required data"""
        self.stockfish_path = stockfish_path
        
        # Check if Stockfish is available
        if not os.path.exists(stockfish_path):
            print(f"Warning: Stockfish not found at {stockfish_path}")
            self.stockfish_available = False
        else:
            self.stockfish_available = True
            print(f"Stockfish found at {stockfish_path}")
        
        # Game state
        self.current_day = 1
        
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
        
        # Create results directory
        os.makedirs("results", exist_ok=True)
        
        # Load traits
        self.traits = self._load_traits()
        
    def load_teams(self, lineup_file, day_sheet):
        """Load teams from lineup file"""
        from data.loaders import load_lineups_from_excel
        return load_lineups_from_excel(lineup_file, day_sheet)
    def _load_traits(self) -> Dict:
        """Load trait definitions - currently hardcoded, could be loaded from file"""
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
    
    def apply_opening(self, board, role):
        """Apply role-based opening moves to a chess board"""
        if role in self.role_openings:
            # Choose a random opening for this role
            opening_sequence = random.choice(self.role_openings[role])
            moves = opening_sequence.split()
            
            # Apply opening moves
            for move_str in moves:
                try:
                    if len(move_str) == 4 and move_str[0] in 'abcdefgh' and move_str[2] in 'abcdefgh':
                        # This is a UCI move
                        move = chess.Move.from_uci(move_str)
                    else:
                        # This is SAN notation
                        move = board.parse_san(move_str)
                    
                    if move in board.legal_moves:
                        board.push(move)
                except Exception as e:
                    continue  # Skip invalid moves
    
    def calculate_material(self, board):
        """Calculate total material value on the chess board"""
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
    
    def simulate_match(self, team_a, team_b, show_details=True):
        """Simulate a match between two teams with Stockfish integration"""
        # Define active roster size
        active_roster_size = 8  # 8 active players, rest on bench
        
        # Get active and bench players
        active_team_a = team_a[:active_roster_size] if len(team_a) > active_roster_size else team_a
        bench_team_a = team_a[active_roster_size:] if len(team_a) > active_roster_size else []
        
        active_team_b = team_b[:active_roster_size] if len(team_b) > active_roster_size else team_b
        bench_team_b = team_b[active_roster_size:] if len(team_b) > active_roster_size else []
        
        # Initialize combat stats for all characters
        self.initialize_combat_stats(active_team_a + bench_team_a + active_team_b + bench_team_b)
        
        # Show team details
        match_context = {
            "day": self.current_day,
            "team_a_id": team_a[0]["team_id"],
            "team_b_id": team_b[0]["team_id"],
            "team_a_name": team_a[0]["team_name"],
            "team_b_name": team_b[0]["team_name"],
            "round": 1,
            "trait_logs": [],
            "convergence_logs": [],
            # Added for parity tracking
            "team_a_momentum": {"state": "stable", "value": 0},
            "team_b_momentum": {"state": "stable", "value": 0},
            "damage_contributors": {}  # Track who damaged whom for assists
        }
        
        if show_details:
            print(f"Match: {match_context['team_a_name']} vs {match_context['team_b_name']}")
            print(f"Team colors: White vs Black")
            print(f"Active players {match_context['team_a_name']}: {[char['name'] for char in active_team_a]}")
            print(f"Bench players {match_context['team_a_name']}: {[char['name'] for char in bench_team_a]}")
            print(f"Active players {match_context['team_b_name']}: {[char['name'] for char in active_team_b]}")
            print(f"Bench players {match_context['team_b_name']}: {[char['name'] for char in bench_team_b]}")
        
        # Create boards for each active character
        team_a_boards = [chess.Board() for _ in active_team_a]
        team_b_boards = [chess.Board() for _ in active_team_b]

        # Add bench teams to match context for substitution tracking
        match_context["bench_team_a"] = bench_team_a
        match_context["bench_team_b"] = bench_team_b
        match_context["substituted_players"] = []
        
        # Apply role-based openings
        for i, character in enumerate(active_team_a):
            self.apply_opening(team_a_boards[i], character.get("role", ""))
        
        for i, character in enumerate(active_team_b):
            self.apply_opening(team_b_boards[i], character.get("role", ""))
        
        # Track material values
        team_a_material = [self.calculate_material(board) for board in team_a_boards]
        team_b_material = [self.calculate_material(board) for board in team_b_boards]
        
        # Maximum moves to simulate
        max_moves = 30
        
        # Simulate moves
        for move_num in range(max_moves):
            match_context["round"] = move_num + 1
            
            if show_details:
                print(f"\nRound {move_num + 1}:")
            
            # Randomize turn order to avoid first-mover bias
            if random.random() < 0.5:
                # Team A goes first
                teams_order = [(active_team_a, team_a_boards, team_a_material, "A"), 
                               (active_team_b, team_b_boards, team_b_material, "B")]
            else:
                # Team B goes first
                teams_order = [(active_team_b, team_b_boards, team_b_material, "B"), 
                               (active_team_a, team_a_boards, team_a_material, "A")]
                
            # Process convergences
            convergences = self.process_convergences(active_team_a, team_a_boards, active_team_b, team_b_boards, match_context, show_details)
            
            # Process round for each team in the randomized order
            for team, boards, material, team_label in teams_order:
                # Update survival stats for all active characters
                for character in team:
                    if not character.get("is_ko", False) and not character.get("is_dead", False):
                        character["combat_stats"]["survival_turns"] += 1
                
                # Process moves for each character
                for i, (character, board) in enumerate(zip(team, boards)):
                    if board.is_game_over() or character.get("is_ko", False) or character.get("is_dead", False):
                        continue
                    
                    # Select and make move
                    move = self.select_move_with_stockfish(board, character)
                    
                    if move:
                        # Process the move
                        if show_details:
                            print(f"{character['name']} moves: {move}")
                        
                        # Make the move
                        board.push(move)
                        
                        # Update material and metrics
                        new_material = self.calculate_material(board)
                        material_change = new_material - material[i]
                        material[i] = new_material
                        
                        # Update character metrics based on material change
                        self.update_character_metrics(character, material_change, match_context, show_details)
                        
                        # Check for KO/death
                        if character["HP"] <= 0 and character["stamina"] <= 0:
                            if character["life"] <= 0:
                                character["is_dead"] = True
                                if show_details:
                                    print(f"  {character['name']} has DIED!")
                            elif character["HP"] <= 0:
                                character["is_ko"] = True
                                if show_details:
                                    print(f"  {character['name']} is KNOCKED OUT!")
            
            # Apply end-of-round effects (trait activations, regen, etc.)
            self.apply_end_of_round_effects(active_team_a + active_team_b, match_context, show_details)
            
            # Check if match is over (all games ended or max moves reached)
            active_games = sum(1 for board, char in zip(team_a_boards, active_team_a)
                             if not board.is_game_over() and 
                                not char.get("is_ko", False) and 
                                not char.get("is_dead", False))
            
            active_games += sum(1 for board, char in zip(team_b_boards, active_team_b)
                              if not board.is_game_over() and 
                                 not char.get("is_ko", False) and 
                                 not char.get("is_dead", False))
            
            if active_games == 0:
                if show_details:
                    print("All games have concluded.")
                break
        
        # Calculate final results
        team_a_wins = 0
        team_b_wins = 0
        character_results = []
        
        # Process active team A results
        for i, (character, board) in enumerate(zip(active_team_a, team_a_boards)):
            result = self.determine_game_result(board, character)
            character_results.append({
                "team": "A",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": result,
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": character.get("is_ko", False),
                "is_dead": character.get("is_dead", False),
                "was_active": True,
                "combat_stats": character["combat_stats"]
            })
            
            if result == "win":
                team_a_wins += 1
                character.setdefault("rStats", {})
                character["rStats"]["rWIN"] = character["rStats"].get("rWIN", 0) + 1
            
            # Calculate XP gain
            self.calculate_xp(character, result)
        

        # Process bench team A results
        for character in bench_team_a:
            was_substituted = character.get("id") in match_context.get("substituted_players", [])
            character_results.append({
                "team": "A",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": "bench" if not was_substituted else self.determine_game_result(None, character),
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": character.get("is_ko", False),
                "is_dead": character.get("is_dead", False),
                "was_active": was_substituted,  # Only True if they were substituted in
                "combat_stats": character.get("combat_stats", {})
            })
        
        # Process active team B results
        for i, (character, board) in enumerate(zip(active_team_b, team_b_boards)):
            result = self.determine_game_result(board, character)
            character_results.append({
                "team": "B",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": "bench" if not was_substituted else self.determine_game_result(None, character),
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": character.get("is_ko", False),
                "is_dead": character.get("is_dead", False),
                "was_active": was_substituted, 
                "combat_stats": character.get("combat_stats", {})
            })
            
            if result == "win":
                team_b_wins += 1
                character.setdefault("rStats", {})
                character["rStats"]["rWIN"] = character["rStats"].get("rWIN", 0) + 1
            
            # Calculate XP gain
            self.calculate_xp(character, result)
        
        # Process bench team B results (they didn't participate)
        for character in bench_team_b:
            character_results.append({
                "team": "B",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": "bench",
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": False,
                "is_dead": False,
                "was_active": False,
                "combat_stats": character["combat_stats"]
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
        
        # Update team morale based on results
        self.update_team_morale(team_a, team_b, winner)
        
        return {
            "team_a_name": match_context["team_a_name"],
            "team_b_name": match_context["team_b_name"],
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "winner": winner,
            "winning_team": winning_team,
            "character_results": character_results,
            "convergence_count": len(match_context["convergence_logs"]),
            "trait_activations": len(match_context["trait_logs"])
        }
    
    def initialize_combat_stats(self, characters):
        """Initialize combat stats for all characters"""
        for character in characters:
            character["combat_stats"] = {
                "damage_dealt": 0,
                "damage_taken": 0,
                "opponent_kos": 0,
                "assists": 0,
                "critical_hits": 0,
                "dodges": 0,
                "tiles_captured": 0,
                "survival_turns": 0,
                "healing_given": 0,
                "healing_received": 0,
                "special_ability_uses": 0
            }
    
    def process_convergences(self, team_a, team_a_boards, team_b, team_b_boards, context, show_details=True):
        """Process convergences between boards with limits to prevent overwhelming numbers"""
        convergences = []
        # Limit convergences per round to prevent overwhelming numbers
        MAX_CONVERGENCES_PER_ROUND = 12
        
        # BALANCE: Limit the number of convergences per round to prevent overwhelming damage
        max_convergences_per_char = 3
        char_convergence_counts = {char["id"]: 0 for char in team_a + team_b}
        
        # Check for non-pawn pieces occupying the same square across different boards
        all_possible_convergences = []
        
        for a_idx, (a_char, a_board) in enumerate(zip(team_a, team_a_boards)):
            # Skip if character is KO'd or dead
            if a_char.get("is_ko", False) or a_char.get("is_dead", False):
                continue
                
            # BALANCE: Skip if character has reached max convergences
            if char_convergence_counts[a_char["id"]] >= max_convergences_per_char:
                continue
                
            for b_idx, (b_char, b_board) in enumerate(zip(team_b, team_b_boards)):
                # Skip if character is KO'd or dead
                if b_char.get("is_ko", False) or b_char.get("is_dead", False):
                    continue
                
                # BALANCE: Skip if character has reached max convergences
                if char_convergence_counts[b_char["id"]] >= max_convergences_per_char:
                    continue
                
                # Find overlapping positions with non-pawn pieces
                for square in chess.SQUARES:
                    a_piece = a_board.piece_at(square)
                    b_piece = b_board.piece_at(square)
                    
                    if (a_piece and b_piece and 
                        a_piece.piece_type != chess.PAWN and 
                        b_piece.piece_type != chess.PAWN):
                        
                        # Calculate combat rolls
                        a_roll = self.calculate_combat_roll(a_char, b_char)
                        b_roll = self.calculate_combat_roll(b_char, a_char)
                        
                        # Apply trait effects for convergence
                        a_traits = self.check_trait_activation(a_char, "convergence", context)
                        for trait_activation in a_traits:
                            trait = self.traits[trait_activation["trait_id"]]
                            if trait.get("formula_key") == "bonus_roll":
                                a_roll += trait.get("value", 0)
                                # Log trait activation
                                context["trait_logs"].append({
                                    "round": context["round"],
                                    "character": a_char["name"],
                                    "trait": trait["name"],
                                    "effect": f"+{trait['value']} to combat roll",
                                    "value": trait["value"]
                                })
                                # Update combat stats
                                a_char["combat_stats"]["special_ability_uses"] += 1
                        
                        b_traits = self.check_trait_activation(b_char, "convergence", context)
                        for trait_activation in b_traits:
                            trait = self.traits[trait_activation["trait_id"]]
                            if trait.get("formula_key") == "bonus_roll":
                                b_roll += trait.get("value", 0)
                                # Log trait activation
                                context["trait_logs"].append({
                                    "round": context["round"],
                                    "character": b_char["name"],
                                    "trait": trait["name"],
                                    "effect": f"+{trait['value']} to combat roll",
                                    "value": trait["value"]
                                })
                                # Update combat stats
                                b_char["combat_stats"]["special_ability_uses"] += 1
                        
                        # Store possible convergence with priority value (difference between rolls)
                        all_possible_convergences.append({
                            "square": square,
                            "a_char": a_char,
                            "b_char": b_char,
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "priority": abs(a_roll - b_roll)  # Higher difference = more dramatic convergence
                        })
        
        # Sort convergences by priority and take only the top ones
        all_possible_convergences.sort(key=lambda x: x["priority"], reverse=True)
        selected_convergences = all_possible_convergences[:MAX_CONVERGENCES_PER_ROUND]
        
        # Process selected convergences
        for idx, conv in enumerate(selected_convergences):
            square = conv["square"]
            a_char = conv["a_char"]
            b_char = conv["b_char"]
            a_roll = conv["a_roll"]
            b_roll = conv["b_roll"]
            
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
            
            # Apply diminishing returns based on convergence index
            damage_factor = 1.0 if idx < 3 else (0.7 if idx < 6 else 0.4)
            
            # BALANCE: Reduce damage from convergences
            # Calculate damage with diminishing returns
            diff = winner_roll - loser_roll
            # Use a logarithmic scale to reduce extreme differences
            base_damage = max(0, int(3 * math.log(1 + diff/10)))
            damage = base_damage * damage_factor
            
            # Apply damage to loser with any damage reduction from traits
            damage_reduction = 0
            damage_reduction_traits = self.check_trait_activation(loser, "damage_taken", context)
            for trait_activation in damage_reduction_traits:
                trait = self.traits[trait_activation["trait_id"]]
                if trait.get("formula_key") == "damage_reduction":
                    damage_reduction += trait.get("value", 0)
                    # Log trait activation
                    context["trait_logs"].append({
                        "round": context["round"],
                        "character": loser["name"],
                        "trait": trait["name"],
                        "effect": f"{trait['value']}% damage reduction",
                        "value": trait["value"]
                    })
                    # Update combat stats
                    loser["combat_stats"]["special_ability_uses"] += 1
            
            # Apply damage with reduction
            actual_damage = self.apply_damage(loser, damage, winner, damage_reduction, context)
            
            # Update convergence counts
            char_convergence_counts[a_char["id"]] += 1
            char_convergence_counts[b_char["id"]] += 1
            
            # Record convergence
            convergence = {
                "square": chess.square_name(square),
                "a_character": a_char["name"],
                "b_character": b_char["name"],
                "a_roll": a_roll,
                "b_roll": b_roll,
                "winner": winner["name"],
                "damage": damage,
                "actual_damage": actual_damage,
                "damage_reduction": damage_reduction
            }
            
            convergences.append(convergence)
            context["convergence_logs"].append(convergence)
            
            # Update tiles captured in combat stats
            winner["combat_stats"]["tiles_captured"] += 1
            
            # Update rStats
            winner.setdefault("rStats", {})
            loser.setdefault("rStats", {})
            
            # Ops or Intel division appropriate stat
            if winner.get("division") == "o":
                winner["rStats"]["rCVo"] = winner["rStats"].get("rCVo", 0) + 1
            else:
                winner["rStats"]["rMBi"] = winner["rStats"].get("rMBi", 0) + 1
            
            if show_details:
                print(f"CONVERGENCE: {a_char['name']} ({a_roll}) vs {b_char['name']} ({b_roll}) at {chess.square_name(square)}")
                print(f"  {winner['name']} wins! {loser['name']} takes {actual_damage} damage (reduced from {damage})")
        
        return convergences
    
    def check_trait_activation(self, character, trigger_type, context=None):
        """Check for trait activation with improved logging for debugging"""
        activated_traits = []
        
        # Skip if character has no traits
        if not character.get("traits"):
            return activated_traits
        
        # Check each trait
        for trait_id in character.get("traits", []):
            if trait_id not in self.traits:
                continue
                
            trait = self.traits[trait_id]
            
            # Check if trigger matches
            triggers = trait.get("triggers", [])
            if trigger_type not in triggers:
                continue
                
            # Calculate activation chance (add randomness to avoid deterministic outcomes)
            # Use character willpower to influence activation chance if available
            base_chance = 0.5  # 50% base chance
            
            # Apply stat bonus if available
            wil_stat = character.get("aWIL", 5)
            stat_bonus = (wil_stat - 5) * 0.05  # 5% per point above 5
            
            # Apply character momentum if available
            momentum_bonus = 0
            if context:
                if character.get("team") == "A" and "team_a_momentum" in context:
                    momentum = context["team_a_momentum"]
                    if momentum["state"] == "crash":
                        momentum_bonus = 0.15  # Bonus for teams in comeback mode
                elif character.get("team") == "B" and "team_b_momentum" in context:
                    momentum = context["team_b_momentum"]
                    if momentum["state"] == "crash":
                        momentum_bonus = 0.15  # Bonus for teams in comeback mode
            
            final_chance = min(0.85, max(0.3, base_chance + stat_bonus + momentum_bonus))
            
            # Random roll for activation
            if random.random() <= final_chance:
                activated_traits.append({
                    "trait_id": trait_id,
                    "effect_type": trait.get("formula_key"),
                    "value": trait.get("value", 0),
                })
        
        return activated_traits
    
    def calculate_combat_roll(self, attacker, defender):
        """Calculate combat roll based on character stats and traits"""
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        roll += attacker.get("aSTR", 5) + attacker.get("aFS", 5)
        
        # Scale by Power Potential
        op_factor = attacker.get("aOP", 5) / 5.0
        roll = int(roll * op_factor)
        
        # Apply momentum factor
        if hasattr(attacker, "team") and attacker["team"] == "A" and "momentum" in attacker:
            if attacker["momentum"]["state"] == "building":
                roll = int(roll * 1.1)  # 10% bonus when in building momentum
            elif attacker["momentum"]["state"] == "crash":
                roll = int(roll * 0.9)  # 10% penalty when crashing
        
        return roll
    
    def apply_damage(self, character, damage, source_character=None, damage_reduction=0, context=None):
        """Apply damage to a character with improved survivability and damage tracking"""
        # BALANCE: Significantly reduce incoming damage
        damage = max(1, damage * 0.3)  # Reduce all damage by 70%
        
        # Apply damage reduction from traits and stats
        # Apply DUR/RES stat bonuses with improved scaling
        dur_bonus = (character.get("aDUR", 5) - 5) * 10  # Increased from 6% to 10% per point
        res_bonus = (character.get("aRES", 5) - 5) * 8  # Increased from 5% to 8% per point
        
        # BALANCE: Increase base damage reduction for all characters
        base_reduction = 30  # Increased from 20%
        reduction = damage_reduction + dur_bonus + res_bonus + base_reduction
        
        # Apply momentum-based damage reduction
        if context:
            if character.get("team") == "A" and "team_a_momentum" in context:
                momentum = context["team_a_momentum"]
                if momentum["state"] == "crash":
                    reduction += 15  # Additional 15% reduction for teams in comeback mode
            elif character.get("team") == "B" and "team_b_momentum" in context:
                momentum = context["team_b_momentum"]
                if momentum["state"] == "crash":
                    reduction += 15  # Additional 15% reduction for teams in comeback mode
        
        # Cap reduction at 85%
        reduction = min(max(0, reduction), 85)
        actual_damage = max(1, damage * (1 - reduction/100.0))
        
        # Apply to HP first with more lenient reduction
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - actual_damage)
        character["HP"] = new_hp
        
        # Update damage stats
        character["combat_stats"]["damage_taken"] += actual_damage
        if source_character:
            source_character["combat_stats"]["damage_dealt"] += actual_damage
            
            # Track damage contributors for assists
            if context and "damage_contributors" in context:
                if character["id"] not in context["damage_contributors"]:
                    context["damage_contributors"][character["id"]] = []
                
                if source_character["id"] not in context["damage_contributors"][character["id"]]:
                    context["damage_contributors"][character["id"]].append(source_character["id"])
        
        # Overflow to stamina if HP is depleted, but at reduced rate
        stamina_damage = 0
        if new_hp == 0:
            # BALANCE: Significantly reduce stamina damage
            stamina_damage = (actual_damage - current_hp) * 0.4  # Reduced from 0.6
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Overflow to life with much higher threshold
            if new_stamina == 0:
                # BALANCE: Make it much harder to lose life
                life_threshold = 100  # Increased from 50
                if stamina_damage > current_stamina + life_threshold:
                    life_damage = 0.5  # Reduced from 1, fractional life loss
                    character["life"] = max(0, character.get("life", 100) - life_damage)
                
                # Check for KO
                character["is_ko"] = True
                if source_character:
                    source_character["combat_stats"]["opponent_kos"] += 1
                    
                    # Award assists
                    if context and "damage_contributors" in context:
                        if character["id"] in context["damage_contributors"]:
                            for contributor_id in context["damage_contributors"][character["id"]]:
                                # Don't count the KO giver as an assist
                                if contributor_id != source_character["id"]:
                                    # Find the contributor character and increment assists
                                    for team_char in context.get("team_a_active", []) + context.get("team_b_active", []):
                                        if team_char["id"] == contributor_id:
                                            team_char["combat_stats"]["assists"] += 1
                                            break
        
        return actual_damage
    
    def update_character_metrics(self, character, material_change, context, show_details=False):
        """Update character metrics based on material change"""
        # Material loss = damage
        if material_change < 0:
            # BALANCE: Reduce damage scaling from material loss
            damage = abs(material_change) * 3  # Reduced from 5 to 3
            self.apply_damage(character, damage, None, 0, context)
            
            # Update rStats for damage sustained
            character.setdefault("rStats", {})
            if character.get("division") == "o":
                character["rStats"]["rDSo"] = character["rStats"].get("rDSo", 0) + damage
            
            if show_details:
                print(f"  {character['name']} HP: {character['HP']}, Stamina: {character['stamina']}, Life: {character['life']}")
        
        # Material gain = damage dealt to opponent
        elif material_change > 0:
            # BALANCE: Reduce damage scaling for stats
            damage_dealt = material_change * 3  # Reduced from 5 to 3
            
            # Update rStats for damage dealt
            character.setdefault("rStats", {})
            if character.get("division") == "o":
                character["rStats"]["rDDo"] = character["rStats"].get("rDDo", 0) + damage_dealt
        
        # BALANCE: Reduce stamina cost for moving
        stamina_cost = 0.5  # Reduced from 1 to 0.5
        
        # Apply WIL bonus to reduce stamina cost with improved scaling
        wil_bonus = (character.get("aWIL", 5) - 5) * 0.08  # 8% reduction per point above 5
        stamina_cost *= max(0.3, 1 - wil_bonus)  # Cap at 70% reduction (was 50%)
        
        character["stamina"] = max(0, character.get("stamina", 100) - stamina_cost)
    
    def apply_end_of_round_effects(self, characters, context, show_details=True):
        """Apply end-of-round effects with improved recovery"""
        # Create temporary team structures for substitution logic
        team_a_active = [char for char in characters if char.get("team", "A") == "A" and not char.get("is_ko", False)]
        team_b_active = [char for char in characters if char.get("team", "B") == "B" and not char.get("is_ko", False)]
        
        # Track substituted Field Leaders
        if "substituted_players" not in context:
            context["substituted_players"] = []
        
        # Check for knocked out Field Leaders and substitute them
        self.check_and_substitute_field_leaders(team_a_active, context["bench_team_a"], "A", context, show_details)
        self.check_and_substitute_field_leaders(team_b_active, context["bench_team_b"], "B", context, show_details)
        
        # Continue with original recovery logic
        for character in characters:
            # Skip dead characters
            if character.get("is_dead", False):
                continue
                        
            # BALANCE: Increase base HP regeneration
            base_hp_regen = 5  # Increased from 3
            
            # Regeneration effects from traits
            trait_heal_amount = 0
            for trait_name in character.get("traits", []):
                if trait_name in self.traits:
                    trait = self.traits[trait_name]
                    if "end_of_turn" in trait.get("triggers", []):
                        if trait.get("formula_key") == "heal":
                            # BALANCE: Boost healing trait effectiveness
                            trait_heal_amount = trait.get("value", 0) * 3  # Tripled healing effect
            
            # Apply total healing
            total_heal = base_hp_regen + trait_heal_amount
            
            # Only heal if not at full HP
            if character.get("HP", 100) < 100:
                old_hp = character.get("HP", 0)
                character["HP"] = min(100, old_hp + total_heal)
                
                # Log healing
                if trait_heal_amount > 0:
                    context["trait_logs"].append({
                        "round": context["round"],
                        "character": character["name"],
                        "trait": "Healing",
                        "effect": f"Healed {character['HP'] - old_hp} HP"
                    })
            
            # BALANCE: Improved stamina regeneration for all characters
            base_regen = 5  # Increased from 3
            
            # Apply WIL bonus to stamina regen
            wil_bonus = max(0, character.get("aWIL", 5) - 5)
            wil_regen = wil_bonus * 0.8  # Increased from 0.5
            
            regen_rate = base_regen + wil_regen
            
            # BALANCE: Much faster recovery from knockdown
            if character.get("is_ko", False):
                # KO'd characters recover faster
                regen_rate *= 3  # Increased from 2
                
                # Improved chance to recover from KO based on stamina
                stamina = character.get("stamina", 0)
                if stamina > 20:  # Lowered threshold from 30
                    # Increased recovery chance
                    recovery_chance = stamina / 150  # 13-66% chance based on stamina
                    if random.random() < recovery_chance:
                        character["is_ko"] = False
                        character["HP"] = max(20, character.get("HP", 0))  # Ensure at least 20 HP
                        if show_details:
                            print(f"  {character['name']} has recovered from knockout!")
            
            character["stamina"] = min(100, character.get("stamina", 0) + regen_rate)

    def check_and_substitute_field_leaders(self, active_team, bench_team, team_id, context, show_details=True):
        """Check for knocked out Field Leaders and substitute them from the bench"""
        # Find any knocked out Field Leaders
        ko_field_leaders = []
        for character in active_team:
            if character.get("role") == "FL" and character.get("is_ko", True):
                ko_field_leaders.append(character)
        
        # If no Field Leaders are knocked out, nothing to do
        if not ko_field_leaders:
            return
        
        for ko_leader in ko_field_leaders:
            # Find a replacement Field Leader on the bench
            replacement = None
            for bench_char in bench_team:
                if bench_char.get("role") == "FL" and not bench_char.get("is_ko", False):
                    replacement = bench_char
                    break
            
            # If no Field Leader found, find character with highest LDR
            if not replacement:
                highest_ldr = -1
                for bench_char in bench_team:
                    ldr = bench_char.get("aLDR", 5)
                    if ldr > highest_ldr and not bench_char.get("is_ko", False):
                        highest_ldr = ldr
                        replacement = bench_char
            
            # If found a replacement, perform the substitution
            if replacement:
                # Remove from bench
                bench_team.remove(replacement)
                # Add to active team
                active_team.append(replacement)
                # Track the substitution
                context["substituted_players"].append(replacement.get("id"))
                # If not already a Field Leader, make them one
                if replacement.get("role") != "FL":
                    replacement["role"] = "FL"
                
                if show_details:
                    print(f"SUBSTITUTION: {ko_leader['name']} (KO'd) replaced by {replacement['name']} as Field Leader")
    
    def update_team_momentum(self, context):
        """Update team momentum based on current match state"""
        # Calculate living characters for each team
        team_a_active = [
            char for char in context.get("team_a_active", [])
            if not char.get("is_ko", False) and not char.get("is_dead", False)
        ]
        
        team_b_active = [
            char for char in context.get("team_b_active", [])
            if not char.get("is_ko", False) and not char.get("is_dead", False)
        ]
        
        team_a_total = len(context.get("team_a_active", []))
        team_b_total = len(context.get("team_b_active", []))
        
        # Calculate percentage of team still active
        team_a_percentage = len(team_a_active) / team_a_total if team_a_total > 0 else 0
        team_b_percentage = len(team_b_active) / team_b_total if team_b_total > 0 else 0
        
        # Initialize momentum if not present
        if "team_a_momentum" not in context:
            context["team_a_momentum"] = {"state": "stable", "value": 0}
        
        if "team_b_momentum" not in context:
            context["team_b_momentum"] = {"state": "stable", "value": 0}
        
        # Update momentum values based on relative team strength
        if team_a_percentage > team_b_percentage + 0.3:  # Team A has 30%+ more active characters
            context["team_a_momentum"]["value"] += 1
            context["team_b_momentum"]["value"] -= 1
        elif team_b_percentage > team_a_percentage + 0.3:  # Team B has 30%+ more active characters
            context["team_b_momentum"]["value"] += 1
            context["team_a_momentum"]["value"] -= 1
        
        # Cap momentum values
        context["team_a_momentum"]["value"] = max(-5, min(5, context["team_a_momentum"]["value"]))
        context["team_b_momentum"]["value"] = max(-5, min(5, context["team_b_momentum"]["value"]))
        
        # Update momentum states
        if context["team_a_momentum"]["value"] >= 3:
            context["team_a_momentum"]["state"] = "building"
        elif context["team_a_momentum"]["value"] <= -3:
            context["team_a_momentum"]["state"] = "crash"
        else:
            context["team_a_momentum"]["state"] = "stable"
            
        if context["team_b_momentum"]["value"] >= 3:
            context["team_b_momentum"]["state"] = "building"
        elif context["team_b_momentum"]["value"] <= -3:
            context["team_b_momentum"]["state"] = "crash"
        else:
            context["team_b_momentum"]["state"] = "stable"
    
    def determine_game_result(self, board, character):
        """Determine the result of a chess game"""
        # If character is KO'd or dead, they lose
        if character.get("is_ko", False) or character.get("is_dead", False):
            return "loss"
            
        # Check chess rules for game over
        if board.is_checkmate():
            return "win" if board.turn == chess.BLACK else "loss"
        elif board.is_stalemate() or board.is_insufficient_material():
            return "draw"
        
        # Otherwise, use material advantage to estimate result
        material = self.calculate_material(board)
        starting_material = 39  # Standard starting material
        
        if material > starting_material * 0.7:
            return "win"
        elif material < starting_material * 0.3:
            return "loss"
        else:
            return "draw"
    
    def calculate_xp(self, character, result):
        """Calculate XP gained in the match"""
        # Base XP from result
        xp = 0
        if result == "win":
            xp += 25
        elif result == "draw":
            xp += 10
        
        # XP from rStats
        r = character.get("rStats", {})
        xp += (
            r.get("rDDo", 0) // 5 +
            r.get("rCVo", 0) * 10 +
            r.get("rMBi", 0) * 10 +
            r.get("rLVSo", 0) * 5
        )
        
        # XP from combat stats
        combat_stats = character.get("combat_stats", {})
        xp += (
            combat_stats.get("damage_dealt", 0) // 10 +
            combat_stats.get("opponent_kos", 0) * 20 +
            combat_stats.get("assists", 0) * 10 +
            combat_stats.get("tiles_captured", 0) * 5 +
            combat_stats.get("survival_turns", 0) * 2 +
            combat_stats.get("healing_given", 0) // 5 +
            combat_stats.get("special_ability_uses", 0) * 5
        )
        
        # Apply AM (Adaptive Mastery) modifier
        am_factor = character.get("aAM", 5) / 5.0
        xp = int(xp * am_factor)
        
        # Update character XP
        character["xp_earned"] = xp
        character["xp_total"] = character.get("xp_total", 0) + xp
        
        return xp
    
    def update_team_morale(self, team_a, team_b, winner):
        """Update team morale based on match result"""
        # Team A morale changes
        morale_change = 10 if winner == "Team A" else -5 if winner == "Team B" else 0
        for character in team_a:
            character["morale"] = max(0, min(100, character.get("morale", 50) + morale_change))
        
        # Team B morale changes
        morale_change = 10 if winner == "Team B" else -5 if winner == "Team A" else 0
        for character in team_b:
            character["morale"] = max(0, min(100, character.get("morale", 50) + morale_change))
    
    def select_move_with_stockfish(self, board, character):
        """Select a move using Stockfish with character-based modifications"""
        if not self.stockfish_available:
            # Fallback to random move selection
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves) if legal_moves else None
        
        try:
            # Determine search depth based on character stats
            base_depth = min(max(2, character.get("aSPD", 5) // 2), 10)
            
            # Adjust depth based on stamina (lower stamina = lower depth)
            stamina_factor = max(0.5, character.get("stamina", 100) / 100)
            adjusted_depth = max(1, int(base_depth * stamina_factor))
            
            # Open Stockfish engine
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                # Add thinking time based on character's Focus/Speed
                thinking_ms = character.get("aFS", 5) * 50
                
                # Get analysis from Stockfish
                limit = chess.engine.Limit(depth=adjusted_depth, time=thinking_ms/1000.0)
                
                # Determine move quality based on character stats and traits
                quality_roll = random.random()
                quality_boost = (character.get("aSTR", 5) + character.get("aFS", 5)) / 20.0
                
                # Apply trait bonuses to quality roll
                for trait_name in character.get("traits", []):
                    if trait_name in self.traits:
                        trait = self.traits[trait_name]
                        if "bonus_roll" in trait.get("formula_key", ""):
                            quality_boost += trait.get("value", 0) / 100.0
                
                # Apply momentum boost/penalty
                if hasattr(character, "team") and character["team"] == "A" and "momentum" in character:
                    if character["momentum"]["state"] == "building":
                        quality_boost += 0.1  # +10% boost when in building momentum
                    elif character["momentum"]["state"] == "crash":
                        quality_boost -= 0.1  # -10% penalty when crashing
                
                quality_roll += quality_boost
                
                # Select move based on quality roll
                if quality_roll > 0.9:  # Brilliant move
                    result = engine.play(board, limit)
                    return result.move
                elif quality_roll > 0.7:  # Good move
                    # Get top 3 moves and pick randomly from them
                    analysis = engine.analyse(board, limit, multipv=3)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                elif quality_roll > 0.4:  # Decent move
                    # Get top 5 moves and pick randomly from them
                    analysis = engine.analyse(board, limit, multipv=5)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                else:  # Suboptimal move
                    # Pick a random legal move with some bias for non-terrible moves
                    legal_moves = list(board.legal_moves)
                    if legal_moves:
                        # Try to avoid obvious blunders
                        if random.random() > 0.3:  # 70% chance of avoiding obvious blunders
                            info = engine.analyse(board, chess.engine.Limit(depth=1))
                            if "pv" in info and info["pv"]:
                                safe_move = info["pv"][0]
                                return safe_move
                        return random.choice(legal_moves)
        
        except Exception as e:
            print(f"Stockfish error: {e}")
            # Fallback to random move selection
            legal_moves = list(board.legal_moves)
            return random.choice(legal_moves) if legal_moves else None
        
        # Final fallback
        legal_moves = list(board.legal_moves)
        return random.choice(legal_moves) if legal_moves else None

# Utility function to run a mirrored match test to check for fairness
def run_mirrored_match_test(simulator, team_a, team_b, iterations=10):
    """Run a series of mirrored matches to test for fairness"""
    print(f"Running {iterations} mirrored match tests...")
    
    normal_a_wins = 0
    normal_b_wins = 0
    normal_draws = 0
    
    mirrored_a_wins = 0
    mirrored_b_wins = 0
    mirrored_draws = 0
    
    # Run normal order matches (A vs B)
    for i in range(iterations):
        print(f"Normal match {i+1}/{iterations}...")
        # Make a deep copy of teams to avoid state contamination
        a_copy = copy.deepcopy(team_a)
        b_copy = copy.deepcopy(team_b)
        
        result = simulator.simulate_match(a_copy, b_copy, show_details=False)
        if result["winner"] == "Team A":
            normal_a_wins += 1
        elif result["winner"] == "Team B":
            normal_b_wins += 1
        else:
            normal_draws += 1
    
    # Run mirrored order matches (B vs A)
    for i in range(iterations):
        print(f"Mirrored match {i+1}/{iterations}...")
        # Make a deep copy of teams to avoid state contamination
        a_copy = copy.deepcopy(team_a)
        b_copy = copy.deepcopy(team_b)
        
        # Swap team names for easier comparison
        for char in a_copy:
            char["temp_name"] = char["team_name"]
            char["team_name"] = b_copy[0]["team_name"]
        
        for char in b_copy:
            char["temp_name"] = char["team_name"]
            char["team_name"] = a_copy[0]["temp_name"]
        
        result = simulator.simulate_match(b_copy, a_copy, show_details=False)
        
        # Since teams are swapped, we need to invert the result
        if result["winner"] == "Team A":  # Actually Team B winning
            mirrored_b_wins += 1
        elif result["winner"] == "Team B":  # Actually Team A winning
            mirrored_a_wins += 1
        else:
            mirrored_draws += 1
    
    # Print results
    print("\nMirrored Match Test Results:")
    print(f"Normal matches (A vs B): A wins: {normal_a_wins}, B wins: {normal_b_wins}, Draws: {normal_draws}")
    print(f"Mirrored matches (B vs A): A wins: {mirrored_a_wins}, B wins: {mirrored_b_wins}, Draws: {mirrored_draws}")
    print(f"Total: A wins: {normal_a_wins + mirrored_a_wins}, B wins: {normal_b_wins + mirrored_b_wins}, Draws: {normal_draws + mirrored_draws}")
    
    # Calculate fairness metric
    total_games = iterations * 2
    a_win_percent = (normal_a_wins + mirrored_a_wins) / total_games * 100
    b_win_percent = (normal_b_wins + mirrored_b_wins) / total_games * 100
    
    print(f"\nFairness analysis:")
    print(f"Team A win rate: {a_win_percent:.1f}%")
    print(f"Team B win rate: {b_win_percent:.1f}%")
    
    if abs(a_win_percent - b_win_percent) < 10:
        print("FAIR: Win rates are within 10% of each other")
    else:
        print("UNFAIR: Win rates differ by more than 10%")
    
    # Check for first-mover advantage
    print("\nFirst-mover advantage analysis:")
    first_mover_wins = normal_a_wins + mirrored_b_wins
    second_mover_wins = normal_b_wins + mirrored_a_wins
    first_mover_win_percent = first_mover_wins / (first_mover_wins + second_mover_wins) * 100 if (first_mover_wins + second_mover_wins) > 0 else 50
    
    print(f"First mover win rate: {first_mover_win_percent:.1f}%")
    
    if abs(first_mover_win_percent - 50) < 5:
        print("FAIR: First-mover advantage is minimal")
    else:
        print(f"{'ADVANTAGE' if first_mover_win_percent > 50 else 'DISADVANTAGE'}: First-mover has a {abs(first_mover_win_percent - 50):.1f}% {'advantage' if first_mover_win_percent > 50 else 'disadvantage'}")
    
    return {
        "normal_a_wins": normal_a_wins,
        "normal_b_wins": normal_b_wins,
        "normal_draws": normal_draws,
        "mirrored_a_wins": mirrored_a_wins,
        "mirrored_b_wins": mirrored_b_wins,
        "mirrored_draws": mirrored_draws,
        "a_win_percent": a_win_percent,
        "b_win_percent": b_win_percent,
        "first_mover_win_percent": first_mover_win_percent
    }