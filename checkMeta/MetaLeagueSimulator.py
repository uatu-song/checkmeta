import os
import random
import math
import chess

from models.character import Character
from models.team import Team
from systems.traits import TraitSystem
from systems.morale import MoraleSystem
from systems.leadership import LeadershipSystem
from systems.synergy import SynergySystem
from simulation.combat import CombatSystem
from simulation.convergence import ConvergenceSystem
from config.openings import ROLE_OPENINGS, get_opening_for_role
from data.loaders import (
    load_lineups_from_excel, 
    load_traits, 
    load_team_ids, 
    load_divisions_from_csv,
    load_attributes,
    apply_attributes_to_teams,
    load_complete_teams
)

class MetaLeagueSimulator:
    """Main simulator class integrating all systems"""
    
    def __init__(self, stockfish_path="/usr/local/bin/stockfish"):
        """Initialize the simulator and all subsystems"""
        # Game state
        self.current_day = 1
        
        # Load data from files
        self.traits = load_traits(use_csv=True)  # Load from trait catalog CSV
        self.role_openings = ROLE_OPENINGS  # From config
        self.team_info = load_team_ids()  # From team IDs CSV
        self.division_info = load_divisions_from_csv()  # From divisions CSV
        
        # Initialize subsystems
        self.trait_system = TraitSystem(trait_definitions=self.traits)
        self.morale_system = MoraleSystem()
        self.leadership_system = LeadershipSystem()
        self.synergy_system = SynergySystem()
        self.combat_system = CombatSystem(stockfish_path)
        
        # Create results directory
        os.makedirs("results", exist_ok=True)
    
    def load_teams(self, lineup_file="All Lineups (1).xlsx", day_sheet="4/7/25"):
        """Load teams with all associated data"""
        return load_complete_teams(lineup_file, day_sheet)
    
    def get_team_active_roster(self, team_data):
        """Get active roster for a team based on team info"""
        # Handle empty team data
        if not team_data:
            return []
        
        # Get team_id safely from Character object or dictionary
        if hasattr(team_data[0], 'team_id'):
            # It's a Character object
            team_id = team_data[0].team_id
        else:
            # It's a dictionary
            team_id = team_data[0]['team_id']
        
        if not team_id or team_id not in self.team_info:
            # If no team info, return all characters (up to 8)
            active_roster_size = 8
            return team_data[:active_roster_size] if len(team_data) > active_roster_size else team_data
        
        # Get roster names from team info
        team_info = self.team_info[team_id]
        active_names = team_info.get('active_roster', [])
        
        if not active_names:
            # Default to first 8 characters if no active roster specified
            active_roster_size = 8
            return team_data[:active_roster_size] if len(team_data) > active_roster_size else team_data
        
        # Find characters by name
        active_roster = []
        for character in team_data:
            # Get character name safely
            if hasattr(character, 'name'):
                char_name = character.name
            else:
                char_name = character['name']
                
            if char_name in active_names:
                active_roster.append(character)
        
        # If we didn't match enough, fill with remaining characters
        if len(active_roster) < len(active_names):
            used_names = set()
            for character in active_roster:
                if hasattr(character, 'name'):
                    used_names.add(character.name)
                else:
                    used_names.add(character['name'])
                    
            for character in team_data:
                if hasattr(character, 'name'):
                    char_name = character.name
                else:
                    char_name = character['name']
                    
                if char_name not in used_names:
                    active_roster.append(character)
                    if len(active_roster) >= len(active_names):
                        break
        
        return active_roster

    def get_team_bench(self, team_data):
        """Get bench for a team based on team info"""
        active_roster = self.get_team_active_roster(team_data)
        
        # Create a set of IDs from active roster
        active_ids = set()
        for character in active_roster:
            if hasattr(character, 'id'):
                # Character object
                active_ids.add(character.id)
            else:
                # Dictionary
                active_ids.add(character['id'])
        
        # Return all characters not in the active roster
        bench = []
        for character in team_data:
            character_id = character.id if hasattr(character, 'id') else character['id']
            if character_id not in active_ids:
                bench.append(character)
                
        return bench

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
        
        # Sum up material for all pieces
        for piece_type in values:
            material += len(board.pieces(piece_type, chess.WHITE)) * values[piece_type]
        
        return material

    def apply_opening(self, board, role):
        """Apply role-based opening moves to a chess board"""
        # Get opening for this role
        opening_sequence = None
        
        if hasattr(self, 'role_openings') and role in self.role_openings:
            opening_choices = self.role_openings[role]
            opening_sequence = random.choice(opening_choices)
        else:
            # Default openings if role_openings not defined
            default_openings = {
                "FL": ["e4", "d4", "c4"],
                "VG": ["e4 e5", "d4 d5"],
                "RG": ["Nf3", "g3"]
            }
            if role in default_openings:
                opening_sequence = random.choice(default_openings[role])
            else:
                opening_sequence = "e4"  # Default to e4
        
        # Apply moves
        if opening_sequence:
            moves = opening_sequence.split()
            for move_str in moves:
                try:
                    # Try to parse and apply the move
                    move = None
                    if len(move_str) == 4 and move_str[0] in 'abcdefgh' and move_str[2] in 'abcdefgh':
                        # UCI format
                        move = chess.Move.from_uci(move_str)
                    else:
                        # SAN format
                        move = board.parse_san(move_str)
                    
                    if move and move in board.legal_moves:
                        board.push(move)
                except Exception as e:
                    # Skip invalid moves
                    continue

    def simulate_match(self, team_a, team_b, show_details=True):
        """Simulate a match between two teams"""
        # Get active and bench players based on team info
        active_team_a = self.get_team_active_roster(team_a)
        bench_team_a = self.get_team_bench(team_a)
        
        active_team_b = self.get_team_active_roster(team_b)
        bench_team_b = self.get_team_bench(team_b)
        
        # Get team names safely
        if team_a and hasattr(team_a[0], 'team_name'):
            team_a_name = team_a[0].team_name
        elif team_a:
            team_a_name = team_a[0]['team_name']
        else:
            team_a_name = "Team A"
            
        if team_b and hasattr(team_b[0], 'team_name'):
            team_b_name = team_b[0].team_name
        elif team_b:
            team_b_name = team_b[0]['team_name']
        else:
            team_b_name = "Team B"
        
        # Match context for tracking events
        match_context = {
            "day": self.current_day,
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "round": 1,
            "trait_logs": [],
            "convergence_logs": []
        }
        
        # Show team details
        if show_details:
            print(f"Match: {team_a_name} vs {team_b_name}")
            
            # Get active player names safely
            active_a_names = []
            for char in active_team_a:
                if hasattr(char, 'name'):
                    active_a_names.append(char.name)
                else:
                    active_a_names.append(char['name'])
                    
            bench_a_names = []
            for char in bench_team_a:
                if hasattr(char, 'name'):
                    bench_a_names.append(char.name)
                else:
                    bench_a_names.append(char['name'])
                    
            active_b_names = []
            for char in active_team_b:
                if hasattr(char, 'name'):
                    active_b_names.append(char.name)
                else:
                    active_b_names.append(char['name'])
                    
            bench_b_names = []
            for char in bench_team_b:
                if hasattr(char, 'name'):
                    bench_b_names.append(char.name)
                else:
                    bench_b_names.append(char['name'])
            
            print(f"Active players {team_a_name}: {active_a_names}")
            print(f"Bench players {team_a_name}: {bench_a_names}")
            print(f"Active players {team_b_name}: {active_b_names}")
            print(f"Bench players {team_b_name}: {bench_b_names}")
        
        # Convert dict data to Character objects if needed
        team_a_characters = []
        for char in active_team_a:
            if isinstance(char, dict):
                team_a_characters.append(Character(char))
            else:
                team_a_characters.append(char)
        
        team_b_characters = []
        for char in active_team_b:
            if isinstance(char, dict):
                team_b_characters.append(Character(char))
            else:
                team_b_characters.append(char)
        
        # Create Team objects
        bench_a_characters = []
        for char in bench_team_a:
            if isinstance(char, dict):
                bench_a_characters.append(Character(char))
            else:
                bench_a_characters.append(char)
                
        bench_b_characters = []
        for char in bench_team_b:
            if isinstance(char, dict):
                bench_b_characters.append(Character(char))
            else:
                bench_b_characters.append(char)
        
        team_a_obj = Team(team_a_characters, bench=bench_a_characters)
        team_b_obj = Team(team_b_characters, bench=bench_b_characters)
        
        # Apply leadership bonuses
        self.leadership_system.apply_leadership_bonuses(team_a_obj)
        self.leadership_system.apply_leadership_bonuses(team_b_obj)
        
        # Calculate team synergy
        self.synergy_system.calculate_team_synergy(team_a_obj)
        self.synergy_system.calculate_team_synergy(team_b_obj)
        
        # Apply morale effects
        for character in team_a_obj.active_characters + team_b_obj.active_characters:
            character.morale_modifiers = self.morale_system.calculate_morale_modifiers(character.morale)
        
        # Initialize game boards and material values
        team_a_boards = [chess.Board() for _ in team_a_obj.active_characters]
        team_b_boards = [chess.Board() for _ in team_b_obj.active_characters]
        
        # Apply role-based openings
        for i, character in enumerate(team_a_obj.active_characters):
            # Access role attribute safely
            role = character.role if hasattr(character, 'role') else 'FL'
            self.apply_opening(team_a_boards[i], role)
        
        for i, character in enumerate(team_b_obj.active_characters):
            # Access role attribute safely
            role = character.role if hasattr(character, 'role') else 'FL'
            self.apply_opening(team_b_boards[i], role)
        
        # Track material values
        team_a_material = [self.calculate_material(board) for board in team_a_boards]
        team_b_material = [self.calculate_material(board) for board in team_b_boards]
        
        # Maximum rounds to simulate
        max_rounds = 20
        
        # Simulate rounds
        for round_num in range(max_rounds):
            match_context["round"] = round_num + 1
            
            if show_details:
                print(f"\nRound {round_num + 1}:")
            
            # Process convergences
            convergences = self.combat_system.process_convergences(
                team_a_obj, team_a_boards, 
                team_b_obj, team_b_boards, 
                self.trait_system, match_context
            )
            match_context["convergence_logs"].extend(convergences)
            
            # Make moves for team A
            for i, character in enumerate(team_a_obj.active_characters):
                if i >= len(team_a_boards) or character.is_ko or character.is_dead:
                    continue
                    
                board = team_a_boards[i]
                if board.is_game_over():
                    continue
                
                # Select and make move
                move = self.combat_system.select_move(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character.name} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self.calculate_material(board)
                    material_change = new_material - team_a_material[i]
                    team_a_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self.combat_system.update_character_metrics(character, material_change, match_context)
            
            # Make moves for team B
            for i, character in enumerate(team_b_obj.active_characters):
                if i >= len(team_b_boards) or character.is_ko or character.is_dead:
                    continue
                    
                board = team_b_boards[i]
                if board.is_game_over():
                    continue
                
                # Select and make move
                move = self.combat_system.select_move(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character.name} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self.calculate_material(board)
                    material_change = new_material - team_b_material[i]
                    team_b_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self.combat_system.update_character_metrics(character, material_change, match_context)
            
            # Apply end-of-round effects
            for character in team_a_obj.active_characters + team_b_obj.active_characters:
                # Skip dead characters
                if hasattr(character, 'is_dead') and character.is_dead:
                    continue
                    
                # Process trait activations for end-of-round triggers
                activations = self.trait_system.check_trait_activation(character, "end_of_round", context=match_context)
                effects = self.trait_system.apply_trait_effects(character, activations, context=match_context)
                
                if effects:
                    match_context["trait_logs"].append({
                        "round": match_context["round"],
                        "character": character.name,
                        "trigger": "end_of_round",
                        "effects": effects
                    })
                
                # Apply recovery effects
                if not character.is_ko:
                    # Regenerate HP and stamina
                    character.HP = min(100, character.HP + 3)
                    character.stamina = min(100, character.stamina + 5)
                else:
                    # KO'd characters recover faster
                    character.stamina = min(100, character.stamina + 10)
                    
                    # Chance to recover from KO
                    if character.stamina > 30:
                        recovery_chance = character.stamina / 200  # 15-50% chance based on stamina
                        if random.random() < recovery_chance:
                            character.is_ko = False
                            character.HP = max(20, character.HP)
                            if show_details:
                                print(f"  {character.name} has recovered from knockout!")
            
            # Check if match is over (all games ended)
            active_a_chars = sum(1 for char in team_a_obj.active_characters if not (hasattr(char, 'is_ko') and char.is_ko) and not (hasattr(char, 'is_dead') and char.is_dead))
            active_b_chars = sum(1 for char in team_b_obj.active_characters if not (hasattr(char, 'is_ko') and char.is_ko) and not (hasattr(char, 'is_dead') and char.is_dead))
            
            active_a_boards = sum(1 for board in team_a_boards if not board.is_game_over())
            active_b_boards = sum(1 for board in team_b_boards if not board.is_game_over())
            
            if active_a_chars == 0 or active_b_chars == 0 or (active_a_boards == 0 and active_b_boards == 0):
                if show_details:
                    print("Match ended due to knockouts or game completions.")
                break
        
        # Calculate final results
        team_a_wins = 0
        team_b_wins = 0
        draws = 0
        character_results = []
        
        # Process team A results
        for i, character in enumerate(team_a_obj.active_characters):
            if i >= len(team_a_boards):
                continue
                
            board = team_a_boards[i]
            result = "ongoing"
            
            # Determine result from board state
            if board.is_checkmate():
                result = "win" if board.turn == chess.BLACK else "loss"
            elif board.is_stalemate() or board.is_insufficient_material():
                result = "draw"
            elif character.is_ko or character.is_dead:
                result = "loss"
            else:
                # Determine based on material advantage
                material = team_a_material[i]
                if material > 30:  # Significant advantage
                    result = "win"
                elif material < 15:  # Significant disadvantage
                    result = "loss"
                else:
                    result = "draw"
            
            # Update team wins
            if result == "win":
                team_a_wins += 1
            elif result == "draw":
                draws += 1
            
            # Record character result
            character_results.append({
                "team": "A",
                "character_id": character.id if hasattr(character, 'id') else str(i),
                "character_name": character.name if hasattr(character, 'name') else f"Character A{i}",
                "result": result,
                "final_hp": character.HP if hasattr(character, 'HP') else 0,
                "final_stamina": character.stamina if hasattr(character, 'stamina') else 0,
                "is_ko": character.is_ko if hasattr(character, 'is_ko') else False,
                "is_dead": character.is_dead if hasattr(character, 'is_dead') else False
            })
            
            # Update character stats
            if hasattr(character, 'games_with_team'):
                character.games_with_team += 1
        
        # Process team B results
        for i, character in enumerate(team_b_obj.active_characters):
            if i >= len(team_b_boards):
                continue
                
            board = team_b_boards[i]
            result = "ongoing"
            
            # Determine result from board state
            if board.is_checkmate():
                result = "win" if board.turn == chess.WHITE else "loss"
            elif board.is_stalemate() or board.is_insufficient_material():
                result = "draw"
            elif character.is_ko or character.is_dead:
                result = "loss"
            else:
                # Determine based on material advantage
                material = team_b_material[i]
                if material > 30:  # Significant advantage
                    result = "win"
                elif material < 15:  # Significant disadvantage
                    result = "loss"
                else:
                    result = "draw"
            
            # Update team wins
            if result == "win":
                team_b_wins += 1
            elif result == "draw":
                draws += 1
            
            # Record character result
            character_results.append({
                "team": "B",
                "character_id": character.id if hasattr(character, 'id') else str(i),
                "character_name": character.name if hasattr(character, 'name') else f"Character B{i}",
                "result": result,
                "final_hp": character.HP if hasattr(character, 'HP') else 0,
                "final_stamina": character.stamina if hasattr(character, 'stamina') else 0,
                "is_ko": character.is_ko if hasattr(character, 'is_ko') else False,
                "is_dead": character.is_dead if hasattr(character, 'is_dead') else False
            })
            
            # Update character stats
            if hasattr(character, 'games_with_team'):
                character.games_with_team += 1
        
        # Determine match winner
        if team_a_wins > team_b_wins:
            winner = "Team A"
            winning_team = team_a_name
        elif team_b_wins > team_a_wins:
            winner = "Team B"
            winning_team = team_b_name
        else:
            winner = "Draw"
            winning_team = "None"
        
        if show_details:
            print(f"\nMatch Result: {team_a_name} {team_a_wins} - {team_b_wins} {team_b_name}")
            print(f"Winner: {winning_team}")
        
        # Return final results
        return {
            "team_a_name": team_a_name,
            "team_b_name": team_b_name,
            "team_a_wins": team_a_wins,
            "team_b_wins": team_b_wins,
            "winner": winner,
            "winning_team": winning_team,
            "character_results": character_results,
            "convergence_count": len(match_context["convergence_logs"]),
            "trait_activations": len(match_context["trait_logs"])
        }