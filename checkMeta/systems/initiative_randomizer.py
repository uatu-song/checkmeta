"""
META Fantasy League - Initiative Randomizer System
Handles initiative order randomization to prevent first-mover advantage
"""

import random
from typing import List, Tuple, Any

def randomize_team_order(team_a, team_a_boards, team_b, team_b_boards) -> Tuple[List, List, str, List, List, str]:
    """Randomize the order in which teams are processed to prevent bias
    
    This function takes two teams and their boards and randomly determines 
    which team should go first in convergence processing. This helps prevent
    first-mover advantages that could create systematic biases.
    
    Args:
        team_a: List of team A characters
        team_a_boards: List of team A chess boards
        team_b: List of team B characters
        team_b_boards: List of team B chess boards
        
    Returns:
        Tuple containing:
            - First team characters
            - First team boards
            - First team identifier ("A" or "B")
            - Second team characters
            - Second team boards
            - Second team identifier ("A" or "B")
    """
    # Randomly determine which team goes first
    if random.random() < 0.5:
        # Team A goes first
        return team_a, team_a_boards, "A", team_b, team_b_boards, "B"
    else:
        # Team B goes first
        return team_b, team_b_boards, "B", team_a, team_a_boards, "A"

def randomize_character_order(characters, boards) -> Tuple[List, List]:
    """Randomize the order in which characters are processed
    
    This function randomizes the processing order of characters within a team,
    which can help prevent systematic biases based on character position in the array.
    
    Args:
        characters: List of characters
        boards: List of corresponding chess boards
        
    Returns:
        Tuple containing:
            - Randomized characters list
            - Randomized boards list (maintaining character-board pairing)
    """
    # Create pairs of (character, board)
    pairs = list(zip(characters, boards))
    
    # Shuffle the pairs
    random.shuffle(pairs)
    
    # Unzip the pairs
    if pairs:
        shuffled_characters, shuffled_boards = zip(*pairs)
        return list(shuffled_characters), list(shuffled_boards)
    else:
        return [], []  # Handle empty lists

def weighted_initiative(team_a, team_b) -> Tuple[List, str, List, str]:
    """Determine initiative order based on character attributes
    
    This function determines initiative order using character attributes
    (particularly Speed/SPD and Leadership/LDR) to weight the randomization.
    
    Args:
        team_a: List of team A characters
        team_b: List of team B characters
        
    Returns:
        Tuple containing:
            - First team characters
            - First team identifier ("A" or "B")
            - Second team characters
            - Second team identifier ("A" or "B")
    """
    # Calculate team initiative scores
    team_a_init = _calculate_team_initiative(team_a)
    team_b_init = _calculate_team_initiative(team_b)
    
    # Calculate probability based on relative initiative
    total_init = team_a_init + team_b_init
    
    if total_init == 0:  # Prevent division by zero
        # Default to 50/50 chance
        team_a_probability = 0.5
    else:
        # Higher initiative gives higher probability
        team_a_probability = team_a_init / total_init
    
    # Randomize based on weighted probability
    if random.random() < team_a_probability:
        # Team A goes first
        return team_a, "A", team_b, "B"
    else:
        # Team B goes first
        return team_b, "B", team_a, "A"

def _calculate_team_initiative(team) -> float:
    """Calculate team initiative score based on character attributes
    
    Args:
        team: List of character dictionaries
        
    Returns:
        float: Initiative score for the team
    """
    initiative = 0.0
    
    for character in team:
        # Skip knocked out characters
        if character.get("is_ko", False):
            continue
            
        # Get speed and leadership attributes (default to 5 if not found)
        speed = character.get("aSPD", 5)
        leadership = character.get("aLDR", 5)
        
        # Field Leaders provide extra initiative bonus
        role_bonus = 1.5 if character.get("role") == "FL" else 1.0
        
        # Calculate character initiative
        char_initiative = (speed * 2 + leadership) * role_bonus
        
        # Apply momentum effects if available
        momentum_state = character.get("momentum_state", "stable")
        momentum_modifier = 1.0
        
        if momentum_state == "building":
            momentum_modifier = 1.2  # 20% bonus
        elif momentum_state == "crash":
            momentum_modifier = 0.8  # 20% penalty
            
        # Apply momentum
        char_initiative *= momentum_modifier
        
        # Add to team total
        initiative += char_initiative
    
    return initiative