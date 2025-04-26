"""
META Fantasy League Simulator - Combat System
Handles combat mechanics during simulation
"""

import os
import random
import chess
import chess.engine

class CombatSystem:
    """System for handling combat mechanics during simulation"""
    
    def __init__(self, stockfish_path=None):
        """Initialize the combat system
        
        Args:
            stockfish_path (str, optional): Path to Stockfish executable. Defaults to None.
        """
        self.stockfish_path = stockfish_path
        self.stockfish_available = stockfish_path and os.path.exists(stockfish_path)
        if self.stockfish_path and not self.stockfish_available:
            print(f"Warning: Stockfish not found at {stockfish_path}")
    
    def select_move(self, board, character):
        """Select a chess move for a character
        
        Args:
            board: Chess board
            character: Character making the move
            
        Returns:
            chess.Move: Selected move or None if no legal moves
        """
        # Get legal moves
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None
        
        if self.stockfish_available:
            try:
                return self.select_move_with_stockfish(board, character)
            except Exception as e:
                print(f"Stockfish error: {e}")
                # Fallback to basic move selection
        
        # Basic move selection without Stockfish
        # Character stats influence move quality
        move_quality = 0.5  # Default
        
        # Use FS and STR stats to influence move quality if available
        fs = getattr(character, 'aFS', 5) if hasattr(character, 'aFS') else 5
        str_val = getattr(character, 'aSTR', 5) if hasattr(character, 'aSTR') else 5
        move_quality = min(max(0.3, (fs + str_val) / 20), 0.9)  # Scale to 0.3-0.9
        
        # Apply stamina penalty
        stamina = getattr(character, 'stamina', 100) if hasattr(character, 'stamina') else 100
        stamina_factor = max(0.5, stamina / 100)
        move_quality *= stamina_factor
        
        # Sometimes select random moves based on character skill
        if random.random() > move_quality:
            return random.choice(legal_moves)
        
        # Look for better moves
        captures = [move for move in legal_moves if board.is_capture(move)]
        checks = [move for move in legal_moves if board.gives_check(move)]
        
        # Prefer checks and captures
        if checks and random.random() < 0.7:
            return random.choice(checks)
        elif captures and random.random() < 0.6:
            return random.choice(captures)
        
        # Fall back to random move
        return random.choice(legal_moves)
    
    def select_move_with_stockfish(self, board, character):
        """Select a move using Stockfish with character stats influencing quality
        
        Args:
            board: Chess board
            character: Character making the move
            
        Returns:
            chess.Move: Selected move
        """
        # Calculate search depth based on character stats
        # Higher stats = deeper search = better moves
        fs = getattr(character, 'aFS', 5) if hasattr(character, 'aFS') else 5
        int_val = getattr(character, 'aSTR', 5) if hasattr(character, 'aSTR') else 5
        base_depth = min(max(2, (fs + int_val) // 3), 10)
        
        # Adjust depth based on character stamina (tired = worse decisions)
        stamina = getattr(character, 'stamina', 100) if hasattr(character, 'stamina') else 100
        stamina_factor = max(0.5, stamina / 100)
        adjusted_depth = max(1, int(base_depth * stamina_factor))
        
        # Time limit based on character's focus
        time_ms = fs * 50
        
        # Open Stockfish engine
        with chess.engine.SimpleEngine.popen_uci(self.stockfish_path) as engine:
            # Get move from engine
            result = engine.play(
                board,
                chess.engine.Limit(depth=adjusted_depth, time=time_ms/1000.0)
            )
            return result.move
    
    def update_character_metrics(self, character, material_change, context):
        """Update character metrics based on material change
        
        Args:
            character: Character to update
            material_change: Change in material value
            context: Match context
        """
        # Material loss = damage
        if material_change < 0:
            damage = abs(material_change) * 3
            self.apply_damage(character, damage)
            
            # Update stats
            if hasattr(character, 'rStats'):
                if getattr(character, 'division', 'o') == 'o':
                    if not hasattr(character.rStats, 'rDSo'):
                        character.rStats['rDSo'] = 0
                    character.rStats['rDSo'] = character.rStats.get('rDSo', 0) + damage
            
            # Print damage details
            if hasattr(character, 'HP') and hasattr(character, 'stamina'):
                print(f"  {character.name} takes {damage:.1f} damage - HP: {character.HP:.1f}, Stamina: {character.stamina:.1f}")
        
        # Material gain = damage dealt
        elif material_change > 0:
            damage_dealt = material_change * 3
            
            # Update stats
            if hasattr(character, 'rStats'):
                if getattr(character, 'division', 'o') == 'o':
                    if not hasattr(character.rStats, 'rDDo'):
                        character.rStats['rDDo'] = 0
                    character.rStats['rDDo'] = character.rStats.get('rDDo', 0) + damage_dealt
        
        # Stamina cost
        stamina_cost = 0.8
        
        # Apply WIL bonus to reduce stamina cost
        wil_bonus = (getattr(character, 'aWIL', 5) - 5) * 0.08
        stamina_cost *= max(0.3, 1 - wil_bonus)
        
        # Apply stamina cost
        if hasattr(character, 'stamina'):
            character.stamina = max(0, character.stamina - stamina_cost)
    
    def apply_damage(self, character, damage):
        """Apply damage to a character
        
        Args:
            character: Character taking damage
            damage: Amount of damage
        """
        # Skip if character can't take damage
        if not hasattr(character, 'HP'):
            return
        
        # Get reduction from traits if any
        reduction = 0
        if hasattr(character, 'traits'):
            for trait_name in character.traits:
                # Check if trait provides damage reduction
                if trait_name in ['armor', 'shield']:
                    reduction += 15
        
        # Apply stats for damage reduction
        dur_bonus = (getattr(character, 'aDUR', 5) - 5) * 5
        res_bonus = (getattr(character, 'aRES', 5) - 5) * 3
        reduction += dur_bonus + res_bonus
        
        # Cap reduction at 75%
        reduction = min(75, max(0, reduction))
        
        # Calculate final damage
        actual_damage = damage * (1 - reduction/100.0)
        
        # Apply to HP
        hp_before = character.HP
        character.HP = max(0, character.HP - actual_damage)
        
        # If HP depleted, apply to stamina
        if character.HP == 0:
            stamina_damage = (actual_damage - hp_before) * 0.5
            
            if hasattr(character, 'stamina'):
                stamina_before = character.stamina
                character.stamina = max(0, character.stamina - stamina_damage)
                
                # Set KO status if stamina also depleted
                if character.stamina == 0:
                    character.is_ko = True
                    print(f"  {character.name} is KNOCKED OUT!")
    
    def process_convergences(self, team_a, team_a_boards, team_b, team_b_boards, trait_system, context):
        """Process convergences (pieces on same squares across boards)
        
        Args:
            team_a: Team A object
            team_a_boards: List of chess boards for team A
            team_b: Team B object
            team_b_boards: List of chess boards for team B
            trait_system: TraitSystem for handling trait activations
            context: Match context
            
        Returns:
            list: Convergence events that occurred
        """
        convergences = []
        
        # For each pair of boards, check for pieces on the same square
        for a_idx, a_board in enumerate(team_a_boards):
            if a_idx >= len(team_a.active_characters):
                continue
                
            a_char = team_a.active_characters[a_idx]
            
            # Skip KO'd characters
            if hasattr(a_char, 'is_ko') and a_char.is_ko:
                continue
                
            for b_idx, b_board in enumerate(team_b_boards):
                if b_idx >= len(team_b.active_characters):
                    continue
                    
                b_char = team_b.active_characters[b_idx]
                
                # Skip KO'd characters
                if hasattr(b_char, 'is_ko') and b_char.is_ko:
                    continue
                
                # Check each square for pieces from both boards
                for square in chess.SQUARES:
                    a_piece = a_board.piece_at(square)
                    b_piece = b_board.piece_at(square)
                    
                    # If both have a piece on this square, create a convergence
                    if a_piece and b_piece and a_piece.piece_type != chess.PAWN and b_piece.piece_type != chess.PAWN:
                        # Combat roll for each character
                        a_roll = self.calculate_combat_roll(a_char, b_char)
                        b_roll = self.calculate_combat_roll(b_char, a_char)
                        
                        # Apply trait bonuses if trait system is available
                        if trait_system:
                            a_traits = trait_system.check_trait_activation(a_char, "convergence")
                            for trait in a_traits:
                                a_roll += trait.get('value', 0)
                            
                            b_traits = trait_system.check_trait_activation(b_char, "convergence")
                            for trait in b_traits:
                                b_roll += trait.get('value', 0)
                        
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
                        
                        # Calculate damage
                        damage = max(1, (winner_roll - loser_roll) // 3)
                        
                        # Apply damage
                        self.apply_damage(loser, damage)
                        
                        # Get square name for logging
                        square_name = chess.square_name(square)
                        
                        print(f"CONVERGENCE at {square_name}: {a_char.name} ({a_roll}) vs {b_char.name} ({b_roll})")
                        print(f"  {winner.name} wins! {loser.name} takes {damage} damage")
                        
                        # Record convergence
                        convergence = {
                            "square": square_name,
                            "a_character": a_char.name if hasattr(a_char, 'name') else f"Character A{a_idx}",
                            "b_character": b_char.name if hasattr(b_char, 'name') else f"Character B{b_idx}",
                            "a_roll": a_roll,
                            "b_roll": b_roll,
                            "winner": winner.name if hasattr(winner, 'name') else "Unknown",
                            "damage": damage
                        }
                        
                        convergences.append(convergence)
                        
                        # Update stats
                        if hasattr(winner, 'rStats'):
                            if getattr(winner, 'division', '') == 'o':
                                winner.rStats['rCVo'] = winner.rStats.get('rCVo', 0) + 1
                            else:
                                winner.rStats['rMBi'] = winner.rStats.get('rMBi', 0) + 1
        
        return convergences
    
    def calculate_combat_roll(self, attacker, defender):
        """Calculate combat roll for convergence
        
        Args:
            attacker: Attacking character
            defender: Defending character
            
        Returns:
            int: Combat roll value
        """
        # Base roll (1-100)
        roll = random.randint(1, 100)
        
        # Add stat bonuses
        str_val = getattr(attacker, 'aSTR', 5) if hasattr(attacker, 'aSTR') else 5
        spd_val = getattr(attacker, 'aSPD', 5) if hasattr(attacker, 'aSPD') else 5
        fs_val = getattr(attacker, 'aFS', 5) if hasattr(attacker, 'aFS') else 5
        
        roll += str_val + fs_val
        
        # Scale by OP (Operations Potential)
        op_factor = getattr(attacker, 'aOP', 5) / 5.0 if hasattr(attacker, 'aOP') else 1.0
        roll = int(roll * op_factor)
        
        # Apply morale factor
        morale = getattr(attacker, 'morale', 50) if hasattr(attacker, 'morale') else 50
        morale_factor = morale / 50.0
        roll = int(roll * morale_factor)
        
        return roll