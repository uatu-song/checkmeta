import chess
import chess.engine
import random
import json
import os
import datetime
import math
from typing import Dict, List, Any, Tuple, Optional

# Add the missing function to determine division from role
def get_division_from_role(role):
    """Determine character division based on role"""
    # Mapping roles to divisions (o = Operations, i = Intelligence)
    operations_roles = ["FL", "VG", "EN"]
    intelligence_roles = ["RG", "GO", "PO", "SV"]
    
    if role in operations_roles:
        return "o"
    elif role in intelligence_roles:
        return "i"
    else:
        # Default to operations for unknown roles
        return "o"

# Helper function to map position/role values
def map_position_to_role(position):
    """Map position values to role codes"""
    position = str(position).upper().strip()
    
    # Map common position names to role codes
    position_map = {
        "FIELD LEADER": "FL",
        "VANGUARD": "VG",
        "ENFORCER": "EN",
        "RANGER": "RG",
        "GHOST OPERATIVE": "GO",
        "PSI OPERATIVE": "PO",
        "SOVEREIGN": "SV",
        # Add more mappings if needed
    }
    
    # Check for exact matches
    if position in position_map:
        return position_map[position]
    
    # Check for partial matches
    for key, value in position_map.items():
        if key in position.upper():
            return value
    
    # Check if it's already a role code
    valid_roles = ["FL", "VG", "EN", "RG", "GO", "PO", "SV"]
    if position in valid_roles:
        return position
    
    # Default to Field Leader if no match
    return "FL"

