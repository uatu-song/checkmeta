"""
META Fantasy League Simulator - Convergence System
Handles convergence detection and resolution between chess boards
"""

import random
import chess

class ConvergenceSystem:
    """System for detecting and resolving convergences between chess boards"""
    
    def __init__(self, trait_system=None):
        """Initialize the convergence system
        
        Args:
            trait_system: Optional TraitSystem for trait activations
        """
        self.trait_system = trait_system
    
    def detect_convergences(self, team_a_boards, team_b_boards, team_a_chars, team_b_chars):
        """Detect convergences between two sets of boards
        
        Args:
            team_a_boards (list): List of chess boards for team A
            team_b_boards (list): List of chess boards for team B
            team_a_chars (list): List of characters for team A
            team_b_chars (list): List of characters for team B
            
        Returns:
            list: List of convergence tuples (square, a_idx, b_idx)
        """
        convergences = []
        
        # Check each pair of boards
        for a_idx, a_board in enumerate(team_a_boards):
            # Skip if index is out of range for characters
            if a_idx >= len(team_a_chars):
                continue
                
            # Skip if character is KO'd or dead
            if hasattr(team_a_chars[a_idx], 'is_ko') and team_a_chars[a_idx].is_ko:
                continue
            if hasattr(team_a_chars[a_idx], 'is_dead') and team_a_chars[a_idx].is_dead:
                continue
            
            for b_idx, b_board in enumerate(team_b_boards):
                # Skip if index is out of range for characters
                if b_idx >= len(team_b_chars):
                    continue
                    
                # Skip if character is KO'd or dead
                if hasattr(team_b_chars[b_idx], 'is_ko') and team_b_chars[b_idx].is_ko:
                    continue
                if hasattr(team_b_chars[b_idx], 'is_dead') and team_b_chars[b_idx].is_dead:
                    continue
                
                # Check each square for pieces from both boards
                for square in chess.SQUARES:
                    a_piece = a_board.piece_at(square)
                    b_piece = b_board.piece_at(square)
                    
                    # If both have a piece on this square, create a convergence
                    # Ignore pawn convergences
                    if a_piece and b_piece and a_piece.piece_type != chess.PAWN and b_piece.piece_type != chess.PAWN:
                        convergences.append((square, a_idx, b_idx))
        
        return convergences
    
    def resolve_convergence(self, square, a_char, b_char, context=None):
        """Resolve a convergence between two characters
        
        Args:
            square (int): Chess square index
            a_char: Character A
            b_char: Character B
            context (dict, optional): Additional context. Defaults to None.
            
        Returns:
            dict: Convergence result
        """
        context = context or {}
        
        # Get character names
        a_name = getattr(a_char, 'name', 'Character A')
        b_name = getattr(b_char, 'name', 'Character B')
        
        # Calculate combat rolls for each character
        a_roll = self.calculate_combat_roll(a_char, b_char)
        b_roll = self.calculate_combat_roll(b_char, a_char)
        
        # Apply trait bonuses if trait system is available
        if self.trait_system:
            # Create a context for trait activation
            trait_context = {
                'combat': True,
                'convergence': True,
                'square': square,
                'opponent': b_char
            }
            
            # Check for trait activations
            a_traits = self.trait_system.check_trait_activation(a_char, "convergence", trait_context)
            for trait in a_traits:
                a_roll += trait.get('value', 0)
                print(f"  {a_name}'s {trait.get('name')} activated! +{trait.get('value')} to combat roll")
            
            trait_context['opponent'] = a_char
            b_traits = self.trait_system.check_trait_activation(b_char, "convergence", trait_context)
            for trait in b_traits:
                b_roll += trait.get('value', 0)
                print(f"  {b_name}'s {trait.get('name')} activated! +{trait.get('value')} to combat roll")
        
        # Determine winner
        if a_roll > b_roll:
            winner = a_char
            loser = b_char
            winner_roll = a_roll
            loser_roll = b_roll
            winner_name = a_name
            loser_name = b_name
        else:
            winner = b_char
            loser = a_char
            winner_roll = b_roll
            loser_roll = a_roll
            winner_name = b_name
            loser_name = a_name
        
        # Calculate damage
        roll_diff = winner_roll - loser_roll
        base_damage = max(1, roll_diff / 5)
        
        # Apply random factor
        damage = int(base_damage * random.uniform(0.8, 1.2))
        damage = max(1, damage)
        
        # Get square name for logging
        square_name = chess.square_name(square)
        
        # Log the convergence
        print(f"CONVERGENCE at {square_name}: {a_name} ({a_roll}) vs {b_name} ({b_roll})")
        print(f"  {winner_name} wins! {loser_name} takes {damage} damage")
        
        # Return convergence details
        return {
            "square": square_name,
            "a_character": a_name,
            "b_character": b_name,
            "a_roll": a_roll,
            "b_roll": b_roll,
            "winner": winner_name,
            "damage": damage,
            "loser": loser
        }
    
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
        str_val = getattr(attacker, 'aSTR', 5)
        spd_val = getattr(attacker, 'aSPD', 5)
        fs_val = getattr(attacker, 'aFS', 5)
        
        roll += str_val + fs_val
        
        # Scale by OP (Operations Potential)
        op_factor = getattr(attacker, 'aOP', 5) / 5.0
        roll = int(roll * op_factor)
        
        # Apply morale factor
        morale = getattr(attacker, 'morale', 50)
        morale_factor = morale / 50.0
        roll = int(roll * morale_factor)
        
        # Apply synergy modifiers
        if hasattr(attacker, 'synergy_modifiers') and 'combat_bonus' in attacker.synergy_modifiers:
            bonus = attacker.synergy_modifiers['combat_bonus']
            roll = int(roll * (1 + bonus))
        
        # Apply leadership modifiers
        if hasattr(attacker, 'leadership_modifiers') and 'convergence_bonus' in attacker.leadership_modifiers:
            bonus = attacker.leadership_modifiers['convergence_bonus']
            roll = int(roll * (1 + bonus))
        
        return roll