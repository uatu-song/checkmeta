###############################
# systems/simulator.py
###############################
"""
Main simulator system for META League
"""

import json
import os
import random
import math
import chess
from typing import Dict, List, Any, Tuple, Optional
from ..models.team import Team
from ..models.character import Character
from ..models.match import MatchResult
from ..systems.traits import TraitSystem
from ..systems.morale import MoraleSystem
from ..systems.leadership import LeadershipSystem
from ..systems.synergy import SynergySystem
from ..systems.chess_engine import ChessEngine
from ..config.openings import ROLE_OPENINGS
from ..config.game_config import MAX_MOVES_TO_SIMULATE, MAX_CONVERGENCES_PER_CHAR

class MetaLeagueSimulator:
    """Main simulator class for META League"""
    
    def __init__(self, stockfish_path: str = "/usr/local/bin/stockfish"):
        """Initialize the simulator and all subsystems"""
        # Game state
        self.current_day = 1
        
        # Initialize subsystems
        self.trait_system = TraitSystem()
        self.morale_system = MoraleSystem()
        self.leadership_system = LeadershipSystem()
        self.synergy_system = SynergySystem()
        self.chess_engine = ChessEngine(stockfish_path)
        
        # Create results directory
        os.makedirs("results", exist_ok=True)
    
    def simulate_match(self, team_a: List[Character], team_b: List[Character], show_details: bool = True) -> Dict[str, Any]:
        """Simulate a match between two teams"""
        # Create Team objects if they aren't already
        if not isinstance(team_a, Team):
            team_a = Team(team_a)
        if not isinstance(team_b, Team):
            team_b = Team(team_b)
        
        # Show team details
        match_result = MatchResult(team_a, team_b, self.current_day)
        
        if show_details:
            print(f"Match: {match_result.team_a_name} vs {match_result.team_b_name}")
            print(f"Team colors: White vs Black")
            print(f"Active players {match_result.team_a_name}: {[char.name for char in team_a.active_characters]}")
            print(f"Bench players {match_result.team_a_name}: {[char.name for char in team_a.bench_characters]}")
            print(f"Active players {match_result.team_b_name}: {[char.name for char in team_b.active_characters]}")
            print(f"Bench players {match_result.team_b_name}: {[char.name for char in team_b.bench_characters]}")
        
        # Apply leadership bonuses
        self.leadership_system.apply_leadership_bonuses(team_a)
        self.leadership_system.apply_leadership_bonuses(team_b)
        
        # Apply team synergy
        self.synergy_system.apply_team_bonuses(team_a)
        self.synergy_system.apply_team_bonuses(team_b)
        self.synergy_system.calculate_team_synergy(team_a)
        self.synergy_system.calculate_team_synergy(team_b)
        
        # Apply morale effects
        for character in team_a.characters + team_b.characters:
            character.morale_modifiers = self.morale_system.calculate_morale_modifiers(character.morale)
        
        # Create boards for each active character
        team_a_boards = [self.chess_engine.create_board() for _ in team_a.active_characters]
        team_b_boards = [self.chess_engine.create_board() for _ in team_b.active_characters]
        
        # Apply role-based openings
        for i, character in enumerate(team_a.active_characters):
            self.chess_engine.apply_opening(team_a_boards[i], character.role, ROLE_OPENINGS)
        
        for i, character in enumerate(team_b.active_characters):
            self.chess_engine.apply_opening(team_b_boards[i], character.role, ROLE_OPENINGS)
        
        # Track material values
        team_a_material = [self.chess_engine.calculate_material(board) for board in team_a_boards]
        team_b_material = [self.chess_engine.calculate_material(board) for board in team_b_boards]
        
        # Simulate moves
        for move_num in range(MAX_MOVES_TO_SIMULATE):
            match_result.round = move_num + 1
            
            if show_details:
                print(f"\nRound {move_num + 1}:")
            
            # Process convergences
            self._process_convergences(team_a, team_a_boards, team_b, team_b_boards, match_result, show_details)
            
            # Make moves for team A
            for i, (character, board) in enumerate(zip(team_a.active_characters, team_a_boards)):
                if board.is_game_over() or character.is_ko or character.is_dead:
                    continue
                
                # Select and make move
                move = self.chess_engine.select_move(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character.name} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self.chess_engine.calculate_material(board)
                    material_change = new_material - team_a_material[i]
                    team_a_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self._update_character_metrics(character, material_change, show_details)
                    
                    # Check for KO/death
                    if character.hp <= 0 and character.stamina <= 0:
                        if character.life <= 0:
                            character.is_dead = True
                            if show_details:
                                print(f"  {character.name} has DIED!")
                        elif character.hp <= 0:
                            character.is_ko = True
                            if show_details:
                                print(f"  {character.name} is KNOCKED OUT!")
            
            # Make moves for team B (similar logic)
            for i, (character, board) in enumerate(zip(team_b.active_characters, team_b_boards)):
                if board.is_game_over() or character.is_ko or character.is_dead:
                    continue
                
                # Select and make move
                move = self.chess_engine.select_move(board, character)
                
                if move:
                    # Process the move
                    if show_details:
                        print(f"{character.name} moves: {move}")
                    
                    # Make the move
                    board.push(move)
                    
                    # Update material and metrics
                    new_material = self.chess_engine.calculate_material(board)
                    material_change = new_material - team_b_material[i]
                    team_b_material[i] = new_material
                    
                    # Update character metrics based on material change
                    self._update_character_metrics(character, material_change, show_details)
                    
                    # Check for KO/death
                    if character.hp <= 0 and character.stamina <= 0:
                        if character.life <= 0:
                            character.is_dead = True
                            if show_details:
                                print(f"  {character.name} has DIED!")
                        elif character.hp <= 0:
                            character.is_ko = True
                            if show_details:
                                print(f"  {character.name} is KNOCKED OUT!")
            
            # Apply end-of-round effects
            self._apply_end_of_round_effects(
                team_a.active_characters + team_b.active_characters, 
                match_result, 
                show_details
            )
            
            # Check if match is over (all games ended or max moves reached)
            active_games = sum(1 for board, char in zip(team_a_boards, team_a.active_characters)
                             if not board.is_game_over() and 
                                not char.is_ko and 
                                not char.is_dead)
            
            active_games += sum(1 for board, char in zip(team_b_boards, team_b.active_characters)
                              if not board.is_game_over() and 
                                 not char.is_ko and 
                                 not char.is_dead)
            
            if active_games == 0:
                if show_details:
                    print("All games have concluded.")
                break
        
        # Process active team A results
        for i, (character, board) in enumerate(zip(team_a.active_characters, team_a_boards)):
            result = self.chess_engine.determine_game_result(board, character)
            match_result.add_character_result(character, "A", result)
            
            # Calculate XP gain
            self._calculate_xp(character, result)
        
        # Process bench team A results (they didn't participate)
        for character in team_a.bench_characters:
            match_result.add_character_result(character, "A", "bench", was_active=False)
        
        # Process active team B results
        for i, (character, board) in enumerate(zip(team_b.active_characters, team_b_boards)):
            result = self.chess_engine.determine_game_result(board, character)
            match_result.add_character_result(character, "B", result)
            
            # Calculate XP gain
            self._calculate_xp(character, result)
        
        # Process bench team B results (they didn't participate)
        for character in team_b.bench_characters:
            match_result.add_character_result(character, "B", "bench", was_active=False)
        
        # Finalize match result
        match_result.finalize()
        
        if show_details:
            print(f"\nMatch Result: {match_result.team_a_name} {match_result.team_a_wins} - {match_result.team_b_wins} {match_result.team_b_name}")
            print(f"Winner: {match_result.winning_team}")
        
        # Update team morale based on results
        self._update_team_morale(team_a, team_b, match_result.winner)
        
        return match_result.to_dict()
    
    def _process_convergences(self, team_a: Team, team_a_boards: List[chess.Board], 
                             team_b: Team, team_b_boards: List[chess.Board], 
                             match_result: MatchResult, show_details: bool = True) -> List[Dict[str, Any]]:
        """Process convergences between boards"""
        convergences = []
        
        # Limit the number of convergences per round to prevent overwhelming damage
        char_convergence_counts = {char.id: 0 for char in team_a.characters + team_b.characters}
        
        # Check for non-pawn pieces occupying the same square across different boards
        for a_idx, (a_char, a_board) in enumerate(zip(team_a.active_characters, team_a_boards)):
            # Skip if character is KO'd or dead
            if a_char.is_ko or a_char.is_dead:
                continue
                
            # Skip if character has reached max convergences
            if char_convergence_counts[a_char.id] >= MAX_CONVERGENCES_PER_CHAR:
                continue
                
            for b_idx, (b_char, b_board) in enumerate(zip(team_b.active_characters, team_b_boards)):
                # Skip if character is KO'd or dead
                if b_char.is_ko or b_char.is_dead:
                    continue
                
                # Skip if character has reached max convergences
                if char_convergence_counts[b_char.id] >= MAX_CONVERGENCES_PER_CHAR:
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
                        a_trait_effects = self.trait_system.apply_trait_effect(
                            a_char, "convergence", {"opponent": b_char, "roll": a_roll}
                        )
                        
                        b_trait_effects = self.trait_system.apply_trait_effect(
                            b_char, "convergence", {"opponent": a_char, "roll": b_roll}
                        )
                        
                        # Apply trait effect bonuses
                        for effect in a_trait_effects:
                            if effect.get("effect") == "combat_bonus":
                                a_roll += effect.get("value", 0)
                                match_result.add_trait_log({
                                    "round": match_result.round,
                                    "character": a_char.name,
                                    "trait": effect.get("trait_name"),
                                    "effect": f"+{effect.get('value')} to combat roll"
                                })
                        
                        for effect in b_trait_effects:
                            if effect.get("effect") == "combat_bonus":
                                b_roll += effect.get("value", 0)
                                match_result.add_trait_log({
                                    "round": match_result.round,
                                    "character": b_char.name,
                                    "trait": effect.get("trait_name"),
                                    "effect": f"+{effect.get('value')} to combat roll"
                                })
                        
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
                        
                        # Calculate damage with diminishing returns
                        diff = winner_roll - loser_roll
                        # Use a logarithmic scale to reduce extreme differences
                        damage = max(0, int(3 * math.log(1 + diff/10)))
                        
                        # Apply damage to loser
                        # Calculate damage reduction from traits
                        damage_reduction = 0
                        for trait_name in loser.traits:
                            if trait_name in self.trait_system.traits:
                                trait = self.trait_system.traits[trait_name]
                                if trait.get("formula_key") == "damage_reduction":
                                    damage_reduction += trait.get("value", 0)
                        
                        # Apply damage
                        damage_result = loser.take_damage(damage, damage_reduction)
                        
                        # Update convergence counts
                        char_convergence_counts[a_char.id] += 1
                        char_convergence_counts[b_char.id] += 1
                        
                        # Record convergence
                        convergence = {
                            "round": match_result.round,
                            "square": chess.square_name(square),
                            "a_character": a_char.name,
                            "b_character": b_char.name,
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "winner": winner.name,
                            "damage": damage,
                            "actual_damage": damage_result["reduced_damage"]
                        }
                        
                        convergences.append(convergence)
                        match_result.add_convergence_log(convergence)
                        
                        # Update rStats
                        winner.r_stats.setdefault("rCVo" if winner.division == "o" else "rMBi", 0)
                        winner.r_stats["rCVo" if winner.division == "o" else "rMBi"] += 1
                        
                        if show_details:
                            print(f"CONVERGENCE: {a_char.name} ({a_roll}) vs {b_char.name} ({b_roll}) at {chess.square_name(square)}")
                            print(f"  {winner.name} wins! {loser.name} takes {damage_result['reduced_damage']} damage")
                            print(f"  {loser.name} HP: {loser.hp}, Stamina: {loser.stamina}, Life: {loser.life}")
        
        return convergences
    
    def _calculate_combat_roll(self, attacker: Character, defender: Character) -> int:
        """Calculate combat roll based on character stats and traits"""
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        roll += attacker.get_attribute('STR') + attacker.get_attribute('FS')
        
        # Scale by Power Potential
        op_factor = attacker.get_attribute('OP') / 5.0
        roll = int(roll * op_factor)
        
        # Add morale modifier
        if hasattr(attacker, 'morale_modifiers') and attacker.morale_modifiers:
            roll += attacker.morale_modifiers.get("combat_bonus", 0)
        
        # Add team synergy modifier
        if hasattr(attacker, 'team_synergy') and attacker.team_synergy:
            roll += attacker.team_synergy.get("combat_bonus", 0)
        
        # Check for Luck trait
        context = {"roll": roll, "opponent": defender}
        luck_effects = self.trait_system.apply_trait_effect(attacker, "combat_roll", context)
        
        # If luck triggered, apply reroll
        for effect in luck_effects:
            if effect.get("effect") == "reroll":
                # Generate new roll
                new_roll = random.randint(1, 100)
                new_roll += attacker.get_attribute('STR') + attacker.get_attribute('FS')
                new_roll = int(new_roll * op_factor)
                
                # Take the better roll
                roll = max(roll, new_roll)
        
        return roll
    
    def _update_character_metrics(self, character: Character, material_change: int, show_details: bool = False) -> None:
        """Update character metrics based on material change"""
        # Material loss = damage
        if material_change < 0:
            # BALANCE: Reduce damage scaling from material loss
            damage = abs(material_change) * 3  # Reduced from 5 to 3
            
            # Get damage reduction from traits
            damage_reduction = 0
            for trait_name in character.traits:
                if trait_name in self.trait_system.traits:
                    trait = self.trait_system.traits[trait_name]
                    if trait.get("formula_key") == "damage_reduction":
                        damage_reduction += trait.get("value", 0)
            
            # Apply damage
            damage_result = character.take_damage(damage, damage_reduction)
            
            # Update rStats for damage sustained
            character.r_stats.setdefault("rDSo" if character.division == "o" else "rDSi", 0)
            character.r_stats["rDSo" if character.division == "o" else "rDSi"] += damage_result["reduced_damage"]
            
            if show_details:
                print(f"  {character.name} HP: {character.hp}, Stamina: {character.stamina}, Life: {character.life}")
        
        # Material gain = damage dealt to opponent
        elif material_change > 0:
            # BALANCE: Reduce damage scaling for stats
            damage_dealt = material_change * 3  # Reduced from 5 to 3
            
            # Update rStats for damage dealt
            character.r_stats.setdefault("rDDo" if character.division == "o" else "rDDi", 0)
            character.r_stats["rDDo" if character.division == "o" else "rDDi"] += damage_dealt
        
        # Higher stamina cost with aStats influence
        base_stamina_cost = 1.5  # Increased from 0.5 to 1.5
        
        # Apply aStats modifiers to stamina cost
        dur_factor = max(0.7, 1.0 - (character.get_attribute('DUR') - 5) * 0.05)  # 5% reduction per DUR above 5, min 30% cost
        res_factor = max(0.7, 1.0 - (character.get_attribute('RES') - 5) * 0.03)  # 3% reduction per RES above 5, min 30% cost
        wil_factor = max(0.7, 1.0 - (character.get_attribute('WIL') - 5) * 0.08)  # 8% reduction per WIL above 5, min 30% cost
        
        # Combined factor - multiply all factors together
        combined_factor = dur_factor * res_factor * wil_factor
        
        # Apply stamina cost with aStats influence
        stamina_cost = base_stamina_cost * combined_factor
        
        character.stamina = max(0, character.stamina - stamina_cost)
    
    def _apply_end_of_round_effects(self, characters: List[Character], match_result: MatchResult, show_details: bool = True) -> None:
        """Apply end-of-round effects with improved recovery"""
        for character in characters:
            # Skip dead characters
            if character.is_dead:
                continue
                    
            # Moderate HP regeneration
            base_hp_regen = 3  # Reduced from 5 back to 3
            
            # Regeneration effects from traits
            trait_heal_amount = 0
            trait_effects = self.trait_system.apply_trait_effect(character, "end_of_turn", {})
            
            for effect in trait_effects:
                if effect.get("effect") == "healing":
                    # BALANCE: Moderate healing trait effectiveness
                    trait_heal_amount = effect.get("value", 0) * 2  # Reduced from 3x to 2x
                    match_result.add_trait_log({
                        "round": match_result.round,
                        "character": character.name,
                        "trait": effect.get("trait_name"),
                        "effect": f"+{effect.get('value') * 2} healing"
                    })
            
            # Apply recovery
            recovery_result = character.recover(base_hp_regen, 2, trait_heal_amount)
            
            # Log recovery from KO
            if recovery_result["recovered_from_ko"]:
                if show_details:
                    print(f"  {character.name} has recovered from knockout!")
    
    def _calculate_xp(self, character: Character, result: str) -> int:
        """Calculate XP gained in the match"""
        # Base XP from result
        xp = 0
        if result == "win":
            xp += 25
            character.r_stats.setdefault("rWIN", 0)
            character.r_stats["rWIN"] += 1
        elif result == "draw":
            xp += 10
        
        # XP from rStats
        r = character.r_stats
        xp += (
            r.get("rDDo", 0) // 5 +
            r.get("rDDi", 0) // 5 +
            r.get("rCVo", 0) * 10 +
            r.get("rMBi", 0) * 10 +
            r.get("rLVSo", 0) * 5 +
            r.get("rLVSi", 0) * 5
        )
        
        # Apply AM (Adaptive Mastery) modifier
        am_factor = character.get_attribute('AM') / 5.0
        xp = int(xp * am_factor)
        
        # Update character XP
        character.xp_earned = xp
        character.xp_total += xp
        
        return xp
    
    def _update_team_morale(self, team_a: Team, team_b: Team, winner: str) -> None:
        """Update team morale based on match result"""
        # Team A morale changes
        morale_change = 10 if winner == "Team A" else -5 if winner == "Team B" else 0
        for character in team_a.characters:
            self.morale_system.update_morale(character, "custom", morale_change)
        
        # Team B morale changes
        morale_change = 10 if winner == "Team B" else -5 if winner == "Team A" else 0
        for character in team_b.characters:
            self.morale_system.update_morale(character, "custom", morale_change)
    
    def export_results(self, results: List[Dict[str, Any]], file_path: str) -> None:
        """Export match results to JSON file"""
        with open(file_path, "w") as f:
            json.dump(results, f, indent=2)
    
    def apply_between_match_recovery(self, teams: Dict[str, List[Character]], show_details: bool = True) -> Dict[str, List[Character]]:
        """Apply between-match recovery for all teams"""
        for team_id, team_chars in teams.items():
            team = Team(team_chars) if not isinstance(team_chars, Team) else team_chars
            
            if show_details:
                print(f"\nApplying between-match recovery for {team.team_name}:")
            
            for character in team.characters:
                # Initialize recovery factors based on character attributes
                recovery_factor = 0.3  # Base recovery is 30% of depleted resources
                
                # Healing trait enhances recovery
                has_healing_trait = "healing" in character.traits
                if has_healing_trait:
                    recovery_factor += 0.2  # +20% recovery with healing trait
                
                # WIL enhances stamina recovery
                wil_bonus = max(0, character.get_attribute('WIL') - 5) * 0.03  # 3% per point above 5
                recovery_factor += wil_bonus
                
                # For knocked out characters, limited recovery
                if character.is_ko:
                    # Calculate stamina recovery (only 30% of depleted stamina)
                    missing_stamina = 100 - character.stamina
                    stamina_recovery = missing_stamina * 0.3  # Only 30% recovery
                    
                    # Apply stamina recovery
                    character.stamina = min(100, character.stamina + stamina_recovery)
                    
                    # Knocked out status remains
                    if show_details:
                        print(f"  {character.name}: KO state continues, stamina +{stamina_recovery:.1f}")
                else:
                    # Regular character recovery
                    # Calculate HP recovery
                    missing_hp = 100 - character.hp
                    hp_recovery = missing_hp * recovery_factor
                    
                    # Calculate stamina recovery 
                    missing_stamina = 100 - character.stamina
                    stamina_recovery = missing_stamina * recovery_factor
                    
                    # Apply recovery
                    character.hp = min(100, character.hp + hp_recovery)
                    character.stamina = min(100, character.stamina + stamina_recovery)
                    
                    if show_details and (hp_recovery > 0 or stamina_recovery > 0):
                        print(f"  {character.name}: HP +{hp_recovery:.1f}, Stamina +{stamina_recovery:.1f}")
            
            # Update team in the dict if it's a Team object
            if isinstance(team_chars, Team):
                teams[team_id] = team
        
        return teams