class MetaLeagueSimulator:
    def __init__(self, stockfish_path="/usr/local/bin/stockfish"):
        """Initialize the META Fantasy League simulator with Stockfish integration"""
        self.stockfish_path = stockfish_path
        
        # Verify Stockfish is available
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
    
    def _load_traits(self):
        """Load trait definitions"""
        # Real traits would be loaded from a file, but for now using hardcoded traits
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
    
    def create_matchups(self, teams):
        """Create matchups between teams"""
        team_ids = list(teams.keys())
        random.shuffle(team_ids)
        
        matchups = []
        for i in range(0, len(team_ids), 2):
            if i + 1 < len(team_ids):
                matchups.append((team_ids[i], team_ids[i+1]))
        
        return matchups
    
    def simulate_match(self, team_a, team_b, show_details=True):
        """Simulate a match between two teams with Stockfish integration"""
        # Define active roster size
        active_roster_size = 8  # 8 active players, rest on bench
        
        # Get active and bench players
        active_team_a = team_a[:active_roster_size] if len(team_a) > active_roster_size else team_a
        bench_team_a = team_a[active_roster_size:] if len(team_a) > active_roster_size else []
        
        active_team_b = team_b[:active_roster_size] if len(team_b) > active_roster_size else team_b
        bench_team_b = team_b[active_roster_size:] if len(team_b) > active_roster_size else []
        
        # Show team details
        match_context = {
            "day": self.current_day,
            "team_a_id": team_a[0]["team_id"],
            "team_b_id": team_b[0]["team_id"],
            "team_a_name": team_a[0]["team_name"],
            "team_b_name": team_b[0]["team_name"],
            "round": 1,
            "trait_logs": [],
            "convergence_logs": []
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
        
        # Apply role-based openings
        for i, character in enumerate(active_team_a):
            self._apply_opening(team_a_boards[i], character.get("role", ""))
        
        for i, character in enumerate(active_team_b):
            self._apply_opening(team_b_boards[i], character.get("role", ""))
        
        # Track material values
        team_a_material = [self._calculate_material(board) for board in team_a_boards]
        team_b_material = [self._calculate_material(board) for board in team_b_boards]
        
        # Maximum moves to simulate
        max_moves = 30
        
        # Simulate moves
        for move_num in range(max_moves):
            match_context["round"] = move_num + 1
            
            if show_details:
                print(f"\nRound {move_num + 1}:")
            
            # Process convergences
            convergences = self._process_convergences(active_team_a, team_a_boards, active_team_b, team_b_boards, match_context, show_details)
            
            # Make moves for team A
            for i, (character, board) in enumerate(zip(active_team_a, team_a_boards)):
                if board.is_game_over() or character.get("is_ko", False) or character.get("is_dead", False):
                    continue
                
                # Select and make move
                move = self._select_move_with_stockfish(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character['name']} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self._calculate_material(board)
                    material_change = new_material - team_a_material[i]
                    team_a_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self._update_character_metrics(character, material_change, show_details)
                    
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
            
            # Make moves for team B (similar logic)
            for i, (character, board) in enumerate(zip(active_team_b, team_b_boards)):
                if board.is_game_over() or character.get("is_ko", False) or character.get("is_dead", False):
                    continue
                
                # Select and make move
                move = self._select_move_with_stockfish(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character['name']} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self._calculate_material(board)
                    material_change = new_material - team_b_material[i]
                    team_b_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self._update_character_metrics(character, material_change, show_details)
                    
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
            self._apply_end_of_round_effects(active_team_a + active_team_b, match_context, show_details)
            
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
            result = self._determine_game_result(board, character)
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
                "was_active": True
            })
            
            if result == "win":
                team_a_wins += 1
                character.setdefault("rStats", {})
                character["rStats"]["rWIN"] = character["rStats"].get("rWIN", 0) + 1
            
            # Calculate XP gain
            self._calculate_xp(character, result)
        
        # Process bench team A results (they didn't participate)
        for character in bench_team_a:
            character_results.append({
                "team": "A",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": "bench",
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": False,
                "is_dead": False,
                "was_active": False
            })
        
        # Process active team B results
        for i, (character, board) in enumerate(zip(active_team_b, team_b_boards)):
            result = self._determine_game_result(board, character)
            character_results.append({
                "team": "B",
                "character_id": character["id"],
                "character_name": character["name"],
                "result": result,
                "final_hp": character["HP"],
                "final_stamina": character["stamina"],
                "final_life": character["life"],
                "is_ko": character.get("is_ko", False),
                "is_dead": character.get("is_dead", False),
                "was_active": True
            })
            
            if result == "win":
                team_b_wins += 1
                character.setdefault("rStats", {})
                character["rStats"]["rWIN"] = character["rStats"].get("rWIN", 0) + 1
            
            # Calculate XP gain
            self._calculate_xp(character, result)
        
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
                "was_active": False
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
        self._update_team_morale(team_a, team_b, winner)
        
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

    
    def _calculate_combat_roll(self, attacker, defender):
        """Calculate combat roll based on character stats and traits"""
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        roll += attacker.get("aSTR", 5) + attacker.get("aFS", 5)
        
        # Scale by Power Potential
        op_factor = attacker.get("aOP", 5) / 5.0
        roll = int(roll * op_factor)
        
        return roll
    
    def _apply_damage(self, character, damage):
        """Apply damage to a character with cascading HP->stamina->life system"""
        # BALANCE: Reduce incoming damage overall
        damage = max(1, damage * 0.5)  # Reduce all damage by 50%
        
        # Apply damage reduction based on traits
        reduction = 0
        for trait_name in character.get("traits", []):
            if trait_name in self.traits:
                trait = self.traits[trait_name]
                if "damage_reduction" in trait.get("formula_key", ""):
                    reduction += trait.get("value", 0)
        
        # Apply DUR/RES stat bonuses with improved scaling
        dur_bonus = (character.get("aDUR", 5) - 5) * 6  # 6% per point above 5
        res_bonus = (character.get("aRES", 5) - 5) * 5  # 5% per point above 5
        
        # BALANCE: Add base damage reduction for all characters
        base_reduction = 20  # All characters get 20% damage reduction
        reduction += dur_bonus + res_bonus + base_reduction
        
        # Cap reduction at 80%
        reduction = min(max(0, reduction), 80)
        actual_damage = max(1, damage * (1 - reduction/100.0))
        
        # Apply to HP first
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - actual_damage)
        character["HP"] = new_hp
        
        # Overflow to stamina if HP is depleted, but at reduced rate
        stamina_damage = 0
        if new_hp == 0:
            # BALANCE: Reduce stamina damage
            stamina_damage = (actual_damage - current_hp) * 0.6  # 60% efficiency
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Overflow to life if stamina is depleted, but make it much harder
            if new_stamina == 0:
                # BALANCE: Make it harder to lose life
                life_threshold = 50  # Need at least this much overflow damage to lose life
                if stamina_damage > current_stamina + life_threshold:
                    life_damage = 1  # Always just 1 life point
                    character["life"] = max(0, character.get("life", 100) - life_damage)
    
    def _update_character_metrics(self, character, material_change, show_details=False):
        """Update character metrics based on material change"""
        # Material loss = damage
        if material_change < 0:
            # BALANCE: Reduce damage scaling from material loss
            damage = abs(material_change) * 3  # Reduced from 5 to 3
            self._apply_damage(character, damage)
            
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
    
    def _apply_end_of_round_effects(self, characters, context, show_details=True):
        """Apply end-of-round effects like trait activations and regeneration"""
        for character in characters:
            # Skip dead characters
            if character.get("is_dead", False):
                continue
                
            # BALANCE: Add base HP regeneration for all characters
            base_hp_regen = 3  # All characters regenerate 3 HP per round
            
            # Regeneration effects from traits
            trait_heal_amount = 0
            for trait_name in character.get("traits", []):
                if trait_name in self.traits:
                    trait = self.traits[trait_name]
                    if "end_of_turn" in trait.get("triggers", []):
                        if trait.get("formula_key") == "heal":
                            # BALANCE: Boost healing trait effectiveness
                            trait_heal_amount = trait.get("value", 0) * 2  # Double healing effect
            
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
            base_regen = 3  # Increased from 1 to 3
            
            # Apply WIL bonus to stamina regen
            wil_bonus = max(0, character.get("aWIL", 5) - 5)
            wil_regen = wil_bonus * 0.5  # Each point above 5 gives 0.5 more stamina regen
            
            regen_rate = base_regen + wil_regen
            
            # BALANCE: Faster recovery from knockdown
            if character.get("is_ko", False):
                # KO'd characters recover faster
                regen_rate *= 2
                
                # Chance to recover from KO based on stamina
                stamina = character.get("stamina", 0)
                if stamina > 30:  # If stamina is above 30%, chance to recover
                    recovery_chance = stamina / 200  # 15-50% chance based on stamina
                    if random.random() < recovery_chance:
                        character["is_ko"] = False
                        character["HP"] = max(10, character.get("HP", 0))  # Ensure at least 10 HP
                        if show_details:
                            print(f"  {character['name']} has recovered from knockout!")
            
            character["stamina"] = min(100, character.get("stamina", 0) + regen_rate)
    
    def _determine_game_result(self, board, character):
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
        material = self._calculate_material(board)
        starting_material = 39  # Standard starting material
        
        if material > starting_material * 0.7:
            return "win"
        elif material < starting_material * 0.3:
            return "loss"
        else:
            return "draw"
    
    def _calculate_xp(self, character, result):
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
        
        # Apply AM (Adaptive Mastery) modifier
        am_factor = character.get("aAM", 5) / 5.0
        xp = int(xp * am_factor)
        
        # Update character XP
        character["xp_earned"] = xp
        character["xp_total"] = character.get("xp_total", 0) + xp
        
        return xp
    
    def _update_team_morale(self, team_a, team_b, winner):
        """Update team morale based on match result"""
        # Team A morale changes
        morale_change = 10 if winner == "Team A" else -5 if winner == "Team B" else 0
        for character in team_a:
            character["morale"] = max(0, min(100, character.get("morale", 50) + morale_change))
        
        # Team B morale changes
        morale_change = 10 if winner == "Team B" else -5 if winner == "Team A" else 0
        for character in team_b:
            character["morale"] = max(0, min(100, character.get("morale", 50) + morale_change))

