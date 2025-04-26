#!/usr/bin/env python3
"""
META Fantasy League Simulator - Chess Openings Configuration
Configuration for role-based chess openings
"""

import random

# Role-based chess openings
ROLE_OPENINGS = {
    "FL": ["e4", "d4", "c4"],         # Field Leader
    "RG": ["Nf3", "g3", "b3"],        # Ranger
    "VG": ["e4 e5 Nf3", "d4 d5 c4"],  # Vanguard
    "EN": ["c4", "d4 d5", "e4 c5"],   # Enforcer
    "GO": ["g3", "b3", "c4"],         # Ghost Operative
    "PO": ["d4 Nf6", "e4 e6", "c4 c5"], # Psi Operative
    "SV": ["e4 e5 Nf3 Nc6", "d4 d5 c4 e6"] # Sovereign
}

# Opening descriptions for reference
OPENING_DESCRIPTIONS = {
    "e4": "King's Pawn Opening",
    "d4": "Queen's Pawn Opening",
    "c4": "English Opening",
    "Nf3": "Réti Opening",
    "g3": "King's Fianchetto Opening",
    "b3": "Nimzo-Larsen Attack",
    "e4 e5 Nf3": "King's Knight Opening",
    "d4 d5 c4": "Queen's Gambit",
    "e4 c5": "Sicilian Defense",
    "d4 Nf6": "Indian Defense Systems",
    "e4 e6": "French Defense", 
    "c4 c5": "Symmetrical English",
    "e4 e5 Nf3 Nc6": "Four Knights Game",
    "d4 d5 c4 e6": "Queen's Gambit Declined"
}

def get_opening_for_role(role, variation=None):
    """Get a chess opening for a specific role
    
    Args:
        role (str): Role code (FL, VG, etc.)
        variation (int, optional): Specific variation to use. Defaults to None (random).
    
    Returns:
        str: Opening sequence
    """
    if role not in ROLE_OPENINGS:
        return None
    
    openings = ROLE_OPENINGS[role]
    
    if variation is not None and 0 <= variation < len(openings):
        return openings[variation]
    
    return random.choice(openings)

def get_opening_description(opening_sequence):
    """Get the description for an opening sequence
    
    Args:
        opening_sequence (str): Opening sequence (e.g., "e4 e5 Nf3")
    
    Returns:
        str: Opening description or None if not found
    """
    return OPENING_DESCRIPTIONS.get(opening_sequence)

def apply_opening(board, role):
    """Apply role-based opening moves to a chess board
    
    Args:
        board: Chess board object
        role (str): Role code (FL, VG, etc.)
    
    Returns:
        bool: True if opening was applied, False otherwise
    """
    opening_sequence = get_opening_for_role(role)
    
    if not opening_sequence:
        return False
    
    moves = opening_sequence.split()
    moves_applied = 0
    
    # Apply opening moves
    for move_str in moves:
        try:
            if len(move_str) == 4 and move_str[0] in 'abcdefgh' and move_str[2] in 'abcdefgh':
                # This is a UCI move
                move = board.parse_uci(move_str)
            else:
                # This is SAN notation
                move = board.parse_san(move_str)
            
            if move in board.legal_moves:
                board.push(move)
                moves_applied += 1
            else:
                break
        except Exception:
            break
    
    return moves_applied > 0