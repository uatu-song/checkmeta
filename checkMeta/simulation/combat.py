"""
META Fantasy League Simulator - Combat System
Handles combat mechanics and damage resolution
"""

import random
import math
import chess
import chess.engine
from typing import Dict, List, Any, Optional

class CombatSystem:
    """System for handling combat mechanics during simulation"""
    
    def __init__(self, trait_system=None, stockfish_path=None):
        """Initialize the combat system
        
        Args:
            trait_system: Optional trait system for trait activations
            stockfish_path: Path to Stockfish engine executable
        """
        self.trait_system = trait_system
        self.stockfish_path = stockfish_path
        self.stockfish_available = stockfish_path and os.path.exists(stockfish_path)
    
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
                        
                        # Apply trait effects for convergence if trait system exists
                        if self.trait_system:
                            a_trait_context = {"opponent": b_char, "square": square}
                            a_traits = self.trait_system.check_trait_activation(a_char, "convergence", a_trait_context)
                            a_effects = self.trait_system.apply_trait_effects(a_char, a_traits, a_trait_context)
                            
                            if "bonus_roll" in a_effects:
                                a_roll += a_effects["bonus_roll"]
                                # Log trait activation
                                context["trait_logs"].append({
                                    "round": context["round"],
                                    "character": a_char["name"],
                                    "trait": a_traits[0]["name"] if a_traits else "Unknown",
                                    "effect": f"+{a_effects['bonus_roll']} to combat roll",
                                    "value": a_effects["bonus_roll"]
                                })
                                # Update combat stats
                                if "combat_stats" in a_char:
                                    a_char["combat_stats"]["special_ability_uses"] += 1
                            
                            b_trait_context = {"opponent": a_char, "square": square}
                            b_traits = self.trait_system.check_trait_activation(b_char, "convergence", b_trait_context)
                            b_effects = self.trait_system.apply_trait_effects(b_char, b_traits, b_trait_context)
                            
                            if "bonus_roll" in b_effects:
                                b_roll += b_effects["bonus_roll"]
                                # Log trait activation
                                context["trait_logs"].append({
                                    "round": context["round"],
                                    "character": b_char["name"],
                                    "trait": b_traits[0]["name"] if b_traits else "Unknown",
                                    "effect": f"+{b_effects['bonus_roll']} to combat roll",
                                    "value": b_effects["bonus_roll"]
                                })
                                # Update combat stats
                                if "combat_stats" in b_char:
                                    b_char["combat_stats"]["special_ability_uses"] += 1
                        
                        # Store possible convergence with priority value (difference between rolls)
                        all_possible_convergences.append({
                            "square": square,
                            "a_idx": a_idx,
                            "b_idx": b_idx,
                            "a_char": a_char,
                            "b_char": b_char,
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "priority": abs(a_roll - b_roll)  # Higher difference = more dramatic convergence
                        })
        
        # Sort convergences by priority and take only the top ones
        all_possible_convergences.sort(key=lambda x: x["priority"], reverse=True)
        selected_convergences = all_possible_convergences[:MAX_CONVERGENCES_PER_ROUND]
        
        # Process selected convergences with damage buffer to prevent first-strike bias
        damage_buffer = []
        
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
            
            # Calculate damage with diminishing returns
            diff = winner_roll - loser_roll
            # Use a logarithmic scale to reduce extreme differences
            base_damage = max(0, int(3 * math.log(1 + diff/10)))
            damage = base_damage * damage_factor
            
            # Get damage reduction from traits
            damage_reduction = 0
            if self.trait_system:
                damage_context = {"damage": damage, "source": winner}
                traits = self.trait_system.check_trait_activation(loser, "damage_taken", damage_context)
                effects = self.trait_system.apply_trait_effects(loser, traits, damage_context)
                
                if "damage_reduction" in effects:
                    damage_reduction = effects["damage_reduction"]
                    if "combat_stats" in loser:
                        loser["combat_stats"]["special_ability_uses"] += 1
                        
                    # Log trait activation
                    context["trait_logs"].append({
                        "round": context["round"],
                        "character": loser["name"],
                        "trait": traits[0]["name"] if traits else "Unknown",
                        "effect": f"{damage_reduction}% damage reduction",
                        "value": damage_reduction
                    })
            
            # Add to damage buffer instead of applying immediately
            damage_buffer.append({
                "target": loser,
                "source": winner,
                "damage": damage,
                "damage_reduction": damage_reduction,
                "square_name": chess.square_name(square),
                "winner_roll": winner_roll,
                "loser_roll": loser_roll
            })
            
            # Update convergence counts
            char_convergence_counts[a_char["id"]] += 1
            char_convergence_counts[b_char["id"]] += 1
            
        # Apply all buffered damage after all calculations
        for damage_entry in damage_buffer:
            actual_damage = self.apply_damage(
                damage_entry["target"], 
                damage_entry["damage"], 
                damage_entry["source"], 
                damage_entry["damage_reduction"], 
                context
            )
            
            # Record convergence
            convergence = {
                "square": damage_entry["square_name"],
                "a_character": a_char["name"],
                "b_character": b_char["name"],
                "a_roll": a_roll,
                "b_roll": b_roll,
                "winner": damage_entry["source"]["name"],
                "damage": damage_entry["damage"],
                "actual_damage": actual_damage,
                "damage_reduction": damage_entry["damage_reduction"]
            }
            
            convergences.append(convergence)
            context["convergence_logs"].append(convergence)
            
            # Update rStats
            damage_entry["source"].setdefault("rStats", {})
            damage_entry["target"].setdefault("rStats", {})
            
            # Update tiles captured in combat stats
            if "combat_stats" in damage_entry["source"]:
                damage_entry["source"]["combat_stats"]["tiles_captured"] += 1
            
            # Ops or Intel division appropriate stat
            if damage_entry["source"].get("division") == "o":
                damage_entry["source"]["rStats"]["rCVo"] = damage_entry["source"]["rStats"].get("rCVo", 0) + 1
            else:
                damage_entry["source"]["rStats"]["rMBi"] = damage_entry["source"]["rStats"].get("rMBi", 0) + 1
            
            if show_details:
                print(f"CONVERGENCE: {a_char['name']} vs {b_char['name']} at {damage_entry['square_name']}")
                print(f"  {damage_entry['source']['name']} wins! {damage_entry['target']['name']} takes {actual_damage} damage")
        
        return convergences
    
    def calculate_combat_roll(self, attacker, defender):
        """Calculate combat roll based on character stats and traits"""
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        str_val = attacker.get("aSTR", 5)
        fs_val = attacker.get("aFS", 5)
        roll += str_val + fs_val
        
        # Scale by Power Potential
        op_factor = attacker.get("aOP", 5) / 5.0
        roll = int(roll * op_factor)
        
        # Apply morale modifier if present
        morale = attacker.get("morale", 50)
        morale_modifier = 1.0
        if morale < 30:  # Low morale
            morale_modifier = 0.8
        elif morale > 70:  # High morale
            morale_modifier = 1.2
        
        roll = int(roll * morale_modifier)
        
        # Apply momentum factor if present
        momentum_state = attacker.get("momentum_state", "stable")
        if momentum_state == "building":
            roll = int(roll * 1.1)  # 10% bonus when in building momentum
        elif momentum_state == "crash":
            roll = int(roll * 0.9)  # 10% penalty when crashing
        
        return roll
    
    def apply_damage(self, character, damage, source_character=None, damage_reduction=0, context=None):
        """Apply damage to a character with improved survivability and damage tracking"""
        context = context or {}
        
        # BALANCE: Reduce base damage
        base_damage = max(1, damage * 0.3)  # Reduce by 70%
        
        # Apply damage reduction from character stats
        # DUR/RES stat bonuses
        dur_bonus = (character.get("aDUR", 5) - 5) * 10  # 10% per point above 5
        res_bonus = (character.get("aRES", 5) - 5) * 8   # 8% per point above 5
        
        # Base reduction + trait reduction + stat bonuses
        reduction = 30 + damage_reduction + dur_bonus + res_bonus
        
        # Apply comeback mechanic for teams in crash momentum
        if context.get("team_momentum", {}).get("state") == "crash":
            reduction += 15  # Additional 15% damage reduction
        
        # Cap reduction at 85%
        reduction = min(max(0, reduction), 85)
        actual_damage = max(1, base_damage * (1 - reduction/100.0))
        
        # Apply to HP first
        current_hp = character.get("HP", 100)
        new_hp = max(0, current_hp - actual_damage)
        character["HP"] = new_hp
        
        # Update damage stats if they exist
        if "combat_stats" in character:
            character["combat_stats"]["damage_taken"] += actual_damage
        
        if source_character and "combat_stats" in source_character:
            source_character["combat_stats"]["damage_dealt"] += actual_damage
            
            # Track damage contributors for assists
            if context and "damage_contributors" in context:
                if character["id"] not in context["damage_contributors"]:
                    context["damage_contributors"][character["id"]] = []
                
                if source_character["id"] not in context["damage_contributors"][character["id"]]:
                    context["damage_contributors"][character["id"]].append(source_character["id"])
        
        # Overflow to stamina if HP is depleted
        stamina_damage = 0
        if new_hp == 0:
            # Reduce stamina damage rate
            stamina_damage = (actual_damage - current_hp) * 0.4
            
            current_stamina = character.get("stamina", 100)
            new_stamina = max(0, current_stamina - stamina_damage)
            character["stamina"] = new_stamina
            
            # Check for KO
            if new_stamina == 0:
                character["is_ko"] = True
                
                # Life damage only in extreme cases
                life_threshold = 100
                if stamina_damage > (current_stamina + life_threshold):
                    life_damage = 0.5  # Fractional life loss
                    character["life"] = max(0, character.get("life", 100) - life_damage)
                
                # Track KO and assists
                if source_character and "combat_stats" in source_character:
                    source_character["combat_stats"]["opponent_kos"] += 1
                    
                    # Award assists
                    if context and "damage_contributors" in context:
                        if character["id"] in context["damage_contributors"]:
                            for contributor_id in context["damage_contributors"][character["id"]]:
                                # Skip the KO giver
                                if contributor_id != source_character["id"]:
                                    # Find and update contributor
                                    for team in [context.get("team_a", []), context.get("team_b", [])]:
                                        for char in team:
                                            if char["id"] == contributor_id and "combat_stats" in char:
                                                char["combat_stats"]["assists"] += 1
                                                break
        
        return actual_damage
    
    def select_move(self, board, character):
        """Select a chess move for a character"""
        # Basic fallback if no stockfish available
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
            
        if not self.stockfish_available:
            # Select based on character quality
            captures = [move for move in legal_moves if board.is_capture(move)]
            checks = [move for move in legal_moves if board.gives_check(move)]
            
            # Higher quality characters prefer tactical moves
            fs_val = character.get("aFS", 5)
            int_val = character.get("aINT", 5) 
            quality_threshold = (fs_val + int_val) / 20  # 0.5 for average character
            
            if random.random() < quality_threshold:
                # Choose tactically
                if checks and random.random() < 0.7:
                    return random.choice(checks)
                elif captures and random.random() < 0.6:
                    return random.choice(captures)
            
            # Otherwise random
            return random.choice(legal_moves)
        
        try:
            # Using stockfish with character stats influencing depth/quality
            base_depth = min(max(2, character.get("aSPD", 5) // 2), 10)
            
            # Adjust for stamina
            stamina_factor = max(0.5, character.get("stamina", 100) / 100)
            adjusted_depth = max(1, int(base_depth * stamina_factor))
            
            with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
                # Thinking time based on Focus/Speed
                thinking_ms = character.get("aFS", 5) * 50
                
                # Get stockfish analysis
                limit = chess.engine.Limit(depth=adjusted_depth, time=thinking_ms/1000.0)
                
                # Quality roll affected by character stats
                quality_roll = random.random()
                quality_boost = (character.get("aSTR", 5) + character.get("aFS", 5)) / 20.0
                
                # Trait impact on quality
                for trait_name in character.get("traits", []):
                    # Implementation details would depend on your trait system
                    # This is a placeholder for trait bonuses
                    quality_boost += 0.05
                
                # Momentum and morale impacts
                if character.get("momentum_state") == "building":
                    quality_boost += 0.1
                elif character.get("momentum_state") == "crash":
                    quality_boost -= 0.1
                
                quality_roll += quality_boost
                
                # Move selection based on quality roll
                if quality_roll > 0.9:  # Brilliant move
                    result = engine.play(board, limit)
                    return result.move
                elif quality_roll > 0.7:  # Good move
                    # Top 3 moves
                    analysis = engine.analyse(board, limit, multipv=3)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                elif quality_roll > 0.4:  # Decent move
                    # Top 5 moves
                    analysis = engine.analyse(board, limit, multipv=5)
                    if analysis:
                        moves = [entry["pv"][0] for entry in analysis if "pv" in entry and entry["pv"]]
                        return random.choice(moves) if moves else None
                else:  # Suboptimal move
                    # Avoid obvious blunders but not optimal
                    if random.random() > 0.3:
                        info = engine.analyse(board, chess.engine.Limit(depth=1))
                        if "pv" in info and info["pv"]:
                            return info["pv"][0]
                    return random.choice(legal_moves)
                    
        except Exception as e:
            print(f"Stockfish error: {e}")
            return random.choice(legal_moves)
            
        # Final fallback
        return random.choice(legal_moves)
    
    def recover_character(self, character, base_hp_regen=5, base_stamina_regen=5, trait_healing=0):
        """Apply healing and recovery to a character"""
        # Apply total healing
        total_heal = base_hp_regen + trait_healing
        
        # Only heal if not at full HP
        if character.get("HP", 100) < 100:
            old_hp = character.get("HP", 0)
            character["HP"] = min(100, old_hp + total_heal)
            heal_amount = character["HP"] - old_hp
            
            # Update healing stats
            if "combat_stats" in character:
                character["combat_stats"]["healing_received"] += heal_amount
            
            return heal_amount
        
        # Apply stamina regeneration
        old_stamina = character.get("stamina", 0)
        character["stamina"] = min(100, old_stamina + base_stamina_regen)
        stamina_gain = character["stamina"] - old_stamina
        
        # Check KO recovery
        recovered_from_ko = False
        if character.get("is_ko", False):
            # KO recovery chance scaled by current stamina
            stamina = character.get("stamina", 0)
            if stamina > 20:
                recovery_chance = stamina / 150
                if random.random() < recovery_chance:
                    character["is_ko"] = False
                    character["HP"] = max(20, character.get("HP", 0))
                    recovered_from_ko = True
        
        return {
            "heal_amount": 0,
            "stamina_gain": stamina_gain,
            "recovered_from_ko": recovered_from_ko
        }