# Improved Excel loading function to handle different column names
def load_lineups_from_excel(file_path, day_sheet="4/7/25"):
    """Load character lineups from an Excel file with detailed error reporting"""
    try:
        import pandas as pd
        
        print(f"Attempting to load from: {file_path}")
        
        # First check if file exists
        if not os.path.exists(file_path):
            print(f"Error: File '{file_path}' does not exist")
            raise FileNotFoundError(f"File '{file_path}' does not exist")
        
        # Get all sheet names to debug
        xls = pd.ExcelFile(file_path)
        available_sheets = xls.sheet_names
        print(f"Available sheets in Excel file: {available_sheets}")
        
        # Try to find a matching sheet
        # Convert date format for more flexible matching
        day_sheet_clean = day_sheet.replace('/', '')
        matching_sheets = [s for s in available_sheets if day_sheet_clean in s.replace('/', '').replace('-', '')]
        selected_sheet = None
        
        if day_sheet in available_sheets:
            selected_sheet = day_sheet
            print(f"Found exact match for sheet: {day_sheet}")
        elif matching_sheets:
            selected_sheet = matching_sheets[0]
            print(f"Found partial match for sheet: {selected_sheet}")
        else:
            # Fall back to first sheet
            selected_sheet = available_sheets[0]
            print(f"No matching sheet found. Using first sheet: {selected_sheet}")
        
        # Load the selected sheet
        print(f"Loading data from sheet: {selected_sheet}")
        df = pd.read_excel(file_path, sheet_name=selected_sheet)
        
        # Print column names for debugging
        print(f"Columns in sheet: {df.columns.tolist()}")
        
        # Map column names based on what's available
        column_mapping = {
            'team_id': ['Team', 'team_id', 'team', 'team id', 'teamid', 'tid'],
            'name': ['Nexus Being', 'name', 'character', 'character name', 'char_name', 'character_name', 'charname'],
            'role': ['Position', 'PositionFull', 'role', 'position', 'char_role', 'character_role']
        }
        
        # Create new columns with required names based on available columns
        required_columns = ['team_id', 'name', 'role']
        
        for required_col, possible_cols in column_mapping.items():
            found = False
            for col in possible_cols:
                if col in df.columns:
                    print(f"Mapping '{col}' to '{required_col}'")
                    df[required_col] = df[col]
                    found = True
                    break
            
            if not found:
                print(f"Error: Could not find any column to map to '{required_col}'")
                raise ValueError(f"Could not find any column to map to '{required_col}'")
        
        # Convert 'Position' values to role codes
        if 'role' in df.columns:
            df['role'] = df['role'].apply(map_position_to_role)
        
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
            
            # Ensure team_id starts with 't' 
            if not team_id.startswith('t'):
                team_id = 't' + team_id
            
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
            
            # Get team name (from Team column or construct from team_id)
            team_name = None
            if 'Team' in df.columns and not pd.isna(row.get('Team')):
                team_name = f"Team {row.get('Team')}"
            else:
                team_name = f"Team {team_id[1:]}"  # Remove 't' prefix for name
            
            # Create character dictionary
            character = {
                'id': f"{team_id}_{len(teams[team_id])}",
                'name': char_name,
                'team_id': team_id,
                'team_name': team_name,
                'role': role,
                'division': get_division_from_role(role),
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
            
            teams[team_id].append(character)
            valid_rows += 1
        
        print(f"Successfully loaded {valid_rows} characters across {len(teams)} teams")
        
        # If no valid teams loaded, return error
        if not teams:
            raise ValueError("No valid teams found in the Excel file")
        
        return teams
    except Exception as e:
        print(f"Error loading lineups from Excel: {e}")
        import traceback
        traceback.print_exc()
        raise e  # Re-raise to ensure the error is propagated

import json
import os
from typing import Dict, List, Tuple

def create_division_matchups(teams: Dict, day_number: int = 1):
    """
    Create division-based matchups for the META League
    
    Parameters:
    - teams: Dictionary of teams keyed by team_id
    - day_number: Current day number (1-5 for weekdays)
    
    Returns:
    - List of matchups (team_id_a, team_id_b)
    """
    # Separate teams into divisions
    division_o = []
    division_i = []
    
    for team_id, team_data in teams.items():
        if team_data and team_data[0].get("division") == "o":
            division_o.append(team_id)
        else:
            division_i.append(team_id)
    
    # Sort team IDs for consistent rotation
    division_o.sort()
    division_i.sort()
    
    # Make sure we have balanced divisions
    if len(division_o) != len(division_i):
        print(f"Warning: Unbalanced divisions - O: {len(division_o)}, I: {len(division_i)}")
        # If unbalanced, we'll use the smaller division size
        min_size = min(len(division_o), len(division_i))
        division_o = division_o[:min_size]
        division_i = division_i[:min_size]
    
    # Rotate based on day number (1-5)
    # Keep division_o fixed and rotate division_i
    rotation = (day_number - 1) % len(division_i)
    if rotation > 0:
        division_i = division_i[rotation:] + division_i[:rotation]
    
    # Create matchups - each team from division_o plays against a team from division_i
    matchups = []
    for i in range(len(division_o)):
        matchups.append((division_o[i], division_i[i]))
    
    return matchups

import json
import os
from typing import Dict, List, Tuple

def create_team_matchups(teams: Dict, day_number: int = 1):
    """
    Create matchups for the META League based on team numbers
    
    Parameters:
    - teams: Dictionary of teams keyed by team_id
    - day_number: Current day number (1-5 for weekdays)
    
    Returns:
    - List of matchups (team_id_a, team_id_b)
    """
    # Get all team IDs and sort them numerically
    all_team_ids = list(teams.keys())
    
    # Sort by team number
    all_team_ids.sort(key=lambda x: int(x[1:]) if x[1:].isdigit() else 999)
    
    print(f"All team IDs: {all_team_ids}")
    
    # Calculate number of active teams
    total_teams = len(all_team_ids)
    
    # Calculate number of matches per day (half the teams)
    matches_per_day = total_teams // 2
    
    # Implement a round-robin scheduling algorithm
    # Keep first team fixed, rotate all others based on day number
    if total_teams <= 1:
        print("Not enough teams for matchups")
        return []
    
    # For odd number of teams, add a dummy team (represents a bye)
    if total_teams % 2 == 1:
        all_team_ids.append("dummy")
        total_teams += 1
    
    # Calculate rotation for current day
    rotation = (day_number - 1) % (total_teams - 1)
    
    # Create the rotated schedule
    # First team stays fixed, others rotate
    remaining_teams = all_team_ids[1:]
    
    if rotation > 0:
        remaining_teams = remaining_teams[-(rotation):] + remaining_teams[:-(rotation)]
    
    # Create schedule
    schedule = []
    fixed_team = all_team_ids[0]
    
    # Combine fixed team with first rotated team
    if remaining_teams[0] != "dummy" and fixed_team != "dummy":
        schedule.append((fixed_team, remaining_teams[0]))
    
    # Pair up the rest of the teams
    for i in range(1, len(remaining_teams) // 2):
        team_a = remaining_teams[i]
        team_b = remaining_teams[total_teams - 1 - i]
        
        if team_a != "dummy" and team_b != "dummy":
            schedule.append((team_a, team_b))
    
    print(f"Generated {len(schedule)} matchups for day {day_number}")
    
    # Ensure we have exactly 5 matches if possible
    while len(schedule) > 5:
        schedule.pop()  # Remove excess matches
    
    return schedule

def run_with_team_matchups(day_number=1, lineup_file="lineups.xlsx"):
    """Run the simulation with team-based matchups"""
    print(f"=== META Fantasy League Simulation - Day {day_number} ===")
    
    # Initialize the simulator
    simulator = MetaLeagueSimulator()
    
    # Load lineups from Excel
    date_string = f"4/7/25"  # Format for day 5
    print(f"Loading lineups from {lineup_file} for {date_string}...")

    try:
        teams = load_lineups_from_excel(lineup_file, date_string)
    except Exception as e:
        print(f"ERROR: Could not load teams from {lineup_file}: {e}")
        print("Creating sample teams as fallback...")
        # Create sample teams if Excel loading fails
        teams = create_sample_teams(simulator)
    
    print(f"\nLoaded {len(teams)} teams:")
    for team_id, team in teams.items():
        print(f"  {team_id}: {team[0]['team_name']} - {len(team)} characters")
    
    # Create team-based matchups
    matchups = create_team_matchups(teams, day_number)
    
    print(f"\nCreated {len(matchups)} matchups:")
    for team_a_id, team_b_id in matchups:
        print(f"  {teams[team_a_id][0]['team_name']} vs {teams[team_b_id][0]['team_name']}")
    
    # Run the matches
    results = []
    for team_a_id, team_b_id in matchups:
        print(f"\nSimulating: {teams[team_a_id][0]['team_name']} vs {teams[team_b_id][0]['team_name']}")
        result = simulator.simulate_match(teams[team_a_id], teams[team_b_id], show_details=True)
        results.append(result)
    
    # Save results
    results_dir = "results"
    os.makedirs(results_dir, exist_ok=True)
    
    with open(f"{results_dir}/day_{day_number}_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to {results_dir}/day_{day_number}_results.json")
    
    return results

def create_sample_teams(simulator):
    """Create sample teams with balanced divisions"""
    teams = {
        "t001": [
            {
                "id": "t001_1",
                "name": "Iron Man",
                "team_id": "t001",
                "team_name": "Avengers",
                "role": "FL",
                "division": "o",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["genius", "armor"],
                "aSTR": 8, "aSPD": 7, "aFS": 9, "aLDR": 8, "aDUR": 7, "aRES": 6, "aWIL": 8,
                "aOP": 9, "aAM": 7, "aSBY": 8,
                "rStats": {},
                "xp_total": 0
            },
            {
                "id": "t001_2",
                "name": "Captain America",
                "team_id": "t001",
                "team_name": "Avengers",
                "role": "VG",
                "division": "o",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["tactical", "shield"],
                "aSTR": 7, "aSPD": 7, "aFS": 8, "aLDR": 9, "aDUR": 8, "aRES": 7, "aWIL": 9,
                "aOP": 7, "aAM": 8, "aSBY": 9,
                "rStats": {},
                "xp_total": 0
            }
        ],
        "t002": [
            {
                "id": "t002_1",
                "name": "Spider-Man",
                "team_id": "t002",
                "team_name": "Champions",
                "role": "VG",
                "division": "o",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["agile", "spider-sense"],
                "aSTR": 8, "aSPD": 9, "aFS": 7, "aLDR": 6, "aDUR": 6, "aRES": 7, "aWIL": 7,
                "aOP": 8, "aAM": 7, "aSBY": 7,
                "rStats": {},
                "xp_total": 0
            },
            {
                "id": "t002_2",
                "name": "Ms. Marvel",
                "team_id": "t002",
                "team_name": "Champions",
                "role": "FL",
                "division": "o",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["stretchy", "healing"],
                "aSTR": 7, "aSPD": 6, "aFS": 8, "aLDR": 7, "aDUR": 6, "aRES": 8, "aWIL": 8,
                "aOP": 7, "aAM": 8, "aSBY": 7,
                "rStats": {},
                "xp_total": 0
            }
        ],
        "t003": [
            {
                "id": "t003_1",
                "name": "Professor X",
                "team_id": "t003",
                "team_name": "X-Men",
                "role": "FL",
                "division": "i",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["telepathic", "genius"],
                "aSTR": 3, "aSPD": 5, "aFS": 9, "aLDR": 10, "aDUR": 5, "aRES": 9, "aWIL": 10,
                "aOP": 10, "aAM": 8, "aSBY": 9,
                "rStats": {},
                "xp_total": 0
            },
            {
                "id": "t003_2",
                "name": "Wolverine",
                "team_id": "t003",
                "team_name": "X-Men",
                "role": "VG",
                "division": "i",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["healing", "agile"],
                "aSTR": 9, "aSPD": 8, "aFS": 7, "aLDR": 6, "aDUR": 10, "aRES": 8, "aWIL": 8,
                "aOP": 7, "aAM": 7, "aSBY": 6,
                "rStats": {},
                "xp_total": 0
            }
        ],
        "t004": [
            {
                "id": "t004_1",
                "name": "Dr. Strange",
                "team_id": "t004",
                "team_name": "Illuminati",
                "role": "FL",
                "division": "i",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["tactical", "genius"],
                "aSTR": 5, "aSPD": 6, "aFS": 10, "aLDR": 8, "aDUR": 7, "aRES": 10, "aWIL": 9,
                "aOP": 9, "aAM": 9, "aSBY": 8,
                "rStats": {},
                "xp_total": 0
            },
            {
                "id": "t004_2",
                "name": "Black Bolt",
                "team_id": "t004",
                "team_name": "Illuminati",
                "role": "SV",
                "division": "i",
                "HP": 100,
                "stamina": 100,
                "life": 100,
                "morale": 50,
                "traits": ["tactical", "shield"],
                "aSTR": 9, "aSPD": 8, "aFS": 7, "aLDR": 8, "aDUR": 9, "aRES": 7, "aWIL": 8,
                "aOP": 10, "aAM": 7, "aSBY": 8,
                "rStats": {},
                "xp_total": 0
            }
        ]
    }
    return teams

# Run the test
if __name__ == "__main__":
    import sys
    
    # Get command line arguments for lineup file
    lineup_file = "lineups.xlsx"  # Default name
    day_number = 5
    
    if len(sys.argv) > 1:
        lineup_file = sys.argv[1]
    
    if len(sys.argv) > 2:
        try:
            day_number = int(sys.argv[2])
        except:
            pass
    
    print(f"Using lineup file: {lineup_file}")
    print(f"Simulating day: {day_number}")
    
    # Define max characters per team - 8 active, 4 on bench
    active_chars = 8
    bench_chars = 4
    
    # Run with team matchups
    run_with_team_matchups(day_number=day_number, lineup_file=lineup_file)