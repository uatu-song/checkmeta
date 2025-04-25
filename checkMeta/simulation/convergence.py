class ConvergenceSystem:
    """System for handling convergences between boards with multi-unit interactions"""
    
    def __init__(self, trait_system=None, combat_system=None):
        """Initialize the convergence system"""
        self.trait_system = trait_system
        self.combat_system = combat_system
    
    def process_convergences(self, team_a: Team, team_a_boards: List[chess.Board], 
                           team_b: Team, team_b_boards: List[chess.Board]) -> List[Dict[str, Any]]:
        """Process convergences between boards with support for multi-unit interactions"""
        convergences = []
        
        # BALANCE: Limit the number of convergences per round to prevent overwhelming damage
        max_convergences_per_char = 3
        char_convergence_counts = {char.id: 0 for char in team_a.characters + team_b.characters}
        
        # Track all character pieces on each square
        square_occupants = {square: {"team_a": [], "team_b": []} for square in chess.SQUARES}
        
        # Map each character's pieces to squares
        for a_idx, (a_char, a_board) in enumerate(zip(team_a.active_characters, team_a_boards)):
            # Skip if character is KO'd or dead
            if a_char.is_ko or a_char.is_dead:
                continue
                
            for square in chess.SQUARES:
                a_piece = a_board.piece_at(square)
                if a_piece and a_piece.piece_type != chess.PAWN:
                    square_occupants[square]["team_a"].append((a_idx, a_char))
        
        for b_idx, (b_char, b_board) in enumerate(zip(team_b.active_characters, team_b_boards)):
            # Skip if character is KO'd or dead
            if b_char.is_ko or b_char.is_dead:
                continue
                
            for square in chess.SQUARES:
                b_piece = b_board.piece_at(square)
                if b_piece and b_piece.piece_type != chess.PAWN:
                    square_occupants[square]["team_b"].append((b_idx, b_char))
        
        # Process convergences for each square
        for square, occupants in square_occupants.items():
            team_a_chars = occupants["team_a"]
            team_b_chars = occupants["team_b"]
            
            # Skip if no convergence (needs at least one from each team)
            if not team_a_chars or not team_b_chars:
                continue
                
            # We have a convergence with potentially multiple characters from each team
            team_a_names = [char.name for _, char in team_a_chars]
            team_b_names = [char.name for _, char in team_b_chars]
            square_name = chess.square_name(square)
            
            # Calculate team combined power
            team_a_total_roll = 0
            team_b_total_roll = 0
            
            # Team A power
            for _, a_char in team_a_chars:
                # Skip if character has reached max convergences
                if char_convergence_counts[a_char.id] >= max_convergences_per_char:
                    continue
                    
                # Calculate base roll
                a_roll = 0
                if self.combat_system:
                    a_roll = self.combat_system.calculate_combat_roll(
                        a_char, team_b_chars[0][1], {"trigger": "convergence"}
                    )
                else:
                    # Fallback to simple calculation
                    a_roll = random.randint(1, 100) + a_char.get_attribute('STR') + a_char.get_attribute('FS')
                
                # Apply trait effects for convergence
                if self.trait_system:
                    trait_effects = self.trait_system.apply_trait_effect(
                        a_char, "convergence", {"opponent": team_b_chars[0][1], "roll": a_roll}
                    )
                    
                    for effect in trait_effects:
                        if effect.get("effect") == "combat_bonus":
                            a_roll += effect.get("value", 0)
                
                # Apply team bonus for multiple attackers (synergy bonus)
                if len(team_a_chars) > 1:
                    a_roll *= (1 + 0.15 * (len(team_a_chars) - 1))  # 15% bonus per additional character
                
                team_a_total_roll += a_roll
                char_convergence_counts[a_char.id] += 1
            
            # Team B power (similar logic)
            for _, b_char in team_b_chars:
                # Skip if character has reached max convergences
                if char_convergence_counts[b_char.id] >= max_convergences_per_char:
                    continue
                    
                # Calculate base roll
                b_roll = 0
                if self.combat_system:
                    b_roll = self.combat_system.calculate_combat_roll(
                        b_char, team_a_chars[0][1], {"trigger": "convergence"}
                    )
                else:
                    # Fallback to simple calculation
                    b_roll = random.randint(1, 100) + b_char.get_attribute('STR') + b_char.get_attribute('FS')
                
                # Apply trait effects for convergence
                if self.trait_system:
                    trait_effects = self.trait_system.apply_trait_effect(
                        b_char, "convergence", {"opponent": team_a_chars[0][1], "roll": b_roll}
                    )
                    
                    for effect in trait_effects:
                        if effect.get("effect") == "combat_bonus":
                            b_roll += effect.get("value", 0)
                
                # Apply team bonus for multiple defenders (synergy bonus)
                if len(team_b_chars) > 1:
                    b_roll *= (1 + 0.15 * (len(team_b_chars) - 1))  # 15% bonus per additional character
                
                team_b_total_roll += b_roll
                char_convergence_counts[b_char.id] += 1
            
            # Determine winning team
            if team_a_total_roll > team_b_total_roll:
                winning_team = "A"
                losing_team = "B"
                winning_chars = team_a_chars
                losing_chars = team_b_chars
                winning_roll = team_a_total_roll
                losing_roll = team_b_total_roll
                winning_team_obj = team_a
                losing_team_obj = team_b
            else:
                winning_team = "B"
                losing_team = "A"
                winning_chars = team_b_chars
                losing_chars = team_a_chars
                winning_roll = team_b_total_roll
                losing_roll = team_a_total_roll
                winning_team_obj = team_b
                losing_team_obj = team_a
            
            # Calculate damage with diminishing returns
            diff = winning_roll - losing_roll
            base_damage = max(0, int(3 * math.log(1 + diff/10)))
            
            # Apply damage to all losing team characters
            total_damage = 0
            for _, loser in losing_chars:
                # Divide damage among losers, but add bonus for being outnumbered
                damage_factor = 1.0 / len(losing_chars)
                if len(winning_chars) > len(losing_chars):
                    # Being outnumbered increases damage taken
                    damage_factor *= (1 + 0.2 * (len(winning_chars) - len(losing_chars)))
                    
                damage = max(1, int(base_damage * damage_factor))
                
                # Apply damage with trait effects
                if self.combat_system:
                    winning_char = winning_chars[0][1]  # use first winner as reference
                    damage_result = self.combat_system.calculate_damage(damage, winning_char, loser)
                    actual_damage = damage_result.get("reduced_damage", damage)
                else:
                    # Get damage reduction from loser's traits
                    damage_reduction = 0
                    if self.trait_system:
                        trait_effects = self.trait_system.apply_trait_effect(
                            loser, "damage_taken", {"damage": damage}
                        )
                        
                        for effect in trait_effects:
                            if effect.get("effect") == "damage_reduction":
                                damage_reduction += effect.get("value", 0)
                    
                    damage_result = loser.take_damage(damage, damage_reduction)
                    actual_damage = damage_result.get("reduced_damage", damage)
                
                total_damage += actual_damage
            
            # Record convergence
            winning_names = [char.name for _, char in winning_chars]
            losing_names = [char.name for _, char in losing_chars]
            
            convergence = {
                "square": square_name,
                "winning_team": winning_team,
                "winning_characters": winning_names,
                "losing_characters": losing_names,
                "winning_roll": winning_roll,
                "losing_roll": losing_roll,
                "total_damage": total_damage
            }
            
            convergences.append(convergence)
            
            # Update rStats for winners
            for _, winner in winning_chars:
                # Track assist stats for multi-character convergences
                if len(winning_chars) > 1:
                    winner.r_stats["team_assists"] = winner.r_stats.get("team_assists", 0) + 1
                    
                    # Track specific character assists
                    winner.r_stats.setdefault("assist_with", {})
                    for _, teammate in winning_chars:
                        if teammate.id != winner.id:
                            assist_key = teammate.id
                            if assist_key not in winner.r_stats["assist_with"]:
                                winner.r_stats["assist_with"][assist_key] = 0
                            winner.r_stats["assist_with"][assist_key] += 1
                
                # Ops or Intel division appropriate stat
                if winner.division == "o":
                    winner.r_stats["rCVo"] = winner.r_stats.get("rCVo", 0) + 1
                else:
                    winner.r_stats["rMBi"] = winner.r_stats.get("rMBi", 0) + 1
        
        return convergences